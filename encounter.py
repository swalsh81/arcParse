import struct
import reference
from event import event
from entity import entity
from PyQt5.QtCore import pyqtSignal, QObject, QAbstractItemModel, QModelIndex, QVariant, Qt
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

    GETTING_EVENTS_LOG = "Getting events..."
    DATA_CLEANUP_LOG = 'Data Cleanup...'
    RELATING_EVENTS_LOG = 'Relating Events...'
    FINDING_DAMAGE_SOURCES = 'Finding Damage Sources...'

    entityCount = -1
    playerCount = 0
    skillCount = -1
    startOfEvents = -1
    fileSize = 0
    inst_id = 0
    boss_addr = -1
    encounterLength = 0

    players = []
    damageSources = dict()

    result = "Failed"

    #Header: 16 bytes
    #Entity Count: 4 bytes
    #Entity: 96 bytes
    #Skill Count: 4 bytes
    #Skill: 68 bytes
    #Event: 64 bytes

    damageIncModel = None


    def __init__(self, filepath):
        super(Encounter, self).__init__()
        self.path = filepath

    def getDamageIncModel(self):
        if self.damageIncModel == None:
            self.damageIncModel = DamageIncModel(self)
        return self.damageIncModel


    def parseQuick(self):
        with open(self.path, 'rb') as fh:
            self.getHeader(fh)
            self.getEntities(fh)
            self.getDuration(fh)
            fh.close()

            # for e in self.entities:
            #     if self.entities[e].id == self.inst_id:
            #         self.logSignal.emit("---%s---" % self.entities[e].name)
            # self.logSignal.emit("Encounter Length: %s" % tools.prettyTimestamp(self.encounterLength))
            # for e in self.entities:
            #     if self.entities[e].isPlayer:
            #         self.entities[e].print()
            #         self.logSignal.emit("%s on %s" % (self.entities[e].account, self.entities[e].character))
        self.finished.emit(self)

    def parseFull(self):
        with open(self.path, 'rb') as fh:
            self.getHeader(fh)
            self.getEntities(fh)
            self.getSkills(fh)
            self.getAllEvents(fh)
            fh.close()
            self.cleanData()
            self.finished.emit(self)

    def getStartOfEvents(self, fh):
        if self.startOfEvents == -1:
            self.startOfEvents = self.startOfEvents = 16 + 4 + (self.getEntityCount(fh) * 96) + 4 + (self.getSkillCount(fh) * 68)
        return self.startOfEvents

    def getDuration(self,fh):

        fh.seek(self.getStartOfEvents(fh), 0)
        startTime = struct.unpack("<Q", fh.read(8))[0]
        fh.seek(-64, os.SEEK_END)
        endTime = struct.unpack("<Q", fh.read(8))[0]
        self.encounterLength = endTime - startTime

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
            if e.isPlayer:
                self.playerCount += 1
                self.players.append(e.addr)
            if e.id == self.inst_id:
                self.boss_addr = e.addr

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
            name = fh.read(64).decode('ascii').rstrip('\x00')
            self.skills[skill_id] = name

        # skills cleanup
        self.skills[1066] = "Resurrect"
        self.skills[1175] = "Bandage"

    def getAllEvents(self, fh):

        #print("start events")
        count = 0
        self.progressSignal.emit('Getting Events...', fh.tell()/self.fileSize)
        logCounter = 0
        fh.seek(self.getStartOfEvents(fh), 0)

        while(1): #breakout at end of file on len(time) where "test"
            evt, valid = self.parseEvent(fh.read(64))
            if not valid:
                break

            #evt.print()

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
            #print(len(bytes))
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

            if evt.is_statechange == reference.cbtstatechange.CBTS_REWARD:
                self.result = "Success"

        self.findDamageSources()
        self.progressSignal.emit("Done", 100)
        #for evt in self.events:
        #    if evt.src in self.entities and self.entities[evt.src].name == 'Soulless Horror':
        #        evt.print()

        #print(len(self.entities))
        #print(len(self.entitiesID))

    def findDamageSources(self):
        eventCounter = 0
        logCounter = 0

        self.damageSources['self'] = []
        self.damageSources[self.boss_addr] = []

        for ent in self.entities:
            e = self.entities[ent]
            if not e.isPlayer:
                continue

            if logCounter >= 10:
                self.progressSignal.emit(self.FINDING_DAMAGE_SOURCES, 100 * eventCounter / len(self.events))
                logCounter = 0
            else:
                logCounter += 1
            eventCounter += 1

            for src in e.damageInc:
                if src == e.addr:
                    continue
                if src not in self.damageSources:
                    self.damageSources[src] = []
                for skill in e.damageInc[src]:
                    if skill not in self.damageSources[src]:
                        self.damageSources[src].append(skill)




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

