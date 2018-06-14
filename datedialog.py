from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt

class DateDialog(QtWidgets.QDialog):

    def __init__(self):
        super(DateDialog, self).__init__()
        uic.loadUi('calendarDialog.ui', self)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def getCalendar(self):
        return self.calendarWidget

    def setDate(self, date):
        self.calendarWidget.setSelectedDate(date)