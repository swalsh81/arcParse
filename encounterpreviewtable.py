from PyQt5.QtWidgets import QTableView, QHeaderView
from PyQt5.QtGui import QPixmap, QColor, QLinearGradient, QBrush
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt, QSize, QSortFilterProxyModel

import worker as Worker
from worker import Job

from encounter import Encounter
from entity import Entity
import reference

from resourcehandler import ResourceHandler


class EncounterPreviewTable(QTableView):
    def __init__(self, parent):
        super(EncounterPreviewTable, self).__init__(parent)
        self.model = EncounterInfoModel()
        self.sortModel = QSortFilterProxyModel()
        self.model.dataChanged.connect(self.compact)
        self.horizontalHeader().sectionResized.connect(self.calcHeader)

    def setup(self, path):
        self.model.setup(path)
        self.sortModel.setSourceModel(self.model)
        self.setModel(self.sortModel)

        sortPoint = self.model.headers.index(self.model.TXT_DPS)
        order = Qt.DescendingOrder
        self.sortModel.sort(sortPoint, order)
        self.horizontalHeader().setSortIndicator(sortPoint,order)

    def compact(self):
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def calcHeader(self):
        v: QHeaderView  = self.horizontalHeader()
        totalheader = 0
        headerEnds = []
        for c in range (0, v.count()):
            totalheader += v.sectionSize(c)
            headerEnds.append(totalheader)

        self.model.totalWidth = totalheader
        self.model.headerWidths = headerEnds

