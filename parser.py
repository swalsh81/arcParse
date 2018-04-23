import struct
import reference
from event import event
from entity import entity

class Parser(object):

    entities = dict() #keys correstond to entity.addr, event.src or event.dest (source and destination of skills)
    entitiesID = dict() #keys are the instance ids which differ from entity.addr.these correspond to src_instid and dest_instid in the event as well as master_src_instid in an event for a pet/minion. values reflect an entity.addr
    skills = dict() #keys are skill.id, values are names
    events = [] #chronological array of events

    def __init__(self, filepath):
        with open(filepath, 'rb') as fh:
            self.parse(fh)
            self.getInstIds()
            #self.fillInStuff()

    def parse(self, fh):
        #defaults
        self.entities[-1] = entity()

        fh.read(4) # skip random EVTC tag
        version = fh.read(8)
        fh.read(1) # skip
        inst_id = struct.unpack("<h", fh.read(2))[0]
        fh.read(1) # skip
        player_count = struct.unpack("<I", fh.read(4))[0]
        print("count %s" % player_count )

        for i in range(player_count):
            e = entity()
            addr = fh.read(8)
            #print(addr)
            e.addr = struct.unpack("<Q", addr)[0]
            #print(e.addr)
            e.setElite(fh.read(4), fh.read(4))
            tough = struct.unpack("<i", fh.read(4))[0]
            healing = struct.unpack("<i", fh.read(4))[0]
            condi = struct.unpack("<i", fh.read(4))[0]
            e.setName(fh.read(68))
            #e.print()
            #if elite != -1:
            #print("%s - Entity: %s Subsquad: %s Profession: %s : %s %s %s" % (elite, name, subsquad, prof, tough, healing, condi))
            self.entities[e.addr] = e
        print(self.entities)

        skill_count = struct.unpack("<i", fh.read(4))[0]
        print("Skill count: %s" % skill_count)


        for i in range(skill_count):
            skill_id = struct.unpack("<i", fh.read(4))[0]
            name = fh.read(64).decode('ascii').rstrip('\x00')
            self.skills[skill_id] = name

        #skills cleanup
        self.skills[1066] = "Resurrect"
        self.skills[1175] = "Bandage"
        print(self.skills)

        print("start events")
        count = 0

        while(1):
            e = event()
            test = fh.read(8) #try to grab timestamp. If not enough data, end of file
            if len(test) < 8:
                break
            e.time = struct.unpack("<Q", test)[0]
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

            #if self.entities[e.addr]

        #self.validateEvents()
        print("Encounter Length: %s" % str(self.events[len(self.events)-1].time - self.events[0].time))

        #self.findSkill(10646)
        #self.minionTest()

    def getInstIds(self):
        for evt in self.events:
            if not evt.is_statechange:
                if evt.src in self.entities:
                    if evt.src_instid not in self.entities[evt.src].inst_id:
                        self.entities[evt.src].inst_id.append(evt.src_instid)
                    if evt.src_instid not in self.entitiesID:
                        self.entitiesID[evt.src_instid] = evt.src

    def fillInStuff(self):
        startTime = self.events[0].time
        badSrc = 0
        badDest = 0
        count = 0
        for e in self.events:
            srcname = self.entities.get(e.src, self.entities[-1]).name
            if srcname == -1:
                srcname = e.src
                badSrc += 1
            e.src = srcname

            destname = self.entities.get(e.dest, self.entities[-1]).name
            if destname == -1:
                destname = e.src
                badDest += 1
            e.dest = destname
            e.time = e.time - startTime
            e.skill_id = self.skills[e.skill_id]
            e.result = reference.cbtresult[e.result]
            e.is_statechange = reference.cbtstatechange[e.is_statechange]
            e.is_buffremove = reference.cbtbuffremove[e.is_buffremove]
            e.print()
            count += 1
        print("invalid src: %i" % badSrc)
        print("invalid dest: %i" % badDest)
        print("event Count: %i" % len(self.events))

    def minionTest(self):
        counter = 0
        for e in self.events:
            if e.src_master_instid >0:
                e.print()
                counter += 1
            if counter > 20:
                break

    def findSkill(self, i):
        for e in self.events:
            if e.skill_id == i:
                e.print()


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


if __name__ == '__main__':
    p = Parser('./test.evtc')