# -*- coding: utf-8 -*-


from PySide import QtCore, QtGui
import os
from gr.pygr import *
try:
    from PySide import shiboken
except ImportError:
    import shiboken

from util.logger import Logger
import sys
from statistics.rdf import RDF
import numpy as np
import os


logger = Logger("gui.gr_widget")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class GrWidget(QtGui.QWidget) :
    def __init__(self, *args) :
        QtGui.QWidget.__init__(self)

        self.init_gui(self)

        os.environ["GKS_WSTYPE"] = "381"
        os.environ["GKS_DOUBLE_BUF"] = "True"

        #self.connect(self.DrawButton, QtCore.SIGNAL("clicked()"), self.draw)
        #self.connect(self.QuitButton, QtCore.SIGNAL("clicked()"), self.quit)
        self.w = 500
        self.h = 500
        self.sizex = 1
        self.sizey = 1
        self.xvalues = None
        self.yvalues = None
        self.title = None
        self.datapoints = None

    def init_gui(self, form) :
        form.setWindowTitle("GrWidget")
        form.resize(QtCore.QSize(500, 500).expandedTo(form.minimumSizeHint()))

        #self.DrawButton = QtGui.QPushButton(form)
        #self.DrawButton.setText("Draw")
        #self.DrawButton.setGeometry(QtCore.QRect(290, 5, 100, 25))
        #self.DrawButton.setObjectName("draw")

        #self.QuitButton = QtGui.QPushButton(form)
        #self.QuitButton.setText("Quit")
        #self.QuitButton.setGeometry(QtCore.QRect(395, 5, 100, 25))
        #self.QuitButton.setObjectName("quit")

        QtCore.QMetaObject.connectSlotsByName(form)

    def quit(self) :
        gr.emergencyclosegks()
        self.close()

    def setdata(self, xvalues, yvalues, title, datapoints=None):
        self.xvalues = xvalues
        self.yvalues = yvalues
        self.title = title
        self.datapoints = datapoints

    def draw(self) :
        self.setStyleSheet("background-color:white;");

        #x = range(0, 128)
        #y = range(0, 128)
        #z = readfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),
        #                          "kws.dat"), separator='$')
        #zrange = max(z) - min(z)
        #h = [min(z) + i * 0.025 * zrange for i in range(0, 40)]

        if not self.xvalues is None:
            rangex = (self.xvalues.min(), self.xvalues.max())
        else:
            rangex = (0, 10)
        if not self.yvalues is None:
            rangey = gr.adjustrange(self.yvalues.min(), self.yvalues.max())
        else:
            rangey = (0, 4)

        gr.clearws()
        mwidth  = self.w * 2.54 / self.logicalDpiX() / 100
        mheight = self.h * 2.54 / self.logicalDpiY() / 100
        gr.setwsviewport(0, mwidth, 0, mheight)
        gr.setwswindow(0, self.sizex, 0, self.sizey)
        gr.setviewport(0.075 * self.sizex, 0.95 * self.sizex, 0.075 * self.sizey, 0.95 * self.sizey)
        gr.setwindow(rangex[0], rangex[1], rangey[0], rangey[1])
        gr.setcharheight(0.012)

        gr.setfillintstyle(1)
        gr.setfillcolorind(0)
        gr.fillrect(rangex[0], rangex[1], rangey[0], rangey[1])

        if not self.xvalues is None and not self.yvalues is None:
            gr.setlinecolorind(2)
            gr.polyline(self.xvalues, self.yvalues)
        else:
            gr.text(0.4, 0.45, "no elements selected")

        if not self.datapoints is None:
            gr.setmarkertype(gr.MARKERTYPE_SOLID_TRI_UP)
            gr.setmarkercolorind(2)
            gr.setmarkersize(1.0)
            gr.polymarker(self.datapoints, np.zeros_like(self.datapoints))

        gr.setlinecolorind(1)
        gr.axes(0.2, 0.2, rangex[0], rangey[0], 5, 5, 0.0075)
        gr.axes(0.2, 0.2, rangex[1], rangey[1], -5, -5, -0.0075)

        if not self.title is None:
            gr.text(0.75, 0.65, self.title)
        self.update()

    def resizeEvent(self, event):
        self.w = event.size().width()
        self.h = event.size().height()
        if self.w > self.h:
            self.sizex = 1
            self.sizey = float(self.h)/self.w
        else:
            self.sizex = float(self.w)/self.h
            self.sizey = 1
        self.draw()

    def paintEvent(self, ev) :
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        os.environ['GKSconid'] = "%x!%x" % (long(shiboken.getCppPointer(self)[0]), long(shiboken.getCppPointer(self.painter)[0]))
        gr.updatews()
        self.painter.end()


