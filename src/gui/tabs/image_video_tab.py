# -*- coding: utf-8 -*-

from PySide import QtGui
from PySide.QtCore import QTimer
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
        selection = file_list.get_selection()
        if not selection:
            QtGui.QMessageBox.information(self, "No frame selected", "Please use the file tab to select at least one frame.", QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)
            return

        dir_name = QtGui.QFileDialog.getExistingDirectory(self, 'Save screenshots to folder...')

        frames_to_write = []
        for file_name, frame_numbers in selection.items():
            if frame_numbers == [-1]:
                num_frames = file.File.open(file_name).info.num_frames
                frame_numbers = range(num_frames)
            for frame_number in frame_numbers:
                frames_to_write.append((file_name, frame_number))
        print frames_to_write
        if dir_name:
            dialog = MassScreenshotDialog(self, frames_to_write, dir_name)
            dialog.show()
            return


class MassScreenshotDialog(QtGui.QDialog):
    def __init__(self, parent, frames_to_write, dir_name):
        super(MassScreenshotDialog, self).__init__(parent)
        self.control = parent.main_window.control
        self.setModal(True)
        self.frames_to_write = frames_to_write
        self.dir_name = dir_name
        self.vbox = QtGui.QVBoxLayout()
        self.progress_bar = QtGui.QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(frames_to_write)-1)
        self.vbox.addWidget(self.progress_bar)
        self.setLayout(self.vbox)
        QTimer.singleShot(10, self.save_single_screenshot)
        self.is_rejected = False


    def save_single_screenshot(self):
        if self.is_rejected:
            return
        current_frame = self.frames_to_write.pop(0)
        file_name, frame_number = current_frame
        width, height = 1920, 1080
        image_file_name = os.path.join(self.dir_name, "{}.{:06d}.png".format(os.path.basename(file_name), frame_number))
        self.control.visualize(file_name, frame_number)
        self.control.visualization.create_scene()
        gr3.export(image_file_name, width, height)
        print(image_file_name)
        if self.frames_to_write:
            self.progress_bar.setValue(self.progress_bar.maximum()-len(self.frames_to_write)+1)
            self.update()
            QTimer.singleShot(10, self.save_single_screenshot)
        else:
            self.done(0)

    def reject(self):
        self.is_rejected = True
        super(MassScreenshotDialog, self).reject()
