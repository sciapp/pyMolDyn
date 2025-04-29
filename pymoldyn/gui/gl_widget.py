import numpy as np
from PySide6 import QtCore, QtWidgets

try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget as QGLWidget

    has_qopenglwidget = True
except ImportError:
    from PySide6 import QtOpenGL
    from PySide6.QtOpenGLWidgets import QOpenGLWidget as QGLWidget

    has_qopenglwidget = False
from OpenGL.GL import (
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    glBindFramebuffer,
    glClear,
    glEnable,
    glReadPixels,
)

from ..config.configuration import config


class UpdateGLEvent(QtCore.QEvent):
    def __init__(self):
        t = QtCore.QEvent.registerEventType()
        super().__init__(QtCore.QEvent.Type(t))


class GLWidget(QGLWidget if has_qopenglwidget else QGLWidget):
    """
    OpenGL widget to show the 3D-scene
    """

    def __init__(self, parent, main_window):
        if has_qopenglwidget:
            super().__init__(parent)
        else:
            super().__init__(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.update_needed = False
        self.dataset_loaded = False
        self.control = parent.control
        self.main_window = main_window
        self.setDisabled(True)
        self.vis.repaint_callback = self.update

    @property
    def vis(self):
        return self.control.visualization

    def initializeGL(self):
        self.vis.assign_opengl_context(self)
        glEnable(GL_DEPTH_TEST)

    def minimumSizeHint(self):
        return QtCore.QSize(400, 400)

    def sizeHint(self):
        return QtCore.QSize(config.OpenGL.gl_window_size[0], config.OpenGL.gl_window_size[1])

    def mouseMoveEvent(self, e):
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
        self.update_needed = True
        rot_v = 0.1
        if e.modifiers() == QtCore.Qt.ShiftModifier:
            if (e.angleDelta().x() != 0) or (e.angleDelta().y() != 0):
                self.vis.rotate_mouse(-e.angleDelta().x() * rot_v, -e.angleDelta().y() * rot_v)
        else:
            if e.angleDelta().y() != 0:
                self.vis.zoom(-e.angleDelta().y())

        QtWidgets.QApplication.postEvent(self, UpdateGLEvent())

    def mousePressEvent(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            self.x = e.x()
            self.y = e.y()

    def mouseDoubleClickEvent(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            x = e.x()
            y = self.height() - e.y()
            glBindFramebuffer(GL_FRAMEBUFFER, 1)  # Bind to correct framebuffer for depth check
            z = glReadPixels(x, y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
            obj = self.vis.get_object_at_2dposition(x, y)
            if obj is None:
                x /= 1.0 * self.width()
                y /= 1.0 * self.height()
                x = x * 2 - 1
                y = y * 2 - 1
                z = z[0][0]
                z = 2 * z - 1
                z = self.vis.proj_mat[2, 3] / (-z - self.vis.proj_mat[2, 2])
                x = -x * z / self.vis.proj_mat[0, 0]
                y = -y * z / self.vis.proj_mat[1, 1]
                z += self.vis.d
                x, y, z, w = np.dot(self.vis.mat, np.array((x, y, z, 1)))
                obj = self.vis.get_object_at_3dposition(x, y, z)
            if obj is not None:
                object_type, object_index = obj
                if object_type == "atom":
                    self.window().statistics_dock.statistics_tab.html_view.show_atom(object_index)
                elif object_type == "domain":
                    self.window().statistics_dock.statistics_tab.html_view.show_domain(object_index)
                elif object_type == "surface cavity":
                    self.window().statistics_dock.statistics_tab.html_view.show_surface_cavity(object_index)
                elif object_type == "center cavity":
                    self.window().statistics_dock.statistics_tab.html_view.show_center_cavity(object_index)
                self.window().statistics_dock.raise_()
            self.updateGL()

    def customEvent(self, e):
        if self.update_needed:
            self.setDisabled(False)
            self.updateGL()
            self.update_needed = False

    #     def create_scene(self, show_box, show_atoms, show_domains, show_cavities=True, center_based_cavities=False):
    def create_scene(self):
        self.vis.create_scene()
        self.updateGL()

    def keyPressEvent(self, e):
        """
        Catches and processes key presses
        """
        rot_v_key = 15
        if e.key() == QtCore.Qt.Key_Right:
            self.vis.rotate_mouse(rot_v_key, 0)
        elif e.key() == QtCore.Qt.Key_Left:
            self.vis.rotate_mouse(-rot_v_key, 0)
        elif e.key() == QtCore.Qt.Key_Up:
            self.vis.rotate_mouse(0, -rot_v_key)
        elif e.key() == QtCore.Qt.Key_Down:
            self.vis.rotate_mouse(0, rot_v_key)
        elif e.key() == QtCore.Qt.Key_D:  # Domains
            self.vis.settings.show_domains = True
            self.vis.settings.show_surface_cavities = False
            self.vis.settings.show_center_cavities = False
            self.main_window.view_dock.view_tab.domain_check.setChecked(True)
            # self.vis.create_scene()
        elif e.key() == QtCore.Qt.Key_S:  # Cavities
            self.vis.settings.show_domains = False
            self.vis.settings.show_surface_cavities = True
            self.vis.settings.show_center_cavities = False
            self.main_window.view_dock.view_tab.surface_cavity_check.setChecked(True)
            # self.vis.create_scene()
        elif e.key() == QtCore.Qt.Key_C:  # center based cavities
            self.vis.settings.show_domains = False
            self.vis.settings.show_surface_cavities = False
            self.vis.settings.show_center_cavities = True
            self.main_window.view_dock.view_tab.center_cavity_check.setChecked(True)
            # self.vis.create_scene()
        if e.key() == QtCore.Qt.Key_R:
            self.vis.reset_view()
        else:
            e.ignore()
        self.updateGL()

    def paintGL(self):
        """
        Refresh scene
        """
        glClear(GL_DEPTH_BUFFER_BIT)
        self.vis.paint(self.width(), self.height(), has_qopenglwidget, self.devicePixelRatio())

    def updateGL(self):
        if has_qopenglwidget:
            self.update()
        else:
            super(GLWidget, self).updateGL()

    def activate(self):
        pass

    def updatestatus(self):
        self.update_needed = True
