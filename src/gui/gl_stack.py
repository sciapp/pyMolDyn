# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from gui.gl_widget import GLWidget
from gui.pdf_widget import PDFWidget
from gui.histogram_widget import HistogramWidget


class GLStack(QtGui.QStackedWidget):
    def __init__(self, parent, main_window):
        QtGui.QStackedWidget.__init__(self, parent)
        self.parent = parent
        self.control = parent.control
        self.gl_widget = GLWidget(self, main_window)
        self.pdf_widget = PDFWidget(self)
        self.histogram_widget = HistogramWidget(self)

        self.addWidget(self.gl_widget)
        self.addWidget(self.pdf_widget)
        self.addWidget(self.histogram_widget)

        self.show()

    def activate(self, index):
        self.setCurrentIndex(index)
        self.widget(index).activate()

    def updatestatus(self):
        for index in range(self.count()):
            widget = self.widget(index)
            widget.updatestatus()