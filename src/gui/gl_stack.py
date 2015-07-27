# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from gui.gl_widget import GLWidget
from gui.rdf_widget import RDFWidget
from gui.histogram_widget import HistogramWidget


class GLStack(QtGui.QStackedWidget):
    def __init__(self, parent, main_window):
        QtGui.QStackedWidget.__init__(self, parent)
        self.parent = parent
        self.control = parent.control
        self.gl_widget = GLWidget(self, main_window)
        self.rdf_widget = RDFWidget(self)
        self.histogram_widget = HistogramWidget(self)

        self.addWidget(self.gl_widget)
        self.addWidget(self.rdf_widget)
        self.addWidget(self.histogram_widget)

        self.show()
