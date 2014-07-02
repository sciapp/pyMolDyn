# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui


class ImageVideoTabDock(QtGui.QDockWidget):
    '''
        DockWidget to the 'image/video'-tab
    '''

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self,"image/video", parent)
        self.setWidget(QtGui.QWidget())

        self.layout             = QtGui.QHBoxLayout()
        self.image_video_tab    = ImageVideoTab(self.widget())

        self.layout.addWidget(self.image_video_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

class ImageVideoTab(QtGui.QWidget):
    '''
        tab 'image/video' in the main widget
    '''

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.init_gui()

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()

        self.image_video_button = QtGui.QPushButton('image_video button', self)
        self.vbox.addWidget(self.image_video_button)

        self.setLayout(self.vbox)
