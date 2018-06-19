from PyQt5.QtWidgets import QTreeView, QHeaderView
from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal, QAbstractItemModel, QVariant, QSortFilterProxyModel, QDate, QDateTime

import time, os
import tools, reference

import worker as Worker
from worker import Job

from encounter import Encounter
from encountercachehandler import EncounterCacheHandler, EncounterInfo

class LogTree(QTreeView):
    tableGenerated = pyqtSignal()
    def __init__(self, parent):
        super(LogTree, self).__init__(parent)

        self.logBrowserModel = LogBrowserModel()
        self.sortModel = FilterModel()
        self.clicked.connect(self.setSelected)
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.path = ""

    def setSelected(self, index:QModelIndex):
        self.logBrowserModel.setSelected(self.sortModel.mapToSource(index))

    def toggleUploadToAll(self, check):
        self.logBrowserModel.toggleUploadToAll(check)

    def setup(self, path = ""):
        self.path = path
        self.logBrowserModel.treeLoaded.connect(self.linkModel)
        self.logBrowserModel.finished.connect(self.finishSetup)
        job = Job(self.logBrowserModel.setup, self.path)
        Worker.ThreadPool.start(job)

    def linkModel(self):
        self.sortModel.setSourceModel(self.logBrowserModel)
        self.setModel(self.sortModel)

        #self.setModel(self.logBrowserModel)

    def getPlayerList(self):
        return self.logBrowserModel.players

    def finishSetup(self):
        self.sortModel.filterStartTime = self.logBrowserModel.earliestLog
        self.tableGenerated.emit()

    def getModel(self):
        return self.logBrowserModel

    def filterSuccess(self, flag):
        self.sortModel.filterSuccess = flag
        self.sortModel.invalidateFilter()

    def filterNew(self, flag):
        self.sortModel.filterNew = flag
        self.sortModel.invalidateFilter()

    def filterPlayers(self, acc, char):
        self.sortModel.filterAccount = acc
        self.sortModel.filterChar = char
        self.sortModel.invalidateFilter()

    def filterStartTime(self, start):
        self.sortModel.filterStartTime = start
        self.sortModel.invalidateFilter()

    def filterEndTime(self, end):
        self.sortModel.filterEndTime = end
        self.sortModel.invalidateFilter()

    def getPath(self, index):
        # return index.internalPointer().path
        p = self.sortModel.mapToSource(index).internalPointer().path
        return p

    def getFilterStartTime(self):
        return self.sortModel.filterStartTime

    def getFilterEndTime(self):
        return self.sortModel.filterEndTime

class FilterModel(QSortFilterProxyModel):

    def __init__(self, parent = None):
        super(FilterModel, self).__init__()
        self.filterStartTime = QDateTime(QDate(2015,11,17)).toUTC().toSecsSinceEpoch()
        self.filterEndTime = time.time()
        self.filterSuccess = False
        self.filterNew = False
        self.filterAccount = ""
        self.filterChar = ""

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        p = source_parent.internalPointer()
        if p == self.sourceModel().root or p is None:
            return True

        node:LogBrowserNode = p.children[source_row]
        if self.filterSuccess:
            if node.result != LogBrowserModel.TXT_SUCCESS:
                return False

        if self.filterAccount is not "":
            if self.filterAccount not in node.accounts:
                return False

        if self.filterChar is not "":
            if self.filterChar not in node.characters:
                return False

        if self.filterNew:
            if not node.isNew:
                return False

        if self.filterStartTime > node.timeStamp:
            if node.timeStamp == 0:
                None
            else:
                return False

        if self.filterEndTime < node.timeStamp:
            return False

        return True

