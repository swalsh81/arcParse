from PyQt5.QtCore import QAbstractItemModel


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