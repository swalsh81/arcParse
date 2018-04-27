import struct
import reference
from event import event
from entity import entity
from PyQt5.QtCore import pyqtSignal, QObject
import tools
import os

class Encounter(QObject):

    entities = dict() #keys correstond to entity.addr, event.src or event.dest (source and destination of skills)
    entitiesID = dict() #keys are the instance ids which differ from entity.addr.these correspond to src_instid and dest_instid in the event as well as master_src_instid in an event for a pet/minion. values reflect an entity.addr
    skills = dict() #keys are skill.id, values are names
    events = [] #chronological array of events

    progressSignal = pyqtSignal(str, int)
    logSignal = pyqtSignal(str)
    finished = pyqtSignal(object)

    GETTING_EVENTS_LOG = "Getting events ..."
    DATA_CLEANUP_LOG = 'Data Cleanup...'

    entityCount = 0
    fileSize = 0
    isnt_id = 0
    encounterLength = 0

    def __init__(self, filepath):
        super(Encounter, self).__init__()
        self.path = filepath

    def parseQuick(self):
        with open(self.path, 'rb') as fh:
            self.getHeader(fh)  #Order
            self.getEntities(fh)#is
            self.getDuration(fh)#important
            fh.close()

            for e in self.entities:
                if self.entities[e].id == self.inst_id:
                    self.logSignal.emit("---%s---" % self.entities[e].name)
            self.logSignal.emit("Encounter Length: %s" % tools.prettyTimestamp(self.encounterLength))
            for e in self.entities:
                if self.entities[e].isPlayer:
                    self.entities[e].print()
                    self.logSignal.emit("%s on %s" % (self.entities[e].account, self.entities[e].character))
        self.finished.emit(self)

    def parseFull(self):
        with open(self.path, 'rb') as fh:
            self.getHeader(fh)
            self.getEntities(fh)
            self.doparse(fh)
            self.cleanData()
            fh.close()
            self.finished.emit(self)

    def getDuration(self,fh):
        skill_count = struct.unpack("<i", fh.read(4))[0]
        fh.seek(68*skill_count,1)
        startTime = struct.unpack("<Q", fh.read(8))[0]
        fh.seek(-64, os.SEEK_END)
        endTime = struct.unpack("<Q", fh.read(8))[0]
        self.encounterLength =  endTime- startTime

    def getHeader(self, fh):
        fh.seek(0, 2)
        self.fileSize = fh.tell()
        print("file Size: %s" % str(self.fileSize))
        fh.seek(0, 0)

        fh.read(4)  # skip random EVTC tag
        version = fh.read(8)
        fh.read(1)  # skip
        self.inst_id = struct.unpack("<h", fh.read(2))[0]
        fh.read(1)  # skip
        self.entityCount = struct.unpack("<I", fh.read(4))[0]

    def getEntities(self, fh):
        for i in range(self.entityCount):
            e = entity()
            addr = fh.read(8)
            e.addr = struct.unpack("<Q", addr)[0]
            e.setElite(fh.read(4), fh.read(4))
            tough = struct.unpack("<i", fh.read(4))[0]
            healing = struct.unpack("<i", fh.read(4))[0]
            condi = struct.unpack("<i", fh.read(4))[0]
            e.setName(fh.read(68))
            self.entities[e.addr] = e

    def doparse(self, fh):

        skill_count = struct.unpack("<i", fh.read(4))[0]
        print("Skill count: %s" % skill_count)


        for i in range(skill_count):
            skill_id = struct.unpack("<i", fh.read(4))[0]
            name = fh.read(64).decode('ascii').rstrip('\x00')
            self.skills[skill_id] = name

        #skills cleanup
        self.skills[1066] = "Resurrect"
        self.skills[1175] = "Bandage"
        #print(self.skills)

        print("start events")
        count = 0
        self.progressSignal.emit('Getting Events...', fh.tell()/self.fileSize)
        logCounter = 0
        while(1): #breakout at end of file on len(time) where "test"
            e = event()
            time = fh.read(8) #try to grab timestamp. If not enough data, end of file
            if len(time) < 8:
                break
            e.time = struct.unpack("<Q", time)[0]
            src = fh.read(8)
            e.src = struct.unpack("<Q", src)[0]
            e.dest = struct.unpack("<Q", fh.read(8))[0]
            e.val = struct.unpack("<l", fh.read(4))[0]
            e.buff_dmg = struct.unpack("<l", fh.read(4))[0]
            e.overstack_val = struct.unpack("<H", fh.read(2))[0]
            e.skill_id = struct.unpack("<H", fh.read(2))[0]
            src_instid = fh.read(2)
            e.src_instid = struct.unpack("<H", src_instid)[0]
            e.dst_instid = struct.unpack("<H", fh.read(2))[0]
            e.src_master_instid = struct.unpack("<H", fh.read(2))[0]
            iss_offset = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_offset_target = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_bd_offset = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_bd_offset_target = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_alt_offset = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_alt_offset_target = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            skar = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            skar_alt = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            skar_use_alt = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            e.iff = struct.unpack("<B", fh.read(1))[0]
            e.is_buff = struct.unpack("<B", fh.read(1))[0]
            e.result = struct.unpack("<B", fh.read(1))[0]
            e.is_activation = struct.unpack("<B", fh.read(1))[0]
            e.is_buffremove = struct.unpack("<B", fh.read(1))[0]
            e.is_ninety = struct.unpack("<B", fh.read(1))[0]
            e.is_fifty = struct.unpack("<B", fh.read(1))[0]
            e.is_moving = struct.unpack("<B", fh.read(1))[0]
            e.is_statechange = struct.unpack("<B", fh.read(1))[0]
            e.is_flanking = struct.unpack("<B", fh.read(1))[0]
            e.is_shields = struct.unpack("<B", fh.read(1))[0]
            result_local = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            ident_local = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            if count < 0:
                print(src_instid)
                print(e.src_instid)
                e.print()
                count += 1
            self.events.append(e)

            if logCounter >= 1000:
                self.progressSignal.emit(self.GETTING_EVENTS_LOG, 100*fh.tell()/self.fileSize)
                logCounter = 0
            else:
                logCounter += 1

        self.progressSignal.emit(self.GETTING_EVENTS_LOG,100)
        self.logSignal.emit("raw time: %s" % (self.events[len(self.events)-1].time - self.events[0].time))
        self.logSignal.emit("Encounter Length: %s" % tools.prettyTimestamp(self.events[len(self.events)-1].time - self.events[0].time))
        self.logSignal.emit("Event Count: %s" % str(len(self.events)))

    def cleanData(self):

        eventCounter = 0
        logCounter = 0

        for evt in self.events:
            #print(str(eventCounter))
            if logCounter >= 1000:
                self.progressSignal.emit(self.DATA_CLEANUP_LOG, 100*eventCounter/len(self.events))
                logCounter = 0
            else:
                logCounter += 1
            eventCounter += 1

            # adjust timestamps to start of encounter
            if evt.is_statechange == reference.cbtstatechange.CBTS_LOGSTART:
                startTime = evt.time
                evt.time = 0
                continue
            evt.time = evt.time - startTime

            # skip non-combat log entries
            if self.skipEvent(evt.is_statechange):
                continue

            #unknown src event
            if evt.src not in self.entities:
                #print("unknown src %i" % unknownSrcCount)
                #unknownSrcCount += 1
                #evt.print()
                continue

            # set first/last seen ticks for each entity
            if self.entities[evt.src].firstSeen == -1:
                self.entities[evt.src].firstSeen = evt.time
            self.entities[evt.src].lastSeen = evt.time

            # relate instids to addrs
            if not evt.is_statechange:
                if evt.src in self.entities:
                    if evt.src_instid not in self.entities[evt.src].inst_id:
                        self.entities[evt.src].inst_id.append(evt.src_instid)
                    if evt.src_instid not in self.entitiesID:
                        self.entitiesID[evt.src_instid] = evt.src




        for evt in self.events:
            # relate master ids to master Addrs
            if evt.src_master_instid > 0 and not self.skipEvent(evt.is_statechange):
                #evt.print()
                #self.entities[evt.src].print()
                masterAddr = self.entitiesID[evt.src_master_instid]
                self.entities[evt.src].master_addr = masterAddr
                if evt.src not in self.entities[masterAddr].minions:
                    self.entities[masterAddr].minions.append(evt.src)
                #self.entities[evt.src].print()
                #self.entities[masterAddr].print()

            #distribute events
            if evt.src == evt.dest:
                if evt.src in self.entities:
                    self.entities[evt.src].addEvent(evt)
            else:
                if evt.src in self.entities:
                    self.entities[evt.src].addEvent(evt)
                if evt.dest in self.entities:
                    self.entities[evt.dest].addEvent(evt)

            if eventCounter >= 1000:
                self.progressSignal.emit(self.DATA_CLEANUP_LOG, 100 * eventCounter / len(self.events))
                eventCounter = 0
            else:
                eventCounter += 1

        self.progressSignal.emit("Done", 100)
        #for evt in self.events:
        #    if evt.src in self.entities and self.entities[evt.src].name == 'Soulless Horror':
        #        evt.print()

        #print(len(self.entities))
        #print(len(self.entitiesID))

    def skipEvent(self, state):
        if state == reference.cbtstatechange.CBTS_LANGUAGE or \
                        state == reference.cbtstatechange.CBTS_GWBUILD or \
                        state == reference.cbtstatechange.CBTS_SHARDID or \
                        state == reference.cbtstatechange.CBTS_LOGSTART or \
                        state == reference.cbtstatechange.CBTS_LOGEND:
            return 1

    #just some testing code
    def validateEvents(self):
        for e in self.events:
            error = 0
            if e.iff < 0 or e.iff > 2:
                print("iff out of bounds")
                error = 1
            if e.result < 0 or e.result > 8:
                print("result out of bounds")
                error = 1
            if e.is_activation < 0 or e.is_activation > 5:
                print("activation out of bounds")
                error = 1
            if e.is_statechange < 0 or e.is_statechange > 17:
                print("statechange out of bounds")
                error = 1
            if e.is_buffremove < 0 or e.is_buffremove > 3:
                print("buffremove out of bounds")
                error = 1
            if error:
                print("index: %i" % self.events.index(e))
                e.print()


#if __name__ == '__main__':
    #p = Parser('./test.evtc')