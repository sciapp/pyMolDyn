# -*- coding: utf-8 -*-
from PySide import QtGui
from gl_widget import GLWidget
from gr_widget import GRView


class GLStack(QtGui.QStackedWidget):

    def __init__(self, parent):
        QtGui.QStackedWidget.__init__(self, parent)
        self.parent = parent
        self.control = parent.control
        self.gl_widget = GLWidget(self)
        self.gr_view = GRView(self)

        self.addWidget(self.gl_widget)
        self.addWidget(self.gr_view)

        self.show()
