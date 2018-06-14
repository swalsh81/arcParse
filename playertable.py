from PyQt5 import QtCore, QtGui, QtWidgets

from matplotlib.figure import Figure, SubplotParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib import rcParams, font_manager

from entity import Entity
from encounter import Encounter

import reference

class PlayerTable(QtWidgets.QTableView):

    def __init__(self, parent):
        super(PlayerTable, self).__init__(parent)
        self.canvas = MplCanvas()

        self.vbl = QtWidgets.QVBoxLayout()  # Set box for plotting
        self.vbl.setContentsMargins(0,0,0,0)
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

        self.encounter = None

    def setData(self, p:Entity, e:Encounter):
        values = []
        labels = []
        zipped = []

        i = 0
        for skill in p.damageOutTotals:
            if skill < 0:
                continue
            s = p.damageOutTotals[skill]
            values.append(s[Entity.SKILL_TOTAL_DAMAGE])
            labels.append(e.skills[skill])
            i += 1
        zipped = list(zip(labels, values))
        sort = sorted(zipped, key=lambda x:x[1])
        labels, values = zip(*sort)

        self.canvas.ax.clear()
        #self.canvas.ax.axis('tight')
        self.canvas.ax.axis('off')
        rects = self.canvas.ax.barh(y=labels, width=values,align='center', color=reference.HIGHLIGHT_COLOR_ARRAY)
        self.canvas.ax.xaxis.set_visible(False)
        self.canvas.ax.yaxis.set_visible(False)
        fontSize = (self.canvas.fig.bbox.height/len(rects))*rects[0].get_height()*.5
        rcParams.update({'font.size': fontSize})
        i = 0
        for r in rects:
            self.canvas.ax.text(0,r.get_height()/2 + r.get_y(), '%s %d'%(labels[i],values[i]), ha='left', va='center')
            i += 1

        self.canvas.draw()
        self.canvas.flush_events()

class MplCanvas(Canvas):
    def __init__(self):
        rcParams.update({'figure.autolayout': True})
        #props = font_manager.FontProperties(family=['sans-serif', 'monospace'])
        #font_manager.FontManager(props)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        #self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        Canvas.__init__(self, self.fig)

if __name__ == '__main__':
    l1 = [3,5,1,7,9,8,2,4,6,10]
    l2 = ["a","b", "c", "d", "e", "f", "g", "h", "i", "j"]
    d = list(zip(l1,l2))
    sort = sorted(d, key=lambda x:x[0])
    print(d)
    print(sort)
    x1, x2 = zip(*sort)
    print(x1)
    print(x2)