class LogBrowserModel(QAbstractItemModel):
    finished = pyqtSignal()
    treeLoaded = pyqtSignal()
    progressSignal = pyqtSignal(str, int)
    dataupdated = pyqtSignal(QModelIndex, QModelIndex)
    setProgressIndefinite = pyqtSignal(bool)

    FINDING_LOGS_TEXT = "Found %s Logs"
    PROGRESS_TEXT_FORMAT = "%s Log %s\t"


    HEADER_TIME = "Time"
    HEADER_RESULT = "Result"
    HEADER_RAIDAR = "Raidar"
    HEADER_DPSR = "dps.report"

    TXT_SUCCESS = "Success"
    TXT_FAILED = "Failed"

    def __init__(self, parent = None):
        super(LogBrowserModel, self).__init__()
        self.root = LogBrowserNode()
        self.headers = ["", self.HEADER_TIME, self.HEADER_RESULT, self.HEADER_RAIDAR, self.HEADER_DPSR, ""]
        self.buttonHeaders = [self.HEADER_DPSR, self.HEADER_RAIDAR]
        self.rootPath = ""
        self.logCount = 0
        self.currentTime = time.time()
        self.uploadToAll = False
        self.currentSelected = QModelIndex()
        self.dataupdated.connect(self.sendDataChanged)
        self.encounterCache = None
        self.signalTimer = 0
        self.counter = 0
        self.earliestLog = self.currentTime

        self.players = []

    def setSelected(self, index: QModelIndex):
        self.currentSelected = index

    def toggleUploadToAll(self, flag):

        self.uploadToAll = flag

    def setup(self, path):
        t = time.time()
        loadStartTime = t
        self.earliestLog = t
        self.root = LogBrowserNode()
        self.encounterCache = EncounterCacheHandler()
        self.players = dict()
        #self.startTime = time.time()
        self.rootPath = path
        self.counter = 0
        self.signalTimer = 0
        self.logCount = 0
        self.setProgressIndefinite.emit(True)
        self.setupTree(self.root, self.rootPath)
        print("Log Count: %s" % self.logCount)
        self.counter = 0
        self.treeLoaded.emit()
        self.setProgressIndefinite.emit(False)
        self.quickParseAll(self.root)
        self.progressSignal.emit("Done", 100)
        print("Load Time: %s" % (time.time() - loadStartTime))
        self.finished.emit()
        #print(self.players)
        # print(time.time() - self.startTime)


    def setupTree(self, parent, path):
        for f in os.listdir(path):
            toUpdate = False
            node = LogBrowserNode()
            file = path + "\\" + f
            node.path = file
            if os.path.isdir(file):
                node.text = f
                node.isLog = False
                if len(os.listdir(file)) > 0:
                    self.setupTree(node, file)
                    parent.addChild(node)
            elif os.path.isfile(file):
                name,ext = os.path.splitext(f)
                if ext == ".evtc" or ext == ".zip":
                    #print(file)
                    node.text = name.replace(".evtc", "")
                    node.isLog = True
                    for h in self.buttonHeaders:
                        node.checkables[h] = False
                    parent.addChild(node)
                    self.logCount += 1
                    self.progressSignal.emit(self.FINDING_LOGS_TEXT % self.logCount, -1)


    def quickParseAll(self, node):
        if node.isLog is False:
            for n in node.children:
                self.quickParseAll(n)
        else:
            encounterInfo:EncounterInfo = self.encounterCache.getInfo(node.path)

            if encounterInfo.kill:
                node.result = self.TXT_SUCCESS
            else:
                node.result = self.TXT_FAILED

            node.lowestBossHealth = encounterInfo.lastBossHealth
            node.time = encounterInfo.length
            node.timeStamp = encounterInfo.timestamp
            if node.timeStamp < self.earliestLog:
                self.earliestLog = node.timeStamp
            i1 = self.createIndex(node.row, 0, node)
            i2 = self.createIndex(node.row, len(self.headers), node)

            for a in encounterInfo.accounts:
                pl = encounterInfo.accounts[a]
                node.accounts.append(a)
                node.characters.append(pl['character'])
                if a not in self.players:
                    self.players[a] = dict()
                    self.players[a]['logcount'] = 0
                    self.players[a]['characters'] = dict()
                if pl['character'] not in self.players[a]['characters']:
                    self.players[a]['characters'][pl['character']] = dict()
                    self.players[a]['characters'][pl['character']]['prof'] = pl['prof']
                    self.players[a]['characters'][pl['character']]['elite'] = pl['elite']
                self.players[a]['logcount'] = self.players[a]['logcount'] + 1
                None
            self.dataupdated.emit(i1, i2)

            t = time.time()
            if self.signalTimer < t - 1:
                self.progressSignal.emit(self.PROGRESS_TEXT_FORMAT % (node.parent.text, node.row + 1),
                                         100 * self.counter / self.logCount)
                self.signalTimer = t

            self.counter += 1


    def sendDataChanged(self, i1, i2):
        self.dataChanged.emit(i1, i2, [Qt.DisplayRole])

    def parent(self, child: QModelIndex):

        if not child.isValid():
            return QModelIndex()
        parentNode = child.internalPointer().parent
        if parentNode == self.root:
            return QModelIndex()

        return self.createIndex(parentNode.row, 0, parentNode)

    def index(self, row: int, column: int, parent: QModelIndex = ...):
        parentNode = self.root

        if parent.isValid():
            parentNode = parent.internalPointer()

        if row < len(parentNode.children) and column < len(self.headers):
            index = self.createIndex(row, column, parentNode.children[row])
            #print(index)
            return index
        else:
            return QModelIndex()

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return QVariant()

        node: LogBrowserNode = index.internalPointer()

        if role == Qt.TextAlignmentRole and self.headers[index.column()] in self.buttonHeaders:
            return Qt.AlignCenter

        if role == Qt.BackgroundRole and self.currentSelected.isValid():
            if index.internalPointer() == self.currentSelected.internalPointer() \
                    or index.internalPointer() == self.currentSelected.internalPointer().parent:
                return reference.HIGHLIGHT_COLOR

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return node.text
            else:
                if node.parent == self.root:
                    return
                h = self.headers[index.column()]
                txt = ''
                if h == self.HEADER_TIME:
                    txt += tools.prettyTimestamp(node.time)
                if h == self.HEADER_RESULT:
                    txt += node.result
                    if node.lowestBossHealth > 0:
                        txt += ": %s%%" % str(node.lowestBossHealth/100)
                return txt

        if role == Qt.CheckStateRole:
            if self.headers[index.column()] in self.buttonHeaders and node.isLog:
                return node.checkables[self.headers[index.column()]]
            return QVariant()

    def setData(self, index: QModelIndex, value, role: int = ...):
        if index.isValid():
            node: LogBrowserNode = index.internalPointer()
            tag = self.headers[index.column()]
            if self.uploadToAll:
                tag = LogBrowserNode.CHECK_ALL
            node.checkForUpload(tag, value)
            self.dataChanged.emit(self.createIndex(index.row(), 0, node), self.createIndex(index.row(), len(self.headers), node))
            return True
        return False


    def flags(self, index: QModelIndex):
        flags = Qt.ItemIsEnabled
        if self.headers[index.column()] in self.buttonHeaders and index.internalPointer().parent != self.root:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def rowCount(self, parent: QModelIndex = ...):
        if not parent.isValid():
            return len(self.root.children)

        if parent.isValid():
            return len(parent.internalPointer().children)

    def columnCount(self, parent: QModelIndex = ...):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and section > 0:
            return self.headers[section]

class LogBrowserNode():

    CHECK_ALL = -123

    def __init__(self):
        self.parent = None
        self.text = "None"
        self.children = []
        self.row = -1
        self.path = None
        self.result = "Unknown"
        self.lowestBossHealth = 10000
        self.index = QModelIndex()
        self.timeStamp = 0
        self.time = 0
        self.checkables = dict()
        self.uploading = False
        self.progress = 0
        self.isLog = False
        self.isNew = False
        self.accounts = []
        self.characters = []

    def addChild(self, node):
        node.parent = self
        node.row = len(self.children)
        self.children.append(node)

    def checkForUpload(self, tag, flag):
        if tag == self.CHECK_ALL:
            for t in self.checkables:
                self.checkables[t] = flag
        else:
            self.checkables[tag] = flag