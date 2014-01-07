# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui, QtOpenGL
import visualization

display_size = 800

class UpdateGLEvent(QtCore.QEvent):

    def __init__(self):
        type = QtCore.QEvent.registerEventType()
        QtCore.QEvent.__init__(self, QtCore.QEvent.Type(type))

class GLWidget(QtOpenGL.QGLWidget):

    def __init__(self, parent=None):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.dataset_loaded = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.bla = False

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
        self.update_needed = True
        if e.modifiers() != QtCore.Qt.ShiftModifier:
            if e.orientation() == QtCore.Qt.Orientation.Vertical:
                self.vis.zoom(e.delta())
        else:
            rot_v = 0.1
            if e.orientation() == QtCore.Qt.Orientation.Horizontal:
                self.vis.rotate_mouse(e.delta()*rot_v, 0)
            else:
                self.vis.rotate_mouse(0, e.delta()*rot_v )

        QtGui.QApplication.postEvent(self, UpdateGLEvent())

    def mousePressEvent(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            self.x = e.x()
            self.y = e.y()

    def customEvent(self, e):
        if self.update_needed:
            self.updateGL()
            self.update_needed = False

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
        else:
            e.ignore()
        self.updateGL()
        
    def paintGL(self):
        if self.dataset_loaded:
            self.vis.paint(self.geometry().width(), self.geometry().height())

