# -*- coding: utf-8 -*-


from PyQt4 import QtCore, QtGui
import gr
from qtgr import GRWidget
import csv

from util.logger import Logger
import sys
from statistics.rdf import RDF
import numpy as np
import os


logger = Logger("gui.rdf_widget")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class GrPlotWidget(GRWidget):
    def __init__(self, *args, **kwargs):
        super(GrPlotWidget, self).__init__(*args, **kwargs)

        self.init_gui(self)

        self.xvalues = None
        self.yvalues = None
        self.title = None
        self.datapoints = None

    def init_gui(self, form):
        form.resize(QtCore.QSize(500, 500).expandedTo(form.minimumSizeHint()))
        QtCore.QMetaObject.connectSlotsByName(form)

    def quit(self):
        gr.emergencyclosegks()
        self.close()

    def setdata(self, xvalues, yvalues, title, datapoints=None):
        self.xvalues = xvalues
        self.yvalues = yvalues
        self.title = title
        self.datapoints = datapoints

    def draw(self, wsviewport=None):
        if self.xvalues is not None:
            rangex = (self.xvalues.min(), self.xvalues.max())
        else:
            rangex = (0, 10)
        if self.yvalues is not None:
            rangey = gr.adjustrange(self.yvalues.min(), self.yvalues.max())
        else:
            rangey = (0, 4)

        if wsviewport is None:
            gr.setwsviewport(0, self.mwidth, 0, self.mheight)
        else:
            gr.setwsviewport(*wsviewport)
        gr.setwswindow(0, self.sizex, 0, self.sizey)
        gr.setviewport(0.075 * self.sizex, 0.95 * self.sizex,
                       0.075 * self.sizey, 0.95 * self.sizey)
        gr.setwindow(rangex[0], rangex[1], rangey[0], rangey[1])
        gr.setcharheight(0.012)

        gr.setfillintstyle(1)
        gr.setfillcolorind(0)
        gr.fillrect(rangex[0], rangex[1], rangey[0], rangey[1])

        if self.xvalues is not None and self.yvalues is not None:
            gr.setlinecolorind(2)
            gr.polyline(self.xvalues, self.yvalues)
        else:
            gr.text(0.4 * self.sizex, 0.5 * self.sizey, "no elements selected")

        gr.setlinecolorind(1)
        gr.axes(0.2, 0.2, rangex[0], rangey[0], 5, 5, 0.0075)
        gr.axes(0.2, 0.2, rangex[1], rangey[1], -5, -5, -0.0075)

        if self.title is not None:
            gr.text(0.8 * self.sizex, 0.9 * self.sizey, self.title)


class RDFWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.control = parent.control
        self.results = None
        self.rdf = None

        self.init_gui()

    def init_gui(self):
        vbox = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()
        self.gr_widget = GrPlotWidget()

        self.datasetlabel = QtGui.QLabel("No data loaded.", self)
        self.datasetlabel.setAlignment(QtCore.Qt.AlignHCenter)

        elembox = QtGui.QHBoxLayout()
        elembox.addWidget(QtGui.QLabel("Elements:", self), 0)
        self.elem1 = QtGui.QComboBox(self)
        self.elem1.setMinimumWidth(170)
        elembox.addWidget(self.elem1, 0, QtCore.Qt.AlignLeft)
        self.elem2 = QtGui.QComboBox(self)
        self.elem2.setMinimumWidth(170)
        elembox.addWidget(self.elem2, 0, QtCore.Qt.AlignRight)
        grid.addLayout(elembox, 0, 0)

        rangebox = QtGui.QHBoxLayout()
        rangebox.addWidget(QtGui.QLabel("Plot range:", self))
        self.range1 = QtGui.QLineEdit("0", self)
        self.range1.setMinimumWidth(30)
        rangebox.addWidget(self.range1)
        rangebox.addWidget(QtGui.QLabel("-", self))
        self.range2 = QtGui.QLineEdit("8", self)
        self.range2.setMinimumWidth(30)
        rangebox.addWidget(self.range2)
        grid.addLayout(rangebox, 0, 1)

        cutoffbox = QtGui.QHBoxLayout()
        cutoffbox.addWidget(QtGui.QLabel("Cutoff:", self))
        self.cutoff = QtGui.QLineEdit("12", self)
        self.cutoff.setMinimumWidth(30)
        cutoffbox.addWidget(self.cutoff)
        cutoffbox.addWidget(QtGui.QLabel("Bandwidth:", self))
        self.bandwidth = QtGui.QLineEdit("", self)
        self.bandwidth.setMinimumWidth(30)
        cutoffbox.addWidget(self.bandwidth)
        grid.addLayout(cutoffbox, 0, 2)

        buttonbox = QtGui.QHBoxLayout()

        self.plotbutton = QtGui.QPushButton("Plot", self)
        buttonbox.addWidget(self.plotbutton)
        self.connect(self.plotbutton, QtCore.SIGNAL("clicked()"), self.draw)

        self.export_image_button = QtGui.QPushButton("Save Image", self)
        buttonbox.addWidget(self.export_image_button)
        self.connect(self.export_image_button, QtCore.SIGNAL("clicked()"), self.export_image)

        self.export_data_button = QtGui.QPushButton("Export Data", self)
        buttonbox.addWidget(self.export_data_button)
        self.connect(self.export_data_button, QtCore.SIGNAL("clicked()"), self.export_data)
        grid.addLayout(buttonbox, 1, 0, 1, 3)

        vbox.addWidget(self.gr_widget, stretch=1)
        vbox.addWidget(self.datasetlabel, stretch=0)
        vbox.addLayout(grid)
        self.setLayout(vbox)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return \
                or event.key() == QtCore.Qt.Key_Enter:
            self.draw()

    def draw(self, now=False, wsviewport=None):
        xvalues = None
        yvalues = None
        title = None
        datapoints = None
        if self.rdf is None:
            self.refresh()
        if self.rdf is not None:
            elem1 = str(self.elem1.currentText())
            if elem1 == "cavity domain centers":
                elem1 = "cav"
            elem2 = str(self.elem2.currentText())
            if elem2 == "cavity domain centers":
                elem2 = "cav"
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
            if f is not None:
                xvalues = np.linspace(range1, range2, 400)
                yvalues = f(xvalues)
                title = "{} - {}".format(elem1, elem2)
                datapoints = f.f.x

        self.gr_widget.setdata(xvalues, yvalues, title, datapoints)
        self.gr_widget.update()
        if now:
            self.gr_widget.draw(wsviewport=wsviewport)

    def export_image(self):
        extensions = (".pdf", ".png", ".bmp", ".jpg", ".jpeg", ".png",
                      ".tiff", ".fig", ".svg", ".wmf", ".eps", ".ps")
        qtext = "*" + " *".join(extensions)
        filepath = QtGui.QFileDialog.getSaveFileName(self, "Save Image",
                                                     ".", "Image Files ({})".format(qtext))
        if len(filepath) == 0:
            return

        if filepath.endswith('.eps') or filepath.endswith('.ps'):
            gr.beginprintext(filepath, 'Color', 'A4', 'Landscape')
            self.draw(now=True, wsviewport=(0, 0.297*0.9, 0, 0.21*0.95))
        else:
            gr.beginprint(filepath)
            self.draw(now=True)
        gr.endprint()

    def export_data(self):
        qtext = " *.csv"
        filepath = QtGui.QFileDialog.getSaveFileName(self, "Save Data",
                                                     ".", "CSV Files ({})".format(qtext))
        if len(filepath) == 0:
            return
        self.draw()
        xvalues = self.gr_widget.xvalues
        yvalues = self.gr_widget.yvalues
        if xvalues is None or yvalues is None:
            return
        with open(filepath, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile)
            for x, y in zip(xvalues, yvalues):
                csvwriter.writerow([x, y])

    def refresh(self):
        results = self.control.results
        if results is not None:
            results = results[-1][-1]
            if self.results != results or self.rdf is None:
                self.results = results
                self.rdf = RDF(results)
                e = np.unique(results.atoms.elements).tolist()
                if results.domains is not None \
                        and len(results.domains.centers) > 0 \
                        and "cav" not in e:
                    e.append("cavity domain centers")
                self.elem1.clear()
                self.elem1.addItems(e)
                self.elem2.clear()
                self.elem2.addItems(e)
                self.gr_widget.setdata(None, None, None)
                self.gr_widget.draw()
            self.datasetlabel.setText(str(results))
        else:
            self.datasetlabel.setText("")
            self.elem1.clear()
            self.elem2.clear()

    def activate(self):
        self.refresh()

    def updatestatus(self):
        self.refresh()
