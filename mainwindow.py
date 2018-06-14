import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QModelIndex, QPoint, QRect, QDateTime, QDate, Qt
from PyQt5.QtWidgets import QComboBox, QDialog, QPushButton

from encounter import Encounter
import worker as Worker
from worker import Job

from encounterpreviewtable import EncounterPreviewTable
from logtree import LogTree, LogBrowserModel
from datedialog import DateDialog
import os

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('arcui.ui', self)
        self.show()

        #self.fullParse.clicked.connect(self.openFull)
        #self.quickParse.clicked.connect(self.openQuick)

        self.progressBarText = ''

        #self.dataTable.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.findLogsPath()
        self.browseButton.clicked.connect(self.browseLogFolder)
        self.viewButton.clicked.connect(self.openLogFolder)
        self.logBrowserModel = None

        # self.playerBoonList.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # self.playerBoonList.setInsertPolicy(QComboBox.InsertAlphabetically)

        self.startDateButton.clicked.connect(self.showStartDateDialog)
        self.endDateButton.clicked.connect(self.showEndDateDialog)

        self.dateDialog = DateDialog()
        self.dateDialog.getCalendar().selectionChanged.connect(self.setFilterDate)
        self.currentDateButton = None

    def showStartDateDialog(self):
        if not self.positionDateDialog(self.startDateButton):
            return
        date:QDate = QDateTime.fromSecsSinceEpoch(self.logBrowserTable.getFilterStartTime(), Qt.UTC).toLocalTime().date()
        self.dateDialog.setDate(date)
        self.dateDialog.show()

    def showEndDateDialog(self):
        if not self.positionDateDialog(self.endDateButton):
            return
        date:QDate = QDateTime.fromSecsSinceEpoch(self.logBrowserTable.getFilterEndTime(), Qt.UTC).toLocalTime().date()
        self.dateDialog.setDate(date)
        self.dateDialog.show()

    def setFilterDate(self):
        date = self.dateDialog.getCalendar().selectedDate()
        print(date)
        if self.currentDateButton == self.startDateButton:
            self.startDateButton.setText(date.toString())
            date = QDateTime(date).toUTC().toSecsSinceEpoch()
            self.logBrowserTable.filterStartTime(date)

        if self.currentDateButton == self.endDateButton:
            self.endDateButton.setText(date.toString())
            date = QDateTime(date).addDays(1).toUTC().toSecsSinceEpoch()
            self.logBrowserTable.filterEndTime(date)


    def positionDateDialog(self, button):
        if self.currentDateButton == button:
            self.dateDialog.hide()
            self.currentDateButton = None
            return False
        pos: QPoint = button.pos()
        buttonSize: QRect = button.rect()
        dialogSize: QRect = self.dateDialog.rect()
        pos.setY(pos.y() + buttonSize.height())
        pos.setX(pos.x() + buttonSize.width() - dialogSize.width())
        globalPos = button.parent().mapToGlobal(pos)
        inWindowPos = self.mapFromGlobal(globalPos)
        self.dateDialog.setParent(self)
        self.dateDialog.move(inWindowPos.x(), inWindowPos.y())
        self.currentDateButton = button
        return True

    def findLogsPath(self):
        #self.logPathEdit.setText('F:/arcdps.cbtlogs')
        folder = os.environ['USERPROFILE'] + "\\My Documents\\Guild Wars 2\\addons\\arcdps\\arcdps.cbtlogs"
        if os.path.exists(folder) and os.path.isdir(folder):
            self.logPathEdit.setText(folder)

    def browseLogFolder(self):
        logDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Main Arc Folder", os.environ['USERPROFILE'])
        self.logPathEdit.setText(logDir)

    def openLogFolder(self):

        self.logBrowserTable.toggleUploadToAll(self.checkUploadAll.isChecked())
        self.checkUploadAll.stateChanged.connect(self.logBrowserTable.toggleUploadToAll)

        logModel:LogBrowserModel = self.logBrowserTable.getModel()
        logModel.progressSignal.connect(self.setProgress)
        logModel.setProgressIndefinite.connect(self.setProgressBarStatus)

        self.logBrowserTable.clicked.connect(self.showEncounterDetails)
        self.logBrowserTable.setup(self.logPathEdit.text())

        self.filterSuccessCheck.stateChanged.connect(self.logBrowserTable.filterSuccess)
        self.filterNewCheck.stateChanged.connect(self.logBrowserTable.filterNew)

    def showEncounterDetails(self, index:QModelIndex):
        path = self.logBrowserTable.getPath(index)
        name, ext = os.path.splitext(path)
        if ext != ".evtc":
            return
        self.encounterPreviewTable.setup(path)
        # self.encounterPreviewTable.clicked.connect(self.viewPlayerDetails)


    # def viewPlayerDetails(self, index: QModelIndex):
    #     encounter:Encounter = index.model().sourceModel().encounter
    #     node = index.model().mapToSource(index).internalPointer()
    #     player:Entity = encounter.entities[node.player]
    #     self.plot1.showSkillDps(player, encounter)

        # for i, b in enumerate(player.buffs.buffList):
        #     self.playerBoonList.insertItem(i, encounter.skills[b], b)
        #
        # self.matPlotWidget.plotBoon(player.buffs.buffList[740])

    # def analyze(self, encounter):
    #     model = None
    #     if encounter.damageIncModel == None:
    #         model = DamageIncModel(encounter)
    #         encounter.damageIncModel = model
    #     else:
    #         model = encounter.damageIncModel
    #
    #     self.dataTable.expanded.connect(model.expanded)
    #     self.dataTable.collapsed.connect(model.collapsed)
    #     self.dataTable.setModel(model)
    #
    #     return

    # def openQuick(self):
    #     encounter = self.openFile()
    #     encounter.finished.connect(self.onFinish)
    #     worker = Worker(encounter.parseQuick)
    #     self.threadpool.start(worker)

    # def openFull(self):
    #     encounter = self.openFile()
    #     encounter.fullFinished.connect(self.analyze)
    #     job = Job(encounter.parseFull)
    #     Worker.ThreadPool.start(job)
    #
    # def openFile(self):
    #     self.log("----------")
    #     name = self.fileEdit.text()
    #     encounter = Encounter(name)
    #     encounter.progressSignal.connect(self.setProgress)
    #     encounter.logSignal.connect(self.log)
    #     return encounter

    def setProgress(self, s, val):
        #print("setProgress")
        if not s == self.progressBarText:
            if val == -1:
                self.progressBar.setFormat(s)
            else:
                self.progressBar.setFormat(s + " %p%")
            self.progressBarText = s
        self.progressBar.setValue(val)

    # def log(self, txt):
    #     self.logEdit.append(txt)

    def onFinish(self, encounter):
        self.log("Result: %s" % encounter.result)

    def setProgressBarStatus(self, indefinite):
        if indefinite:
            self.progressBar.setMaximum(0)
        elif not indefinite:
            self.progressBar.setMaximum(100)

if __name__ == '__main__':
    #print(os.environ)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
