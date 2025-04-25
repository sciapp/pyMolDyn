import csv
import sys

import gr
import numpy as np
from PySide6 import QtCore, QtWidgets
from qtgr import GRWidget

from ..statistics.pdf import PDF, Kernels
from ..util.logger import Logger

logger = Logger("gui.pdf_widget")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class GrPlotWidget(GRWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.xvalues = None
        self.yvalues = None
        self.title = None
        self.datapoints = None

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
        gr.setviewport(0.075 * self.sizex, 0.95 * self.sizex, 0.075 * self.sizey, 0.95 * self.sizey)
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


class PDFWidget(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        self.control = parent.control
        self.results = None
        self.pdf = None

        self.init_gui()

    def init_gui(self):
        vbox = QtWidgets.QVBoxLayout()
        grid = QtWidgets.QGridLayout()
        self.gr_widget = GrPlotWidget()

        self.datasetlabel = QtWidgets.QLabel("No data loaded.", self)
        self.datasetlabel.setAlignment(QtCore.Qt.AlignHCenter)

        elembox = QtWidgets.QHBoxLayout()
        elembox.addWidget(QtWidgets.QLabel("Elements:", self), 0)
        self.elem1 = QtWidgets.QComboBox(self)
        self.elem1.setMinimumWidth(170)
        elembox.addWidget(self.elem1, 1)
        self.elem2 = QtWidgets.QComboBox(self)
        self.elem2.setMinimumWidth(170)
        elembox.addWidget(self.elem2, 1)
        grid.addLayout(elembox, 0, 0)

        rangebox = QtWidgets.QHBoxLayout()
        rangebox.addWidget(QtWidgets.QLabel("Plot range:", self))
        self.range1 = QtWidgets.QLineEdit("0", self)
        self.range1.setMinimumWidth(30)
        rangebox.addWidget(self.range1)
        rangebox.addWidget(QtWidgets.QLabel("-", self))
        self.range2 = QtWidgets.QLineEdit("8", self)
        self.range2.setMinimumWidth(30)
        rangebox.addWidget(self.range2)
        grid.addLayout(rangebox, 1, 0)

        cutoffbox = QtWidgets.QHBoxLayout()
        cutoffbox.addWidget(QtWidgets.QLabel("Kernel:", self))
        self.kernels = {
            "Gaussian": Kernels.gauss,
            "Epanechnikov": Kernels.epanechnikov,
            "Compact": Kernels.compact,
            "Triangular": Kernels.triang,
            "Box": Kernels.quad,
            "Right Box": Kernels.posquad,
            "Left Box": Kernels.negquad,
        }
        self.kernel = QtWidgets.QComboBox(self)
        self.kernel.setMinimumWidth(130)
        self.kernel.addItems(
            [
                "Gaussian",
                "Epanechnikov",
                "Compact",
                "Triangular",
                "Box",
                "Right Box",
                "Left Box",
            ]
        )
        cutoffbox.addWidget(self.kernel)
        cutoffbox.addWidget(QtWidgets.QLabel("Cutoff:", self))
        self.cutoff = QtWidgets.QLineEdit("12", self)
        self.cutoff.setMinimumWidth(30)
        cutoffbox.addWidget(self.cutoff)
        cutoffbox.addWidget(QtWidgets.QLabel("Bandwidth:", self))
        self.bandwidth = QtWidgets.QLineEdit("", self)
        self.bandwidth.setMinimumWidth(30)
        cutoffbox.addWidget(self.bandwidth)
        grid.addLayout(cutoffbox, 2, 0)

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
        grid.addLayout(buttonbox, 3, 0)

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
        title = None
        datapoints = None
        if self.pdf is None:
            self.refresh()
        if self.pdf is not None:
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
            try:
                bandwidth = float(str(self.bandwidth.text()))
                if bandwidth < 0:
                    bandwidth = 0
                    self.bandwidth.setText("0")
            except ValueError:
                bandwidth = None
                self.bandwidth.setText("")
            kernel = self.kernels.get(self.kernel.currentText(), None)
            f = self.pdf.pdf(elem1, elem2, cutoff=cutoff, h=bandwidth, kernel=kernel)
            if f is not None:
                if callable(f):
                    xvalues = np.linspace(range1, range2, 400)
                    yvalues = f(xvalues)
                    title = "{} - {}".format(elem1, elem2)
                    datapoints = f.f.x
                else:
                    peaks = f[np.logical_and(range1 < f, f < range2)]
                    if len(peaks) > 2:
                        xvalues = np.zeros(len(peaks) * 3)
                        xvalues[0::3] = peaks
                        xvalues[1::3] = peaks
                        xvalues[2::3] = peaks
                        yvalues = np.zeros(len(peaks) * 3)
                        yvalues[1::3] = 1
                        datapoints = peaks

        self.gr_widget.setdata(xvalues, yvalues, title, datapoints)
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
        if len(filepath) == 0:
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
        results = self.control.results
        if results is not None:
            results = results[-1][-1]
            if self.results != results or self.pdf is None:
                self.results = results
                self.pdf = PDF(results)
                e = np.unique(results.atoms.elements).tolist()
                for i in range(len(e)):
                    e[i] = e[i].decode("utf-8")
                if results.domains is not None and len(results.domains.centers) > 0 and "cav" not in e:
                    e.append("cavity domain centers")
                self.elem1.clear()
                self.elem1.addItems(e)
                self.elem2.clear()
                self.elem2.addItems(e)
                self.gr_widget.setdata(None, None, None)
                self.gr_widget.update()
            self.datasetlabel.setText(str(results))
        else:
            self.datasetlabel.setText("")
            self.elem1.clear()
            self.elem2.clear()

    def activate(self):
        self.refresh()

    def updatestatus(self):
        self.refresh()
