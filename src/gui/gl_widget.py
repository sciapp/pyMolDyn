# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui, QtOpenGL
from visualization import visualization

display_size = 800

class UpdateGLEvent(QtCore.QEvent):

    def __init__(self):
        t = QtCore.QEvent.registerEventType()
        QtCore.QEvent.__init__(self, QtCore.QEvent.Type(t))

class GLWidget(QtOpenGL.QGLWidget):
    '''
        OpenGL widget to show the 3d-scene
    '''

    def __init__(self, parent=None):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.update_needed = False
        self.dataset_loaded = False

    def initializeGL(self):
        pass

    def minimumSizeHint(self):
        return QtCore.QSize(display_size, display_size)

    def sizeHint(self):
        return QtCore.QSize(display_size, display_size)

    def show_dataset(self, volume, filename, frame_nr, resolution, use_center_points):
        '''
            shows calculation {calculation_nr} of frame {frame_nr} in file {filename}
        '''
        self.vis = visualization.Visualization(volume, filename, frame_nr, resolution, use_center_points)
        self.dataset_loaded = True
        self.updateGL()

    def mouseMoveEvent(self, e):
        if self.dataset_loaded:
            if e.buttons() & QtCore.Qt.LeftButton:
                dx = e.x() - self.x
                dy = e.y() - self.y
                self.vis.rotate_mouse(dx, dy)
                self.x = e.x()
                self.y = e.y()
                self.updateGL()

    def wheelEvent(self, e):
        if self.dataset_loaded:
            self.update_needed = True
            if e.modifiers() != QtCore.Qt.ShiftModifier:
                if e.orientation() == QtCore.Qt.Orientation.Vertical:
                    self.vis.zoom(e.delta())
            else:
                rot_v = 0.1
                if e.orientation() == QtCore.Qt.Orientation.Horizontal:
                    self.vis.rotate_mouse(e.delta() * rot_v, 0)
                else:
                    self.vis.rotate_mouse(0, e.delta() * rot_v )

            QtGui.QApplication.postEvent(self, UpdateGLEvent())

    def mousePressEvent(self, e):
        if self.dataset_loaded:
            if e.buttons() and QtCore.Qt.LeftButton:
                self.x = e.x()
                self.y = e.y()

    def customEvent(self, e):
        if self.update_needed:
            self.updateGL()
            self.update_needed = False

    def keyPressEvent(self, e):
        '''
            catches and processes key presses
        '''
        if self.dataset_loaded:
            rot_v_key = 15
            if e.key() == QtCore.Qt.Key_Right:
                self.vis.rotate_mouse(rot_v_key, 0)
            elif e.key() == QtCore.Qt.Key_Left:
                self.vis.rotate_mouse(-rot_v_key, 0)
            elif e.key() == QtCore.Qt.Key_Up:
                self.vis.rotate_mouse(0, -rot_v_key)
            elif e.key() == QtCore.Qt.Key_Down:
                self.vis.rotate_mouse(0, rot_v_key)
            elif e.key() == QtCore.Qt.Key_D:            # Domains
                self.vis.create_scene(False)
            elif e.key() == QtCore.Qt.Key_C:            # Cavities
                self.vis.create_scene(True)
            elif e.key() == QtCore.Qt.Key_F:            # center based cavities
                self.vis.create_scene(True,True)
            else:
                e.ignore()
            self.updateGL()
        
    def paintGL(self):
        '''
            refresh scene
        '''
        if self.dataset_loaded:
            self.vis.paint(self.geometry().width(), self.geometry().height())
        else:
            import gr3
            gr3.setbackgroundcolor(0.0, 0.0, 0.0, 1.0)
            gr3.drawimage(0, display_size, 0, display_size, display_size, display_size, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)
            
