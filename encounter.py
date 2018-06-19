import struct
import reference
from event import event
from entity import Entity
from PyQt5.QtCore import pyqtSignal, QObject
import tools
import os, time
from io import BytesIO
from zipfile import ZipFile, ZipExtFile

class Encounter(QObject):
    GETTING_EVENTS_LOG = "Getting events..."
    DATA_CLEANUP_LOG = 'Data Cleanup...'
    RELATING_EVENTS_LOG = 'Relating Events...'
    FINDING_DAMAGE_SOURCES = 'Finding Damage Sources...'
    STARTING_PARSE = 'Starting Parse...'

    progressSignal = pyqtSignal(str, int)
    logSignal = pyqtSignal(str)
    quickFinished = pyqtSignal(object)
    fullFinished = pyqtSignal(object)

    startPrinting = False

    def __init__(self, filepath):
        super(Encounter, self).__init__()
        self.path = filepath

        self.entities = dict()  # keys correspond to entity.addr, event.src or event.dest (source and destination of skills)
        self.entitiesID = dict()  # keys are the instance ids which differ from entity.addr.these correspond to src_instid and dest_instid in the event as well as master_src_instid in an event for a pet/minion. values reflect an entity.addr
        self.skills = dict()  # keys are skill.id, values are names
        self.events = []  # chronological array of events
        self.buffs = []

        self.entityCount = -1
        self.playerCount = 0
        self.skillCount = -1
        self.startOfEvents = -1
        self.fileSize = 0
        self.inst_id = 0
        self.boss_addr = -1
        self.bossAddrs = []
        self.encounterLength = 0
        self.startTime = 0

        self.players = []
        self.playerRef = dict()
        #self.damageSources = dict()

        self.kill = False
        self.bossDeath = False
        self.lowestBossHealth = 10000

        self.damageIncModel = None

        self.quickComplete = False
        self.fullComplete = False

        self.endTime = -1

        self.logLength = -1
        # Header: 16 bytes
        # Entity Count: 4 bytes
        # Entity: 96 bytes
        # Skill Count: 4 bytes
        # Skill: 68 bytes
        # Event: 64 bytes

    def getFile(self):
        name, ext = os.path.splitext(self.path)
        fh = None
        if ext == ".evtc":
            fh = open(self.path, 'rb')
        if ext == ".zip":
            name, ext = os.path.splitext(os.path.basename(self.path))
            fh = BytesIO(ZipFile(self.path, 'r').read(name))
        return fh

    def parseQuick(self):
        fh = self.getFile()
        self.progressSignal.emit(self.STARTING_PARSE, -1)
        self.getHeader(fh)
        self.getEntities(fh)
        self.findSuccessFail(fh)
        self.getLogLength()
        fh.close()

        # for e in self.entities:
        #     if self.entities[e].id == self.inst_id:
        #         self.logSignal.emit("---%s---" % self.entities[e].name)
        # self.logSignal.emit("Encounter Length: %s" % tools.prettyTimestamp(self.encounterLength))
        # for e in self.entities:
        #     if self.entities[e].isPlayer:
        #         self.entities[e].print()
        #         self.logSignal.emit("%s on %s" % (self.entities[e].account, self.entities[e].character))
        self.quickComplete = True
        self.progressSignal.emit("Done", 100)
        self.quickFinished.emit(self)

    def parseFull(self):
        fh = self.getFile()
        parseStart = time.time()
        if not self.quickComplete:
            self.getHeader(fh)
            self.getEntities(fh)
            self.findSuccessFail(fh)
            #self.getDuration(fh)
        self.getSkills(fh)
        self.getAllEvents(fh)
        fh.close()
        self.cleanData()
        self.quickComplete = True
        self.fullComplete = True
        self.fullFinished.emit(self)
        print("Parse Time: %s" % (time.time() - parseStart))

    def getStartOfEvents(self, fh):
        if self.startOfEvents == -1:
            self.startOfEvents = self.startOfEvents = 16 + 4 + (self.getEntityCount(fh) * 96) + 4 + (self.getSkillCount(fh) * 68)
        return self.startOfEvents

    def getLogLength(self):
        fh = self.getFile()
        fh.seek(self.getStartOfEvents(fh), 0)
        evt,success = self.parseEvent(fh.read(64))
        encStart = evt.time
        if evt.is_statechange == reference.cbtstatechange.CBTS_LOGSTART:
            #evt.print()
            self.startTime = evt.val
        else:
            while evt.is_statechange != reference.cbtstatechange.CBTS_LOGSTART:
                evt, success = self.parseEvent(fh.read(64))
                if evt.is_statechange == reference.cbtstatechange.CBTS_LOGSTART:
                    self.startTime = evt.val
                    break

        fh.seek(-64, os.SEEK_END)
        encEnd = struct.unpack("<Q", fh.read(8))[0]
        self.logLength = encEnd - encStart
        fh.close()
        return self.startTime, self.logLength

    # def getDuration(self,fh):
    #
    #     fh.seek(self.getStartOfEvents(fh), 0)
    #     self.startTime = struct.unpack("<Q", fh.read(8))[0]
    #     fh.seek(-64, os.SEEK_END)
    #     endTime = struct.unpack("<Q", fh.read(8))[0]
    #     self.encounterLength = endTime - self.startTime
    #     return self.startTime, self.encounterLength

    def getHeader(self, fh):
        fh.seek(0, 2)
        self.fileSize = fh.tell()
        #print("file Size: %s" % str(self.fileSize))
        fh.seek(0, 0)

        fh.read(4)  # skip random EVTC tag
        version = fh.read(8)
        fh.read(1)  # skip
        self.inst_id = struct.unpack("<h", fh.read(2))[0]

    def getEntityCount(self, fh):
        if self.entityCount == -1:
            fh.seek(16, 0)
            self.entityCount = struct.unpack("<I", fh.read(4))[0]
        return self.entityCount

    def getEntities(self, fh):
        self.getEntityCount(fh)
        fh.seek(20, 0)
        count = 0
        for i in range(self.entityCount):
            e = Entity()
            addr = fh.read(8)
            e.addr = struct.unpack("<Q", addr)[0]
            e.setElite(fh.read(4), fh.read(4))
            tough = struct.unpack("<i", fh.read(4))[0]
            healing = struct.unpack("<i", fh.read(4))[0]
            condi = struct.unpack("<i", fh.read(4))[0]
            e.setName(fh.read(68))
            self.entities[e.addr] = e
            if e.isPlayer:
                self.playerCount += 1
                self.players.append(e.addr)
                self.playerRef[e.account] = e.addr
                self.playerRef[e.character] = e.addr
            if e.id == self.inst_id:
                self.boss_addr = e.addr
            if self.boss_addr in self.entities and self.entities[self.boss_addr].name == e.name:
                self.bossAddrs.append(e.addr)


    def getSkillCount(self, fh):
        if self.skillCount == -1:
            self.getEntityCount(fh)
            fh.seek(16 + 4 + (self.entityCount * 96), 0)
            self.skillCount = struct.unpack("<i", fh.read(4))[0]
            #print("Skill count: %s" % self.skillCount)
        return self.skillCount

    def getSkills(self, fh):
        self.getSkillCount(fh)
        fh.seek(16 + 4 + (self.getEntityCount(fh) * 96) + 4, 0)
        for i in range(self.skillCount):
            skill_id = struct.unpack("<i", fh.read(4))[0]
            name = fh.read(64).decode('utf-8').rstrip('\x00')
            self.skills[skill_id] = name
            # if name == "Confusion":
            #    print("%s:%s" % (skill_id, name))
            # print("%s %s" %(name, skill_id))

        # skills cleanup
        self.skills[1066] = "Resurrect"
        self.skills[1175] = "Bandage"


    def findSuccessFail(self, fh):
        # print("------")
        if self.boss_addr == -1:
            self.getEntities(fh)
        # print(self.entities[self.boss_addr].name)
        it = 1
        valid = True

        fh.seek(self.getStartOfEvents(fh),0)
        e,v = self.parseEvent(fh.read(64))
        startTime = e.time

        while valid :
            if self.fileSize < 64*it:
                return
            fh.seek((-64 * it), 2)
            evt, valid = self.parseEvent(fh.read(64))

            if it == 1:
                self.encounterLength = evt.time-startTime

            if evt.src in self.bossAddrs and evt.is_statechange == reference.cbtstatechange.CBTS_CHANGEDEAD:
                self.lowestBossHealth = 0
                self.kill = True
                self.bossDeath = True
                # print("kill")
                self.encounterLength = evt.time-startTime
                return

            if evt.is_statechange == reference.cbtstatechange.CBTS_REWARD:
                self.lowestBossHealth = 0
                self.kill = True
                #print("Reward")
                self.encounterLength = evt.time-startTime

            if evt.src in self.bossAddrs and evt.is_statechange == reference.cbtstatechange.CBTS_HEALTHUPDATE:
                #print("lowest %s" % event.dest)
                if evt.dest < self.lowestBossHealth and not self.kill:
                    self.lowestBossHealth = evt.dest
                if evt.dest > 5:
                    return

            if self.kill and evt.time < self.encounterLength-2000:
                print("breakout")
                return

            it += 1



    def getAllEvents(self, fh):

        # print("start events")
        count = 0
        self.progressSignal.emit('Getting Events...', fh.tell()/self.fileSize)
        logCounter = 0
        fh.seek(self.getStartOfEvents(fh), 0)

        while 1 : #breakout at end of file on len(time) where "test"
            evt, valid = self.parseEvent(fh.read(64))
            if not valid:
                break

            # evt.print()

            self.events.append(evt)

            if logCounter >= 1000:
                self.progressSignal.emit(self.GETTING_EVENTS_LOG, 100*fh.tell()/self.fileSize)
                logCounter = 0
            else:
                logCounter += 1

        self.progressSignal.emit(self.GETTING_EVENTS_LOG,100)
        self.logSignal.emit("raw time: %s" % (self.events[len(self.events)-1].time - self.events[0].time))
        self.encounterLength = self.events[len(self.events)-1].time - self.events[0].time
        self.logSignal.emit("Encounter Length: %s" % tools.prettyTimestamp(self.encounterLength))
        self.logSignal.emit("Event Count: %s" % str(len(self.events)))

    def parseEvent(self, bytes):
        e = event()
        if len(bytes) < 64:
            # print(len(bytes))
            return e, False

        e.time = struct.unpack("<Q", bytes[0:8])[0]
        e.src = struct.unpack("<Q", bytes[8:16])[0]
        e.dest = struct.unpack("<Q", bytes[16:24])[0]
        e.val = struct.unpack("<l", bytes[24:28])[0]
        e.buff_dmg = struct.unpack("<l", bytes[28:32])[0]
        e.overstack_val = struct.unpack("<H", bytes[32:34])[0]
        e.skill_id = struct.unpack("<H", bytes[34:36])[0]
        e.src_instid = struct.unpack("<H", bytes[36:38])[0]
        e.dst_instid = struct.unpack("<H", bytes[38:40])[0]
        e.src_master_instid = struct.unpack("<H", bytes[40:42])[0]
        #iss_offset = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #iss_offset_target = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #iss_bd_offset = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #iss_bd_offset_target = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #iss_alt_offset = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #iss_alt_offset_target = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #skar = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #skar_alt = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #skar_use_alt = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        e.iff = struct.unpack("<B", bytes[51:52])[0]
        e.is_buff = struct.unpack("<B", bytes[52:53])[0]
        e.result = struct.unpack("<B", bytes[53:54])[0]
        e.is_activation = struct.unpack("<B", bytes[54:55])[0]
        e.is_buffremove = struct.unpack("<B", bytes[55:56])[0]
        e.is_ninety = struct.unpack("<B", bytes[56:57])[0]
        e.is_fifty = struct.unpack("<B", bytes[57:58])[0]
        e.is_moving = struct.unpack("<B", bytes[58:59])[0]
        e.is_statechange = struct.unpack("<B", bytes[59:60])[0]
        e.is_flanking = struct.unpack("<B", bytes[60:61])[0]
        e.is_shields = struct.unpack("<B", bytes[61:62])[0]
        #result_local = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage
        #ident_local = struct.unpack("<B", fh.read(1))[0]  # internal tracking garbage

        return e, True

    def cleanData(self):

        eventCounter = 0
        logCounter = 0
        startTime = 0
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

            # unknown src event
            if evt.src not in self.entities:
                # print("unknown src %i" % unknownSrcCount)
                # unknownSrcCount += 1
                # evt.print()
                continue

            ent:Entity = self.entities[evt.src]
            if ent.firstSeen == -1:
                ent.firstSeen = evt.time
            ent.lastSeen = evt.time

            # relate instids to addrs
            if not evt.is_statechange:
                if evt.src in self.entities:
                    if evt.src_instid not in ent.inst_id:
                        ent.inst_id.append(evt.src_instid)
                    if evt.src_instid not in self.entitiesID:
                        self.entitiesID[evt.src_instid] = evt.src

            # if evt.skill_id == 740 and evt.is_buffremove == 1 and evt.time < 110000:
            #     self.printPrettyEvent(evt)

        eventCounter = 0
        logCounter = 0

        for evt in self.events:
            if logCounter >= 1000:
                self.progressSignal.emit(self.RELATING_EVENTS_LOG, 100*eventCounter/len(self.events))
                logCounter = 0
            else:
                logCounter += 1
            eventCounter += 1
            # relate master ids to master Addrs
            if evt.src_master_instid > 0 and not self.skipEvent(evt.is_statechange):
                #evt.print()
                #self.entities[evt.src].print()
                if evt.src in self.entities:
                    masterAddr = self.entitiesID[evt.src_master_instid]

                    self.entities[evt.src].master_addr = masterAddr

                    if evt.src not in self.entities[masterAddr].minions:
                        self.entities[masterAddr].minions.append(evt.src)
                #self.entities[evt.src].print()
                #self.entities[masterAddr].print()

            #distribute events

            # rewardTime = -1
            # bossDeadTime = -1
            # if evt.is_statechange == reference.cbtstatechange.CBTS_REWARD:
            #     self.gotReward = True
            #     #print("reward %s" % evt.time)
            #     rewardTime = evt.time
            #
            # if evt.src == self.boss_addr and evt.is_statechange == reference.cbtstatechange.CBTS_CHANGEDEAD:
            #     self.bossDeath = True
            #     #print("boss")
            #     bossDeadTime = evt.time
            #
            # if bossDeadTime > 0:
            #     self.encounterLength = bossDeadTime
            # elif rewardTime > 0:
            #     #print("else")
            #     self.encounterLength = rewardTime

            if evt.time >= self.encounterLength:
                break

            if not (evt.src in self.players or evt.dest in self.players or (evt.src_master_instid in self.entitiesID and self.entitiesID[evt.src_master_instid] in self.players)):
                continue

            entityCheck = False

            if evt.src in self.entities and evt.dest in self.entities:
                entityCheck = True

            if evt.src == evt.dest:
                if evt.src in self.entities:
                    self.entities[evt.src].addEvent(evt, entityCheck)
            else:
                if evt.src in self.entities:
                    self.entities[evt.src].addEvent(evt, entityCheck)
                if evt.dest in self.entities:
                    self.entities[evt.dest].addEvent(evt, entityCheck)

            # if evt.skill_id == 34362:
            #     self.printPrettyEvent(evt)
            #     evt.print()
            # if evt.is_buff and not evt.is_activation and evt.is_buffremove == 2:
            #     self.printPrettyEvent(evt)
            #     evt.print()
            #     print("")
            #     if logCounter % 100 == 0:
            #         None

