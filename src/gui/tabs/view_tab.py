# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui


class ViewTabDock(QtGui.QDockWidget):
    '''
        DockWidget to the 'view'-tab
    '''

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "view", parent)
        self.setWidget(QtGui.QWidget())

        self.layout     = QtGui.QHBoxLayout()
        self.view_tab   = ViewTab(self.widget())

        self.layout.addWidget(self.view_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

class ViewTab(QtGui.QWidget):
    '''
        tab 'view' in the main widget
    '''

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.init_gui()

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()

        self.view_button = QtGui.QPushButton('view button', self)
        self.vbox.addWidget(self.view_button)

        self.setLayout(self.vbox)