class GRView(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.control = parent.control
        self.results = None
        self.rdf = None

        self.init_gui()

    def init_gui(self):
        vbox = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()
        self.gr_widget = GrWidget()

        self.datasetlabel = QtGui.QLabel("No data loaded. Press 'Refresh'.", self)
        self.datasetlabel.setAlignment(QtCore.Qt.AlignHCenter)

        elembox = QtGui.QHBoxLayout()
        elembox.addWidget(QtGui.QLabel("Elements:", self), 0, 0)
        self.elem1 = QtGui.QComboBox(self)
        elembox.addWidget(self.elem1, 0, 1)
        self.elem2 = QtGui.QComboBox(self)
        elembox.addWidget(self.elem2, 0, 2)
        grid.addLayout(elembox, 0, 0)

        rangebox = QtGui.QHBoxLayout()
        rangebox.addWidget(QtGui.QLabel("Plot range:", self))
        self.range1 = QtGui.QLineEdit("0", self)
        rangebox.addWidget(self.range1)
        rangebox.addWidget(QtGui.QLabel("-", self))
        self.range2 = QtGui.QLineEdit("10", self)
        rangebox.addWidget(self.range2)
        grid.addLayout(rangebox, 0, 1)

        cutoffbox = QtGui.QHBoxLayout()
        cutoffbox.addWidget(QtGui.QLabel("Cutoff:", self))
        self.cutoff = QtGui.QLineEdit("", self)
        cutoffbox.addWidget(self.cutoff)
        cutoffbox.addWidget(QtGui.QLabel("Bandwidth:", self))
        self.bandwidth = QtGui.QLineEdit("", self)
        cutoffbox.addWidget(self.bandwidth)
        grid.addLayout(cutoffbox, 0, 2)

        self.plotbutton = QtGui.QPushButton("Plot", self)
        grid.addWidget(self.plotbutton, 1, 0)
        self.connect(self.plotbutton, QtCore.SIGNAL("clicked()"), self.draw)

        self.exportbutton = QtGui.QPushButton("Save Image", self)
        grid.addWidget(self.exportbutton, 1, 1)
        self.connect(self.exportbutton, QtCore.SIGNAL("clicked()"), self.export)

        self.refreshbutton = QtGui.QPushButton("Refresh Data", self)
        grid.addWidget(self.refreshbutton, 1, 2)
        self.connect(self.refreshbutton, QtCore.SIGNAL("clicked()"), self.refresh)

        vbox.addWidget(self.gr_widget, stretch=1)
        vbox.addWidget(self.datasetlabel, stretch=0)
        vbox.addLayout(grid)
        self.setLayout(vbox)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return \
                or event.key() == QtCore.Qt.Key_Enter:
            self.draw()

    def draw(self):
        xvalues = None
        yvalues = None
        title = None
        datapoints = None
        if self.rdf is None:
            self.refresh()
        if not self.rdf is None:
            elem1 = str(self.elem1.currentText())
            elem2 = str(self.elem2.currentText())
            range1 = float(str(self.range1.text()))
            range2 = float(str(self.range2.text()))
            cutoff = str(self.cutoff.text())
            if len(cutoff) > 0 and float(cutoff) > 0:
                cutoff = float(cutoff)
            else:
                cutoff = None
            bandwidth = str(self.bandwidth.text())
            if len(bandwidth) > 0 and float(bandwidth) > 0:
                bandwidth = float(bandwidth)
            else:
                bandwidth = None
            f = self.rdf.rdf(elem1, elem2, cutoff=cutoff, h=bandwidth)
            if not f is None:
                xvalues = np.linspace(range1, range2, 400)
                yvalues = f(xvalues)
                title = "{} - {}".format(elem1, elem2)
                datapoints = f.f.x

        self.gr_widget.setdata(xvalues, yvalues, title, datapoints)
        self.gr_widget.draw()

    def export(self):
        extensions = (".eps", ".ps", ".pdf", ".png", ".bmp", ".jpg", ".jpeg", ".png", ".tiff", ".fig", ".svg", ".wmf")
        qtext = "*" + " *".join(extensions)
        filepath, _ = QtGui.QFileDialog.getSaveFileName(self, "Save Image", \
                ".", "Image Files ({})".format(qtext))
        if len(filepath) == 0:
            return
        gr.beginprint(filepath)
        self.draw()
        gr.endprint()

    def refresh(self):
        results = self.control.results
        if not results is None:
            results = results[-1][-1]
            if self.results != results or self.rdf is None:
                self.results = results
                self.rdf = RDF(results)
                e = np.unique(results.atoms.elements).tolist()
                if len(results.domains.centers) > 0 and not "cav" in e:
                    e.append("cav")
                self.elem1.clear()
                self.elem1.addItems(e)
                self.elem2.clear()
                self.elem2.addItems(e)
                self.gr_widget.setdata(None, None, None)
                self.gr_widget.draw()
            dataset = "{}, frame {}, resolution {}".format(
                    os.path.basename(results.filepath),
                    results.frame + 1,
                    results.resolution)
            self.datasetlabel.setText(dataset)
        else:
            self.datasetlabel.setText("")
            self.elem1.clear()
            self.elem2.clear()