#        self.findDamageSources()


        # for evt in self.events:
        #     if evt.time > 314000 and evt.time < 314200:
        #         self.printPrettyEvent(evt)

        for player in self.players:
            p: Entity = self.entities[player]
            for minion in p.minions:
                m:Entity = self.entities[minion]
                for dest in m.damage.foes:
                    p.damage.addMinionDamage(dest, m.damage.foes[dest].totalDamageIn)

        # for e in self.entities:
        #     ent: entity = self.entities[e]
        #     if ent.name == self.entities[self.boss_addr].name:
        #         ent.print()
        #         print("-------------------------------------------------")
        #
        # for p in self.players:
        #     pl = self.entities[p]
        #     print(pl.name)
        #     for e in self.entities:
        #         ent:entity = self.entities[e]
        #         if ent.id == self.inst_id:
        #             print("%s %s" % (ent.name, pl.damageOut[e][entity.ENTITY_TOTAL_DAMAGE]))

        self.progressSignal.emit("Done", 100)

        #for player in self.players:
            #print("%s last seen %s" % (self.entities[player].character, self.entities[player].lastSeen))
            #continue
            #if True:
                #None
                #break

            # p:Entity = self.entities[player]
            # if p.character != "aaaa":
            #     None
            #     continue
            #
            # print("--------------------------------------")
            # print(p.name)
            #
            # for skill in p.damageOutTotals:
            #     if skill < 0:
            #         continue
            #     s = self.skills[skill]
            #     print("%s: %s Hits %s" % (s, p.damageOutTotals[skill][Entity.SKILL_TOTAL_DAMAGE], p.damageOutTotals[skill][Entity.SKILL_IMPACT]))
            #
            # dmg = p.damageOut
            #
            # for d in dmg:
            #     if d in self.entities:
            #         print("")
            #         print("%s %s" % (d, self.entities[d].inst_id))
            #         print("Target: %s: %s" % (self.entities[d].name, dmg[d][Entity.ENTITY_TOTAL_DAMAGE]))
            #         print("%s - %s" % (self.entities[d].firstSeen, self.entities[d].lastSeen))
            #     for s in dmg[d]:
            #         if s in self.skills:
            #             print("%s: %s" % (self.skills[s], dmg[d][s][Entity.SKILL_TOTAL_DAMAGE]))

    # def findDamageSources(self):
    #     eventCounter = 0
    #     logCounter = 0
    #
    #     self.damageSources['self'] = []
    #     self.damageSources[self.boss_addr] = []
    #
    #     for ent in self.entities:
    #         e = self.entities[ent]
    #         if not e.isPlayer:
    #             continue
    #
    #         if logCounter >= 10:
    #             self.progressSignal.emit(self.FINDING_DAMAGE_SOURCES, 100 * eventCounter / len(self.events))
    #             logCounter = 0
    #         else:
    #             logCounter += 1
    #         eventCounter += 1
    #
    #         for src in e.damageInc:
    #             if src == e.addr:
    #                 continue
    #             if src not in self.damageSources:
    #                 self.damageSources[src] = []
    #             for skill in e.damageInc[src]:
    #                 if skill not in self.damageSources[src]:
    #                     self.damageSources[src].append(skill)

    def skipEvent(self, state):
        if state == reference.cbtstatechange.CBTS_LANGUAGE or \
                        state == reference.cbtstatechange.CBTS_GWBUILD or \
                        state == reference.cbtstatechange.CBTS_SHARDID or \
                        state == reference.cbtstatechange.CBTS_LOGSTART or \
                        state == reference.cbtstatechange.CBTS_LOGEND:
            return 1

    #just some testing code
    # def validateEvents(self):
    #     for e in self.events:
    #         error = 0
    #         if e.iff < 0 or e.iff > 2:
    #             print("iff out of bounds")
    #             error = 1
    #         if e.result < 0 or e.result > 8:
    #             print("result out of bounds")
    #             error = 1
    #         if e.is_activation < 0 or e.is_activation > 5:
    #             print("activation out of bounds")
    #             error = 1
    #         if e.is_statechange < 0 or e.is_statechange > 17:
    #             print("statechange out of bounds")
    #             error = 1
    #         if e.is_buffremove < 0 or e.is_buffremove > 3:
    #             print("buffremove out of bounds")
    #             error = 1
    #         if error:
    #             print("index: %i" % self.events.index(e))
    #             e.print()

    def getBossDps(self, player):
        return self.getBossDamage(player) /(self.encounterLength/1000)

    def getBossDamage(self, player):
        p: Entity = self.entities[player]
        dmg = 0
        for target in self.bossAddrs:

            if target in p.damage.foes:
                dmg += p.damage.foes[target].totalDamageIn
                # print(p.character)
                # print("%s %s %s" %(self.entities[target].name, p.damage.foes[target].totalDamageIn,dmg))
        return dmg

    def getTotalDps(self, player):
        p: Entity = self.entities[player]
        dmg = p.damage.totalOut
        return dmg/(self.encounterLength/1000)

#if __name__ == '__main__':
    #p = Parser('./test.evtc')

    def printPrettyEvent(self, evt:event):
        src = evt.src
        if evt.src in self.entities:
            src = self.entities[evt.src].name

        dest = evt.dest
        if evt.dest in self.entities:
            dest = self.entities[evt.dest].name

        skill = self.skills.get(evt.skill_id, evt.skill_id)

        print("Time: %s\tSource: %s\tDest: %s\tSkill: %s\tDuration: %s\tOverstack: %s\tRemove: %s" % (evt.time, src, dest, skill, evt.val, evt.overstack_val, evt.is_buffremove))