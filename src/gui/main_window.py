# -*- coding: utf-8 -*-

import visualization
import calculation
from gui.file_tab import FileTabDock
from gui.view_tab import ViewTabDock
from gui.image_video_tab import ImageVideoTabDock
from gui.gl_widget import GLWidget
import gr3
from PySide import QtCore, QtGui, QtOpenGL
import numpy
import math


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        
        self.center             = CentralWidget(self)
        self.file_dock          = FileTabDock(self)
        self.view_dock          = ViewTabDock(self)
        self.image_video_dock   = ImageVideoTabDock(self)

        self.docks = []
        
        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtGui.QTabWidget.North)
        
        for dock in (self.file_dock, self.view_dock, self.image_video_dock):
            self.docks.append(dock)

        self.setCentralWidget(self.center)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.file_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.view_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.image_video_dock, QtCore.Qt.Vertical)

        for dock in self.docks[1:]:
            self.tabifyDockWidget(self.file_dock, dock)

        self.show()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_M:
            if not self.isFullScreen():
                for dock in self.docks:
                    dock.hide()
                self.showFullScreen()
            else:
                for dock in self.docks:
                    dock.show()
                self.showNormal()
 
    def show_dataset(self, volume, filename, frame_nr, resolution, use_surface_points):
        self.statusBar().showMessage(filename)
        
        if visualization.calculated(filename, frame_nr, resolution, use_surface_points):
            self.center.show_dataset(volume, filename, frame_nr, resolution, use_surface_points)

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

    def show_dataset(self, volume, filename, frame_nr, resolution, use_surface_points):
        self.gl_widget.show_dataset(volume, filename, frame_nr, resolution, use_surface_points)

