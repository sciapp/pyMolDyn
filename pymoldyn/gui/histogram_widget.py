import csv
import sys
from math import floor

import gr
import numpy as np
from PySide6 import QtCore, QtWidgets
from qtgr import GRWidget

from ..util.logger import Logger

logger = Logger("gui.histogram_widget")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class GrHistogramWidget(GRWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.xvalues = None
        self.yvalues = None
        self.title = None
        self.datapoints = None

    def setdata(self, xvalues, yvalues, widths, title):
        self.xvalues = xvalues
        self.yvalues = yvalues
        self.widths = widths
        self.title = title

    def draw(self, wsviewport=None):
        if self.xvalues is not None and self.widths is not None:
            maxidx = np.argmax(self.xvalues)
            rangex = (self.xvalues.min(), self.xvalues[maxidx] + self.widths[maxidx])
        else:
            rangex = (0.0, 100.0)
        if self.yvalues is not None:
            rangey = gr.adjustrange(0.0, self.yvalues.max())
        else:
            rangey = (0.0, 8.0)

        if wsviewport is None:
            gr.setwsviewport(0, self.mwidth, 0, self.mheight)
        else:
            gr.setwsviewport(*wsviewport)
        gr.setwswindow(0, self.sizex, 0, self.sizey)
        gr.setviewport(0.075 * self.sizex, 0.95 * self.sizex, 0.075 * self.sizey, 0.95 * self.sizey)
        gr.setwindow(rangex[0], rangex[1], rangey[0], rangey[1])
        gr.setcharheight(0.012)

        gr.setfillintstyle(1)
        gr.setfillcolorind(0)
        gr.fillrect(rangex[0], rangex[1], rangey[0], rangey[1])

        if self.xvalues is not None and self.yvalues is not None and self.widths is not None:
            gr.setfillintstyle(1)
            gr.setfillcolorind(2)
            for i in range(self.xvalues.size):
                gr.fillrect(
                    self.xvalues[i],
                    self.xvalues[i] + self.widths[i] * 0.8,
                    0.0,
                    self.yvalues[i],
                )
        else:
            gr.text(0.45 * self.sizex, 0.5 * self.sizey, "no data")

        gr.setlinecolorind(1)
        xtick = floor(0.02 * (rangex[1] - rangey[0]) * 100.0) / 100.0
        ytick = floor(0.04 * (rangey[1] - rangey[0]) * 50.0) / 50.0
        gr.axes(xtick, ytick, rangex[0], rangey[0], 10, 5, 0.0075)
        gr.axes(xtick, ytick, rangex[1], rangey[1], -10, -5, -0.0075)

        if self.title is not None:
            gr.text(0.8 * self.sizex, 0.9 * self.sizey, self.title)


class HistogramWidget(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        self.control = parent.control
        self.results = None

        self.init_gui()

    def init_gui(self):
        vbox = QtWidgets.QVBoxLayout()
        grid = QtWidgets.QGridLayout()
        self.gr_widget = GrHistogramWidget()

        self.datasetlabel = QtWidgets.QLabel("No data loaded.", self)
        self.datasetlabel.setAlignment(QtCore.Qt.AlignHCenter)

        selectbox = QtWidgets.QHBoxLayout()
        self.cavity_type_box = QtWidgets.QComboBox(self)
        self.cavity_type_box.setMinimumWidth(180)
        selectbox.addWidget(self.cavity_type_box)
        selectbuttongroup = QtWidgets.QButtonGroup(self)
        self.volumebutton = QtWidgets.QRadioButton("Cavity Volume", self)
        selectbox.addWidget(self.volumebutton)
        selectbuttongroup.addButton(self.volumebutton)
        self.areabutton = QtWidgets.QRadioButton("Surface Area", self)
        selectbox.addWidget(self.areabutton)
        selectbuttongroup.addButton(self.areabutton)
        self.volumebutton.setChecked(True)
        grid.addLayout(selectbox, 0, 0)

        self.weightbutton = QtWidgets.QCheckBox("Weighted Histogram", self)
        self.weightbutton.setChecked(True)
        grid.addWidget(self.weightbutton, 0, 1)

        binbox = QtWidgets.QHBoxLayout()
        binbox.addWidget(QtWidgets.QLabel("Number of Bins:", self), 0)
        self.nbins = QtWidgets.QLineEdit(self)
        self.nbins.setMinimumWidth(50)
        binbox.addWidget(self.nbins, 0, QtCore.Qt.AlignLeft)
        grid.addLayout(binbox, 0, 2)

        buttonbox = QtWidgets.QHBoxLayout()

        self.plotbutton = QtWidgets.QPushButton("Plot", self)
        buttonbox.addWidget(self.plotbutton)
        self.plotbutton.clicked.connect(self.draw)

        self.export_image_button = QtWidgets.QPushButton("Save Image", self)
        buttonbox.addWidget(self.export_image_button)
        self.export_image_button.clicked.connect(self.export_image)

        self.export_data_button = QtWidgets.QPushButton("Export Data", self)
        buttonbox.addWidget(self.export_data_button)
        self.export_data_button.clicked.connect(self.export_data)
        grid.addLayout(buttonbox, 1, 0, 1, 3)

        vbox.addWidget(self.gr_widget, stretch=1)
        vbox.addWidget(self.datasetlabel, stretch=0)
        vbox.addLayout(grid)
        self.setLayout(vbox)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.update()

    def draw(self, now=False, wsviewport=None):
        xvalues = None
        yvalues = None
        widths = None
        title = None
        if self.results is None:
            self.refresh()
        if self.cavity_type_box.currentText():
            if self.cavity_type_box.currentText() == "Surface-based Cavities":
                cavities = self.results.surface_cavities
            elif self.cavity_type_box.currentText() == "Center-based Cavities":
                cavities = self.results.center_cavities
            elif self.cavity_type_box.currentText() == "Cavity Domains":
                cavities = self.results.domains
            nbins = str(self.nbins.text())
            if len(nbins) > 0 and int(nbins) > 0:
                nbins = int(nbins)
            else:
                nbins = 50
            if self.volumebutton.isChecked():
                data = cavities.volumes
            else:
                data = cavities.surface_areas
            if len(data) > 0:
                if self.weightbutton.isChecked():
                    hist, bin_edges = np.histogram(data, bins=nbins, weights=data)
                else:
                    hist, bin_edges = np.histogram(data, bins=nbins)
                widths = bin_edges[1:] - bin_edges[:-1]
                xvalues = bin_edges[:-1]
                yvalues = hist

        self.gr_widget.setdata(xvalues, yvalues, widths, title)
        self.gr_widget.update()
        if now:
            self.gr_widget.draw(wsviewport=wsviewport)

    def export_image(self):
        extensions = (
            ".pdf",
            ".png",
            ".bmp",
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".fig",
            ".svg",
            ".wmf",
            ".eps",
            ".ps",
        )
        qtext = "*" + " *".join(extensions)
        filepath = QtWidgets.QFileDialog.getSaveFileName(self, "Save Image", ".", "Image Files ({})".format(qtext))[0]
        if not filepath:
            return

        if filepath.endswith(".eps") or filepath.endswith(".ps"):
            gr.beginprintext(filepath, "Color", "A4", "Landscape")
            self.draw(now=True, wsviewport=(0, 0.297 * 0.9, 0, 0.21 * 0.95))
        else:
            gr.beginprint(filepath)
            self.draw(now=True)
        gr.endprint()

    def export_data(self):
        qtext = " *.csv"
        filepath = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data", ".", "CSV Files ({})".format(qtext))[0]
        if len(filepath) == 0:
            return
        self.update()
        xvalues = self.gr_widget.xvalues
        yvalues = self.gr_widget.yvalues
        if xvalues is None or yvalues is None:
            return
        with open(filepath, "w") as csvfile:
            csvwriter = csv.writer(csvfile)
            for x, y in zip(xvalues, yvalues):
                csvwriter.writerow([x, y])

    def refresh(self):
        self.cavity_type_box.clear()
        results = self.control.results
        if results is not None:
            results = results[-1][-1]
            if results.surface_cavities is not None:
                self.cavity_type_box.addItem("Surface-based Cavities")
            if results.center_cavities is not None:
                self.cavity_type_box.addItem("Center-based Cavities")
            if results.domains is not None:
                self.cavity_type_box.addItem("Cavity Domains")
            if self.results != results:
                self.results = results
                self.gr_widget.setdata(None, None, None, None)
                self.gr_widget.update()
            self.datasetlabel.setText(str(results))
        else:
            self.datasetlabel.setText("")

    def activate(self):
        self.refresh()

    def updatestatus(self):
        self.refresh()