class DamageIncModel(QAbstractItemModel):
    encounter = None
    entryDict = dict()
    SELF_INFLICTED = -100

    DEFAULT_TEXT = "-"


    def __init__(self, encounter, parent = None):
        super(DamageIncModel, self).__init__()
        self.encounter = encounter
        self.root = TreeNode()
        self.initializeData()

    def initializeData(self):

        self.root.addNode(TreeNode(self.SELF_INFLICTED, TreeNode.SRC_TYPE))
        self.root.addNode(TreeNode(self.encounter.boss_addr, TreeNode.SRC_TYPE))
        for index, player in enumerate(self.encounter.players):
            p = self.encounter.entities[player]
            #print(p.name)
            for src in p.damageInc:
                if src == p.addr:
                    id = self.SELF_INFLICTED
                else:
                    id = src
                srcNode = self.root.addNode(TreeNode(id, TreeNode.SRC_TYPE))

                for skill in p.damageInc[src]:
                    # if skill == entity.SRC_INC_TOTAL_DAMAGE:
                    #     while len(srcNode.data) < index:
                    #         srcNode.addData("")
                    #     srcNode.addData(p.damageInc[src][entity.SRC_INC_TOTAL_DAMAGE])
                    #     continue
                    if skill != entity.SRC_INC_TOTAL_DAMAGE:
                        srcNode.addNode(TreeNode(skill, TreeNode.SKILL_TYPE))
                    # while len(skNode.data) < index:
                    #     skNode.addData(0)
                    #skNode.addData(p.damageInc[src][skill][entity.SKILL_INC_TOTAL_DAMAGE])
        None

    def parent(self, childIndex):
        if not childIndex.isValid():
            return QModelIndex()

        childNode = childIndex.internalPointer()
        if childNode.parent == self.root:
            return QModelIndex()

        return self.createIndex(childNode.parent.row, 0, childNode.parent)

    def index(self, row, column, parent):
        parentNode = self.root

        if parent.isValid():
            parentNode = parent.internalPointer()

        if row < len(parentNode.children) and column < len(self.encounter.players) + 1:
            return self.createIndex(row, column, parentNode.children[row])
        else:
            return QModelIndex()

    def headerData(self, section, orientation, role):
        #if orientation != Qt.Vertical:
        #    return QVariant()
        if role == Qt.DisplayRole:
            if section == 0:
                return "%s\n%s\n%s" % (self.encounter.entities[self.encounter.boss_addr].name,
                                   tools.prettyTimestamp(self.encounter.encounterLength),
                                   self.encounter.result)
            else:
                return self.encounter.entities[self.encounter.players[section - 1]].name.replace(":", "\n")

    def getSrc(self, index):
        node = index.internalPointer()
        id = None
        if node.type == TreeNode.SRC_TYPE:
            id = node.id
        if node.type == TreeNode.SKILL_TYPE:
            id = node.parent.id

        if id == self.SELF_INFLICTED:
            return self.encounter.players[index.column() - 1], "Self Inflicted"
        elif id == None:
            return -1, "Unknown"
        else:
            return id, self.encounter.entities[id].name

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        node = index.internalPointer()

        #if role == Qt.SizeHintRole or role == Qt.FontRole:
        #    return
        txt = ""
        playerId = self.encounter.players[index.column() - 1]
        player = self.encounter.entities[playerId]
        srcId, srcName = self.getSrc(index)

        if role == Qt.DisplayRole:
            if index.column() == 0:
                if node.type == TreeNode.SRC_TYPE:
                    txt = srcName
                if node.type == TreeNode.SKILL_TYPE:
                    txt = self.encounter.skills[node.id]
            else:
                try:
                    if node.type == TreeNode.SRC_TYPE:
                            txt = player.damageInc[srcId][entity.SRC_INC_TOTAL_DAMAGE]
                    if node.type == TreeNode.SKILL_TYPE:
                            txt = player.damageInc[srcId][node.id][entity.SKILL_INC_TOTAL_DAMAGE]
                except KeyError:
                    txt = self.DEFAULT_TEXT
                #txt = node.data[index.column() - 1]
            return txt

        if role == Qt.ToolTipRole:
            txt += srcName
            srcInfoText = ""
            if index.column() == 0:
                squadDamage = 0
                if node.type == TreeNode.SRC_TYPE:
                    if node.id != self.SELF_INFLICTED:
                        first = self.encounter.entities[node.id].firstSeen
                        last = self.encounter.entities[node.id].lastSeen
                        srcInfoText += "Spawn time: %s\n" % tools.prettyTimestamp(first)
                        srcInfoText += "Lifespan: %s" %tools.prettyTimestamp(last - first)
                    for p in self.encounter.players:
                        try:
                            if node.id == self.SELF_INFLICTED:
                                squadDamage += self.encounter.entities[p].damageInc[p][entity.SRC_INC_TOTAL_DAMAGE]
                            else:
                                squadDamage += self.encounter.entities[p].damageInc[srcId][entity.SRC_INC_TOTAL_DAMAGE]
                        except KeyError:
                            None
                if node.type == TreeNode.SKILL_TYPE:
                    txt += "\n%s" % self.encounter.skills[node.id]
                    for p in self.encounter.players:
                        try:
                            if node.parent.id == self.SELF_INFLICTED:
                                squadDamage += self.encounter.entities[p].damageInc[p][node.id][entity.SKILL_INC_TOTAL_DAMAGE]
                            else:
                                squadDamage += self.encounter.entities[p].damageInc[srcId][node.id][entity.SKILL_INC_TOTAL_DAMAGE]
                        except KeyError:
                            None

                txt += "\n-Total Squad Damage: %s" % str(squadDamage)
                if len(srcInfoText) > 0:
                    txt += "\n\n" + srcInfoText
            else:
                txt = self.encounter.entities[playerId].character + "\n" + txt
                if node.type == TreeNode.SRC_TYPE:
                    txt += "\n-Total Damage: "
                    if srcId in player.damageInc:
                        txt += str(player.damageInc[srcId][entity.SRC_INC_TOTAL_DAMAGE])
                    else:
                        txt += self.DEFAULT_TEXT
                if node.type == TreeNode.SKILL_TYPE:
                    try:
                        sk = player.damageInc[node.parent.id][node.id]
                        txt += "\n-%s: %s" %(self.encounter.skills[node.id], sk.get(entity.SKILL_INC_TOTAL_DAMAGE, 0))
                        txt += "\n-Impacts Incoming: %s" % sk.get(entity.SKILL_INC_IMPACT, 0)
                        txt += "\n--Blocked: %s" % sk.get(entity.RESULT_MODIFIER + reference.cbtresult.CBTR_BLOCK, 0)
                        txt += "\n--Evaded: %s" % sk.get(entity.RESULT_MODIFIER + reference.cbtresult.CBTR_EVADE, 0)
                        txt += "\n--Missed: %s" % sk.get(entity.RESULT_MODIFIER + reference.cbtresult.CBTR_BLIND, 0)
                    except KeyError:
                        None
            return txt


    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.root.children)

        if parent.isValid():
            return len(parent.internalPointer().children)

    def columnCount(self, parent):
        return self.encounter.playerCount + 1

class TreeNode():

    SRC_TYPE = -100
    SKILL_TYPE = -101

    def __init__(self, id = -1, type = -1, parent = None):
        #self.data = []
        self.id = id
        self.parent = parent
        self.children = []
        self.type = type
        self.row = -1

    def addNode(self, node):
        for c in self.children:
            if c.id == node.id:
                return c
        self.children.append(node)
        node.parent = self
        node.row = len(self.children) - 1
        return node

    # def addData(self, data):
    #     self.data.append(data)

    def getChildById(self, id):
        for c in self.children:
            if c.id == id:
                return c

    def indexOf(self, id):
        for i in range(self.children):
            if self.children.id == id:
                return i