class EncounterInfoModel(QAbstractItemModel):

    TXT_SUBSQUAD = "Grp"
    TXT_CLASS = ""
    TXT_CHARACTER = "Character"
    TXT_ACCOUNT = "Display Name"
    TXT_DPS = "DPS"
    TXT_BOSS_DPS = "Boss DPS"
    TXT_DMG_TOTAL = "Total"
    TXT_DMG_BOSS = "Total Boss"
    TXT_INCOMING = "Damage In"
    TXT_IN_DPS = "DPS In"
    TXT_DOWN = "Downs"
    TXT_DEAD = "Dead"

    headers = [TXT_SUBSQUAD, TXT_CLASS, TXT_CHARACTER, TXT_ACCOUNT, TXT_DPS, TXT_BOSS_DPS, TXT_DMG_TOTAL, TXT_DMG_BOSS, TXT_DOWN, TXT_DEAD]

    fullOnlyHeaders = [TXT_DOWN, TXT_DEAD, TXT_DPS, TXT_BOSS_DPS, TXT_DMG_TOTAL, TXT_DMG_BOSS]

    def __init__(self, parent = None):
        super(EncounterInfoModel, self).__init__()
        self.encounter = None
        self.path = ""
        self.resourceHandler = None
        self.nodes = []
        self.highestRowValue = -1
        self.totalWidth = 0
        self.headerWidths = []
        self.ready = False

    def reset(self):
        self.encounter = None
        self.nodes.clear()
        self.path = ""

    def setup(self, path):
        self.resourceHandler = ResourceHandler()
        self.reset()
        self.path = path
        self.encounter = Encounter(path)
        self.encounter.quickFinished.connect(self.quickParseFinished)
        job = Job(self.encounter.parseQuick)
        Worker.ThreadPool.start(job)

    def getEncounter(self):
        return self.encounter

    def quickParseFinished(self):
        self.layoutAboutToBeChanged.emit()
        self.nodes = []
        for p in self.encounter.players:
            self.nodes.append(EncounterNode(p))
        self.layoutChanged.emit()
        self.emitChange()
        self.encounter.fullFinished.connect(self.emitChange)
        self.encounter.fullFinished.connect(self.findHighestValue)
        job = Job(self.encounter.parseFull)
        Worker.ThreadPool.start(job)

    def emitChange(self):
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(len(self.nodes) - 1, len(self.headers) - 1))

    def index(self, row: int, column: int, parent: QModelIndex = ...):
        return self.createIndex(row, column, self.nodes[row])

    def parent(self, child: QModelIndex):
        return QModelIndex()

    def rowCount(self, parent: QModelIndex = ...):
        return len(self.nodes)

    def columnCount(self, parent: QModelIndex = ...):
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = ...):

        if not index.isValid():
            return QVariant()

        node: EncounterNode = index.internalPointer()
        p: Entity = self.encounter.entities[node.player]
        h = self.headers[index.column()]

        if h == self.TXT_CLASS and role == Qt.DecorationRole:
            if node.pixmap is None:
                try:
                    #print("was none")
                    specInfo = self.resourceHandler.getSpecialization(p.elite, p.prof)
                    p = QPixmap()
                    p.loadFromData(specInfo[self.resourceHandler.PROFESSION_ICON])
                    p = p.scaled(QSize(20, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    node.pixmap = p
                except Exception as e:
                    return QVariant()
            return node.pixmap

        if role == Qt.TextAlignmentRole:
            if h in [self.TXT_SUBSQUAD, self.TXT_CLASS, self.TXT_DEAD, self.TXT_DOWN, self.TXT_DPS, self.TXT_BOSS_DPS, self.TXT_DMG_BOSS, self.TXT_DMG_TOTAL]:
                return Qt.AlignCenter

        if role == Qt.DisplayRole:

            if h == self.TXT_SUBSQUAD:
                return p.subsquad
            if h == self.TXT_CHARACTER:
                return p.character
            if h == self.TXT_ACCOUNT:
                return p.account
            if h == self.TXT_BOSS_DPS:
                return self.encounter.getBossDps(node.player)
            if h == self.TXT_DPS:
                return self.encounter.getTotalDps(node.player)
            if h == self.TXT_DMG_TOTAL:
                return p.damage.totalOut
            if h ==  self.TXT_DMG_BOSS:
                return self.encounter.getBossDamage(node.player)
            if h == self.TXT_DOWN:
                return p.downed
            if h == self.TXT_DEAD:
                return p.dead
            return QVariant()

        if role == Qt.BackgroundRole:
            if not self.encounter.fullComplete:
                return QVariant()
            rightBound = self.headerWidths[index.column()]/self.totalWidth
            leftBound = 0
            if index.column() > 0:
                leftBound = self.headerWidths[index.column() - 1]/self.totalWidth

            # barBound = self.encounter.getTotalDps(node.player)/self.highestRowValue
            if self.highestRowValue == 0:
                barBound = 0
            else:
                barBound = self.data(self.createIndex(index.row(), 4, node), Qt.DisplayRole)/self.highestRowValue

            profColor = QColor(*reference.CLASS_COLORS[p.prof], 60)
            if rightBound <= barBound:
                return profColor
            elif leftBound >= barBound:
                return QVariant()
            else:
                colpercent = rightBound - leftBound
                colwidth = 0
                if index.column() > 0:
                    colwidth = self.headerWidths[index.column()] - self.headerWidths[index.column() - 1]
                else:
                    colwidth = self.headerWidths[index.column()]
                toFill = barBound-leftBound

                gradient = QLinearGradient(0, 0, colwidth, 0)
                gradient.setColorAt(toFill/colpercent, profColor)
                gradient.setColorAt((toFill/colpercent) + .000001, QColor('white'))
                brush = QBrush(gradient)
                return brush

    def findHighestValue(self):
        self.highestRowValue = 0
        # for player in self.encounter.players:
        #     d = self.encounter.getTotalDps(player)
        #     if self.highestRowValue < d:
        #         self.highestRowValue = d
        for i in range(0, self.rowCount()):
            val = self.data(self.createIndex(i, 4, self.nodes[i]), Qt.DisplayRole)
            if self.highestRowValue < val:
                self.highestRowValue = val
        print("Highest: %s" % self.highestRowValue)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Vertical:
            return QVariant()

        if role == Qt.DisplayRole:
            return self.headers[section]

        if role == Qt.InitialSortOrderRole:
            h = self.headers[section]
            if h in [self.TXT_CHARACTER, self.TXT_ACCOUNT, self.TXT_CLASS]:
                return Qt.AscendingOrder
            else:
                return Qt.DescendingOrder
            return QVariant()

class EncounterNode():

    def __init__(self, player):
        self.player = player
        self.pixmap = None