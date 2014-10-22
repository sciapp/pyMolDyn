# -*- coding: utf-8 -*-
import numpy as np
import numpy.linalg as la
from PySide import QtCore, QtGui, QtOpenGL
import visualization
from config.configuration import config
from OpenGL.GL import glReadPixels, GL_FLOAT, GL_DEPTH_COMPONENT
from util.gl_util import create_perspective_projection_matrix, create_look_at_matrix


class UpdateGLEvent(QtCore.QEvent):

    def __init__(self):
        t = QtCore.QEvent.registerEventType()
        QtCore.QEvent.__init__(self, QtCore.QEvent.Type(t))


class GLWidget(QtOpenGL.QGLWidget):
    """
        OpenGL widget to show the 3D-scene
    """

    def __init__(self, parent=None):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.update_needed = False
        self.dataset_loaded = False

    def initializeGL(self):
        pass

    def minimumSizeHint(self):
        return QtCore.QSize(config.OpenGL.gl_window_size[0], config.OpenGL.gl_window_size[1])

    def sizeHint(self):
        return QtCore.QSize(config.OpenGL.gl_window_size[0], config.OpenGL.gl_window_size[1])

    def show_dataset(self, volume, filename, frame_nr, resolution):
        """
            shows calculation {calculation_nr} of frame {frame_nr} in file {filename}
        """
        self.vis = visualization.Visualization(volume, filename, frame_nr, resolution)
        self.dataset_loaded = True
        self.updateGL()

    def mouseMoveEvent(self, e):
        if self.dataset_loaded:
            dx = e.x() - self.x
            dy = e.y() - self.y
            if e.buttons() & QtCore.Qt.LeftButton:
                if e.modifiers() == QtCore.Qt.AltModifier:
                    self.vis.translate_mouse(dx, dy)
                else:
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
                    self.vis.rotate_mouse(0, e.delta() * rot_v)

            QtGui.QApplication.postEvent(self, UpdateGLEvent())

    def mousePressEvent(self, e):
        if self.dataset_loaded:
            if e.buttons() and QtCore.Qt.LeftButton:
                self.x = e.x()
                self.y = e.y()

    def mouseDoubleClickEvent(self, e):
        if self.dataset_loaded:
            if e.buttons() and QtCore.Qt.LeftButton:
                x = e.x()
                y = self.height() - e.y()
                z = glReadPixels(x, y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
                x /= 1.0*self.width()
                y /= 1.0*self.height()
                x = x * 2 - 1
                y = y * 2 - 1
                z = z[0][0]
                z = 2 * z - 1
                z = self.vis.proj_mat[2, 3] / (-z - self.vis.proj_mat[2, 2])
                x = -x*z/self.vis.proj_mat[0, 0]
                y = -y*z/self.vis.proj_mat[1, 1]
                x, y, z, w  = np.dot(la.inv(self.vis.lookat_mat), np.array((x, y, z, 1)))
                print(x, y, z, w)


    def customEvent(self, e):
        if self.update_needed:
            self.updateGL()
            self.update_needed = False

#     def create_scene(self, show_box, show_atoms, show_domains, show_cavities=True, center_based_cavities=False):
    def create_scene(self):
        if self.dataset_loaded:
            self.vis.create_scene()
            self.updateGL()

    def keyPressEvent(self, e):
        """
            catches and processes key presses
        """
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
                self.vis.settings.show_domains = True
                self.vis.settings.show_cavities = False
                self.vis.settings.show_alt_cavities = False
                self.vis.create_scene()
            elif e.key() == QtCore.Qt.Key_C:            # Cavities
                self.vis.settings.show_domains = False
                self.vis.settings.show_cavities = True
                self.vis.settings.show_alt_cavities = False
                self.vis.create_scene()
            elif e.key() == QtCore.Qt.Key_F:            # center based cavities
                self.vis.settings.show_domains = False
                self.vis.settings.show_cavities = False
                self.vis.settings.show_alt_cavities = True
                self.vis.create_scene()
            else:
                e.ignore()
            self.updateGL()

    def paintGL(self):
        """
            refresh scene
        """
        if self.dataset_loaded:
            self.vis.paint(self.geometry().width(), self.geometry().height())
        else:
            import gr3
            gr3.setbackgroundcolor(config.Colors.background[0], config.Colors.background[1], config.Colors.background[2], 1.0)
            gr3.drawimage(0, config.OpenGL.gl_window_size[0], 0, config.OpenGL.gl_window_size[1], config.OpenGL.gl_window_size[0], config.OpenGL.gl_window_size[1], gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)

