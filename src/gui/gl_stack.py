# -*- coding: utf-8 -*-

from PySide import QtGui
from gui.gl_widget import GLWidget
from gui.rdf_widget import RDFWidget
from gui.histogram_widget import HistogramWidget


class GLStack(QtGui.QStackedWidget):
    def __init__(self, parent):
        QtGui.QStackedWidget.__init__(self, parent)
        self.parent = parent
        self.control = parent.control
        self.gl_widget = GLWidget(self)
        self.rdf_widget = RDFWidget(self)
        self.histogram_widget = HistogramWidget(self)

        self.addWidget(self.gl_widget)
        self.addWidget(self.rdf_widget)
        self.addWidget(self.histogram_widget)

        self.show()
