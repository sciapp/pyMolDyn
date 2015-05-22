# -*- coding: utf-8 -*-

from PySide import QtGui
from gui.gl_widget import GLWidget
from core import file
import gr3
import os.path


class ImageVideoTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'image/video'-tab
    """

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "image/video", parent)
        self.setWidget(QtGui.QWidget())

        self.layout             = QtGui.QHBoxLayout()
        self.image_video_tab    = ImageVideoTab(self.widget(), parent)

        self.layout.addWidget(self.image_video_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)


class ImageVideoTab(QtGui.QWidget):
    """
        tab 'image/video' in the main widget
    """

    def __init__(self, parent, main_window):
        QtGui.QWidget.__init__(self, parent)
        self.main_window = main_window
        self.init_gui()

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()

        screenshot_button = QtGui.QPushButton('Save screenshot for this frame', self)
        screenshot_button.clicked.connect(self.save_screenshot)
        self.vbox.addWidget(screenshot_button)
        mass_screenshot_button = QtGui.QPushButton('Save screenshot for all selected frames', self)
        mass_screenshot_button.clicked.connect(self.save_screenshot_for_all_selected_frames)
        self.vbox.addWidget(mass_screenshot_button)

        self.setLayout(self.vbox)

    def save_screenshot(self):
        file_name, okay = QtGui.QFileDialog.getSaveFileName(self,
            'Save screenshot...', filter='Portable Network Graphics (*.png)')
        if okay and file_name:
            for widget in QtGui.QApplication.topLevelWidgets():
                for gl_widget in widget.findChildren(GLWidget):
                    gl_widget.vis.save_screenshot(file_name)

    def save_screenshot_for_all_selected_frames(self):
        file_list = self.main_window.file_dock.file_tab.file_list

        frames_to_write = []
        selection = file_list.get_selection()
        for file_name, frame_numbers in selection.items():
            if frame_numbers == [-1]:
                frame_numbers = range(file.File.open(file_name).info.num_frames)
            for frame_number in frame_numbers:
                frames_to_write.append((file_name, frame_number))
        print frames_to_write
        control = self.main_window.control

        width, height = 1920, 1080
        for file_name, frame_number in frames_to_write:
            image_file_name = "{}.{:06d}.png".format(os.path.basename(file_name), frame_number)
            control.visualize(file_name, frame_number)
            control.visualization.create_scene()
            gr3.export(image_file_name, width, height)
