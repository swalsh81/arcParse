import sys
from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QThreadPool
from plotwidget import PlotWidget
from encounter import Encounter
from worker import Worker




class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.show()

        self.fullParse.clicked.connect(self.openFull)
        self.quickParse.clicked.connect(self.openQuick)

        self.threadpool = QThreadPool()

        self.progressBarText = ''

    def openFull(self, encounter):
        encounter = self.openFile()
        encounter.finished.connect(self.analyze)
        worker = Worker(encounter.parseFull)
        self.threadpool.start(worker)

    def analyze(self, encounter):
        for e in encounter.entities:
            if encounter.entities[e].isPlayer:
                p = encounter.entities[e]
                self.log("\n" + p.character)

                for source in p.damageInc:
                    self.log('-')
                    self.log("From: %s" % encounter.entities[source].name)
                    src = p.damageInc[source]
                    for skill in src:
                        sk = src[skill]
                        self.log("%s hit %s times for %s damage" % (encounter.skills[skill], str(sk['count']), str(sk['damage'])))

    def openQuick(self, encounter):
        encounter = self.openFile()
        worker = Worker(encounter.parseQuick)
        self.threadpool.start(worker)

    def openFile(self):
        name = self.fileEdit.text()
        encounter = Encounter(name)
        encounter.progressSignal.connect(self.setProgress)
        encounter.logSignal.connect(self.log)
        return encounter

    def setProgress(self, s, val):
        #print("setProgress")
        if not s == self.progressBarText:
            self.progressBar.setFormat(s + " %p%")
            self.progressBarText = s
        self.progressBar.setValue(val)

    def log(self, txt):
        self.logEdit.append(txt)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
