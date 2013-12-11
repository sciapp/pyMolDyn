import visualization
from gui.main_tab_widget import TabWidget
from gui.gl_widget import GLWidget
import gr3
from PySide import QtCore, QtGui, QtOpenGL
import numpy
import math


class Window(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('pyMolDyn 2')
        self.init_gui()
 
    def init_gui(self):
        self.gl_widget  = GLWidget(self)
        self.tab_widget = TabWidget(self)

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.gl_widget)
        mainLayout.addWidget(self.tab_widget)
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(mainLayout)
        self.show()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_M:
            if not self.isFullScreen():
                self.tab_widget.hide()
                self.showFullScreen()
            else:
                self.tab_widget.show()
                self.showNormal()

#    def closeEvent(self, event):
#        reply = QtGui.QMessageBox.question(self, 'Message',
#            "Are you sure to quit?", QtGui.QMessageBox.Yes | 
#            QtGui.QMessageBox.No, QtGui.QMessageBox.No)
#        if reply == QtGui.QMessageBox.Yes:
#            event.accept()
#        else:
#            event.ignore() 

    def show_dataset(self, volume, filename, frame_nr):
        self.gl_widget.show_dataset(volume, filename, frame_nr)

