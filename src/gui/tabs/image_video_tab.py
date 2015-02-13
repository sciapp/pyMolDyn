# -*- coding: utf-8 -*-

from PySide import QtGui
from gui.gl_widget import GLWidget


class ImageVideoTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'image/video'-tab
    """

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "image/video", parent)
        self.setWidget(QtGui.QWidget())

        self.layout             = QtGui.QHBoxLayout()
        self.image_video_tab    = ImageVideoTab(self.widget())

        self.layout.addWidget(self.image_video_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)


class ImageVideoTab(QtGui.QWidget):
    """
        tab 'image/video' in the main widget
    """

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.init_gui()

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()

        screenshot_button = QtGui.QPushButton('Save screenshot', self)
        screenshot_button.clicked.connect(self.save_screenshot)
        self.vbox.addWidget(screenshot_button)

        self.setLayout(self.vbox)

    def save_screenshot(self):
        file_name, okay = QtGui.QFileDialog.getSaveFileName(self,
            'Save screenshot...', filter='Portable Network Graphics (*.png)')
        if okay and file_name:
            for widget in QtGui.QApplication.topLevelWidgets():
                for gl_widget in widget.findChildren(GLWidget):
                    gl_widget.vis.save_screenshot(file_name)
