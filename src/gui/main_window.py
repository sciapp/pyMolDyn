import visualization
from main_tab_widget import TabWidget
import gr3
from PySide import QtCore, QtGui, QtOpenGL
import numpy
import math

display_size = 800

class Window(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('pyMolDyn 2')
        self.init_gui()
#        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
#        self.showFullScreen()
 
    def init_gui(self):
        self.gl_widget  = GLWidget(self)
        self.tab_widget = TabWidget(self)

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.gl_widget)
        mainLayout.addWidget(self.tab_widget)
        
        self.setLayout(mainLayout)
        self.show()

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

class GLWidget(QtOpenGL.QGLWidget):

    def __init__(self, parent=None):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.dataset_loaded = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def minimumSizeHint(self):
        return QtCore.QSize(display_size, display_size)

    def sizeHint(self):
        return QtCore.QSize(display_size, display_size)

    def show_dataset(self, volume, filename, frame_nr):
        self.dataset_loaded = True
        self.vis = visualization.Visualization(volume, filename, frame_nr)
        self.updateGL()

    def mouseMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
           dx = e.x() - self.x
           dy = e.y() - self.y
           self.vis.rotate_mouse(dx, dy)
           self.x = e.x()
           self.y = e.y()
           self.updateGL()

    def wheelEvent(self, e):
        self.vis.zoom(e.delta())
        self.updateGL()

    def mousePressEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self.x = e.x()
            self.y = e.y()

    def keyPressEvent(self,e):
        self.vis.process_key(e)
    
        if e.key() == QtCore.Qt.Key_Right:
            self.vis.process_key('right')
        elif e.key() == QtCore.Qt.Key_Left:
            self.vis.process_key('left')
        elif e.key() == QtCore.Qt.Key_Up:
            self.vis.process_key('up')
        elif e.key() == QtCore.Qt.Key_Down:
            self.vis.process_key('down')
        elif e.key() == QtCore.Qt.Key_D:
            self.vis.process_key('d')
        elif e.key() == QtCore.Qt.Key_C:
            self.vis.process_key('c')
        elif e.key() == QtCore.Qt.Key_F:
            self.vis.process_key('f')
        self.updateGL()
        
    def paintGL(self):
        self.vis.paint(display_size)

    def paintGL(self):
        if self.dataset_loaded:
            self.vis.paint(display_size)
