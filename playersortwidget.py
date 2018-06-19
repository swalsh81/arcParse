from PyQt5.QtWidgets import QWidget, QComboBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import QPixmap, QIcon

from resourcehandler import ResourceHandler


class PlayerSortWidget(QWidget):

    selectionChanged = pyqtSignal(str, str)

    def __init__(self, parent):
        super(PlayerSortWidget, self).__init__(parent)

        self.accountBox:QComboBox = QComboBox()
        self.charBox:QComboBox = QComboBox()

        self.accounts = []
        self.characters = []
        self.players = dict()

        self.resourceHandler = ResourceHandler()

    def newSelection(self):
        account = ""
        character = ""

        if self.accountBox.currentIndex() > 0:
            account = self.accountBox.currentText()

        if self.charBox.currentIndex() > 0:
            character = self.charBox.currentText()

        self.selectionChanged.emit(account, character)

    def setBoxes(self, accountBox, charBox):
        self.accountBox = accountBox
        self.charBox = charBox
        self.accountBox.currentIndexChanged.connect(self.setCharacters)
        self.accountBox.currentIndexChanged.connect(self.newSelection)
        self.charBox.currentIndexChanged.connect(self.newSelection)

    def setPlayers(self, players):
        self.players = players
        self.accounts = []
        for a in players:
            self.accounts.append(a)
        self.accounts = sorted(players, key=lambda x:self.players[x]['logcount'], reverse=True)
        #print(self.accounts)
        self.accountBox.addItem("Player")
        self.accountBox.addItems(self.accounts)

    def setCharacters(self, account):
        self.charBox.clear()
        if account == 0:
            self.charBox.addItem("Character")
            return
        else:
            self.charBox.addItem("Any")
            account -= 1

        account = self.accounts[account]
        if account in self.players:
            for char in self.players[account]['characters']:
                c = self.players[account]['characters'][char]
                p = QPixmap()
                p.loadFromData(self.resourceHandler.getSpecialization(c['elite'], c['prof'])[self.resourceHandler.PROFESSION_ICON])
                self.charBox.addItem(QIcon(p), char)
                #self.charBox.setItemIcon(i, self.resourceHandler.getSpecialization(c['elite'], c['prof']))
