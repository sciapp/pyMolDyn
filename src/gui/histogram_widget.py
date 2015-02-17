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
import numpy as np
import os
from math import floor


logger = Logger("gui.histogram_widget")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class GrHistogramWidget(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self)

        self.init_gui(self)

        os.environ["GKS_WSTYPE"] = "381"
        os.environ["GKS_DOUBLE_BUF"] = "True"

        self.w = 500
        self.h = 500
        self.sizex = 1
        self.sizey = 1
        self.xvalues = None
        self.yvalues = None
        self.title = None
        self.datapoints = None

    def init_gui(self, form):
        form.resize(QtCore.QSize(500, 500).expandedTo(form.minimumSizeHint()))
        QtCore.QMetaObject.connectSlotsByName(form)

    def setdata(self, xvalues, yvalues, widths, title):
        self.xvalues = xvalues
        self.yvalues = yvalues
        self.widths = widths
        self.title = title

    def draw(self):
        self.setStyleSheet("background-color:white;")

        if self.xvalues is not None and self.widths is not None:
            maxidx = np.argmax(self.xvalues)
            rangex = (self.xvalues.min(),
                      self.xvalues[maxidx] + self.widths[maxidx])
        else:
            rangex = (0.0, 100.0)
        if self.yvalues is not None:
            rangey = gr.adjustrange(0.0, self.yvalues.max())
        else:
            rangey = (0.0, 8.0)

        gr.clearws()
        mwidth = self.w * 2.54 / self.logicalDpiX() / 100
        mheight = self.h * 2.54 / self.logicalDpiY() / 100
        gr.setwsviewport(0, mwidth, 0, mheight)
        gr.setwswindow(0, self.sizex, 0, self.sizey)
        gr.setviewport(0.075 * self.sizex, 0.95 * self.sizex,
                       0.075 * self.sizey, 0.95 * self.sizey)
        gr.setwindow(rangex[0], rangex[1], rangey[0], rangey[1])
        gr.setcharheight(0.012)

        gr.setfillintstyle(1)
        gr.setfillcolorind(0)
        gr.fillrect(rangex[0], rangex[1], rangey[0], rangey[1])

        if self.xvalues is not None and self.yvalues is not None \
                and self.widths is not None:
            gr.setfillintstyle(1)
            gr.setfillcolorind(2)
            for i in range(self.xvalues.size):
                gr.fillrect(self.xvalues[i],
                            self.xvalues[i] + self.widths[i] * 0.8,
                            0.0, self.yvalues[i])
        else:
            gr.text(0.45 * self.sizex, 0.5 * self.sizey, "no data")

        gr.setlinecolorind(1)
        xtick = floor(0.02 * (rangex[1] - rangey[0]) * 100.0) / 100.0
        ytick = floor(0.04 * (rangey[1] - rangey[0]) * 50.0) / 50.0
        gr.axes(xtick, ytick, rangex[0], rangey[0], 10, 5, 0.0075)
        gr.axes(xtick, ytick, rangex[1], rangey[1], -10, -5, -0.0075)

        if self.title is not None:
            gr.text(0.8 * self.sizex, 0.9 * self.sizey, self.title)
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

    def paintEvent(self, ev):
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        self_pointer = long(shiboken.getCppPointer(self)[0])
        painter_pointer = long(shiboken.getCppPointer(self.painter)[0])
        os.environ['GKSconid'] = "%x!%x" % (self_pointer, painter_pointer)
        self.draw()
        gr.updatews()
        self.painter.end()


class HistogramWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.control = parent.control
        self.results = None

        self.init_gui()

    def init_gui(self):
        vbox = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()
        self.gr_widget = GrHistogramWidget()

        self.datasetlabel = QtGui.QLabel("No data loaded. Press 'Refresh'.", self)
        self.datasetlabel.setAlignment(QtCore.Qt.AlignHCenter)

        selectbox = QtGui.QHBoxLayout()
        selectbuttongroup = QtGui.QButtonGroup(self)
        self.volumebutton = QtGui.QRadioButton("Cavity Volume", self)
        selectbox.addWidget(self.volumebutton)
        selectbuttongroup.addButton(self.volumebutton)
        self.areabutton = QtGui.QRadioButton("Surface Area", self)
        selectbox.addWidget(self.areabutton)
        selectbuttongroup.addButton(self.areabutton)
        self.volumebutton.setChecked(True)
        grid.addLayout(selectbox, 0, 0)

        self.weightbutton = QtGui.QCheckBox("Weighted Histogram", self)
        self.weightbutton.setChecked(True)
        grid.addWidget(self.weightbutton, 0, 1)

        binbox = QtGui.QHBoxLayout()
        binbox.addWidget(QtGui.QLabel("Number of Bins:", self), 0, 0)
        self.nbins = QtGui.QLineEdit(self)
        binbox.addWidget(self.nbins, 0, 1)
        grid.addLayout(binbox, 0, 2)

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
        widths = None
        title = None
        if self.results is None:
            self.refresh()
        if self.results is not None and self.results.surface_cavities is not None:
            nbins = str(self.nbins.text())
            if len(nbins) > 0 and float(nbins) > 0:
                nbins = float(nbins)
            else:
                nbins = 50
            if self.volumebutton.isChecked():
                data = self.results.surface_cavities.volumes
            else:
                data = self.results.surface_cavities.surface_areas
            if len(data) > 0:
                if self.weightbutton.isChecked():
                    hist, bin_edges = np.histogram(data, bins=nbins, weights=data)
                else:
                    hist, bin_edges = np.histogram(data, bins=nbins)
                widths = bin_edges[1:] - bin_edges[:-1]
                xvalues = bin_edges[:-1]
                yvalues = hist

        self.gr_widget.setdata(xvalues, yvalues, widths, title)
        self.gr_widget.draw()

    def export(self):
        extensions = (".eps", ".ps", ".pdf", ".png", ".bmp", ".jpg", ".jpeg",
                      ".png", ".tiff", ".fig", ".svg", ".wmf")
        qtext = "*" + " *".join(extensions)
        filepath, okay = QtGui.QFileDialog.getSaveFileName(self, "Save Image",
                                                           ".", "Image Files ({})".format(qtext))
        if not okay or len(filepath) == 0:
            return
        gr.beginprint(filepath)
        self.draw()
        gr.endprint()

    def refresh(self):
        results = self.control.results
        if results is not None:
            results = results[-1][-1]
            if self.results != results:
                self.results = results
                self.gr_widget.setdata(None, None, None, None)
                self.gr_widget.draw()
            self.datasetlabel.setText(str(results))
        else:
            self.datasetlabel.setText("")
            self.elem1.clear()
            self.elem2.clear()
