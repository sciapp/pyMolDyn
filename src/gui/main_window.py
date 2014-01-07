# -*- coding: utf-8 -*-

import visualization
from gui.main_tab_widget import TabWidgetDock
from gui.gl_widget import GLWidget
import gr3
from PySide import QtCore, QtGui, QtOpenGL
import numpy
import math


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        
        self.center     = CentralWidget(self)
        self.tab_dock   = TabWidgetDock(self)

        self.setCentralWidget(self.center)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.tab_dock, QtCore.Qt.Vertical)
        
        self.show()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_M:
            if not self.isFullScreen():
                self.tab_dock.hide()
                self.showFullScreen()
            else:
                self.tab_dock.show()
                self.showNormal()

    
    def show_dataset(self, volume, filename, frame_nr):
        self.center.show_dataset(volume, filename, frame_nr)
#    def closeEvent(self, event):
#        reply = QtGui.QMessageBox.question(self, 'Message',
#            "Are you sure to quit?", QtGui.QMessageBox.Yes | 
#            QtGui.QMessageBox.No, QtGui.QMessageBox.No)
#        if reply == QtGui.QMessageBox.Yes:
#            event.accept()
#        else:
#            event.ignore() 

class CentralWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('pyMolDyn 2')
        self.init_gui()
 
    def init_gui(self):
        self.gl_widget  = GLWidget(self)

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.gl_widget)
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(mainLayout)

    def show_dataset(self, volume, filename, frame_nr):
        self.gl_widget.show_dataset(volume, filename, frame_nr)

