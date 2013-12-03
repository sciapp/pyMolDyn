import visualization
import gr3
from PySide import QtCore, QtGui, QtOpenGL
import numpy
import math

display_size = 1000

class Window(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
#        self.setWindowTitle(self.tr(repr(visualization.get_volume())))
        self.init_gui()
 
    def init_gui(self):
        self.gl = GLWidget(self)
        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.gl)
        self.setLayout(mainLayout)

#TODO: Unschoen
    def show_dataset(self, volume, filename, frame_nr):
        self.gl.show_dataset(volume, filename, frame_nr)

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