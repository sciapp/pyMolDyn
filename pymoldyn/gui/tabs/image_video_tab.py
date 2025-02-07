import os.path
import shutil
import sys
import tempfile

from PySide6 import QtWidgets
from PySide6.QtCore import QProcess, QTimer

from ...core import file


class ImageVideoTabDock(QtWidgets.QDockWidget):
    """
    DockWidget for the 'image/video'-tab
    """

    def __init__(self, parent):
        super().__init__("image/video", parent)  # self?
        self.setWidget(QtWidgets.QWidget())

        self.layout = QtWidgets.QHBoxLayout()
        self.image_video_tab = ImageVideoTab(self.widget(), parent)

        self.layout.addWidget(self.image_video_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)


class ImageVideoTab(QtWidgets.QWidget):
    """
    tab 'image/video' in the main widget
    """

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.init_gui()

    def init_gui(self):
        self.vbox = QtWidgets.QVBoxLayout()

        self.screenshot_button = QtWidgets.QPushButton("Save screenshot for the current frame", self)
        self.video_button = QtWidgets.QPushButton("Save video for all selected frames", self)
        self.mass_screenshot_button = QtWidgets.QPushButton("Save screenshot for all selected frames", self)

        self.screenshot_button.clicked.connect(self.save_screenshot)
        self.screenshot_button.setDisabled(True)
        self.mass_screenshot_button.clicked.connect(self.save_screenshot_for_all_selected_frames)
        self.mass_screenshot_button.setDisabled(True)
        self.video_button.clicked.connect(self.save_video_for_all_selected_frames)
        self.video_button.setDisabled(True)

        self.vbox.addWidget(self.screenshot_button)
        self.vbox.addWidget(self.mass_screenshot_button)
        self.vbox.addWidget(self.video_button)
        self.vbox.addStretch()
        self.setLayout(self.vbox)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    def save_screenshot(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save screenshot...", filter="Portable Network Graphics (*.png)"
        )[0]
        if file_name:
            ext = os.path.splitext(file_name)[1]
            if not ext:
                file_name += ".png"
            self.main_window.control.visualization.save_screenshot(file_name)

    def get_selected_frames(self):
        file_list = self.main_window.file_dock.file_tab.file_list
        selection = file_list.get_selection()
        if not selection:
            QtWidgets.QMessageBox.information(
                self,
                "No frame selected",
                "Please use the file tab to select at least one frame.",
                QtWidgets.QMessageBox.Ok,
                QtWidgets.QMessageBox.NoButton,
            )
            return

        frames_to_write = []
        for file_name, frame_numbers in selection.items():
            if frame_numbers == [-1]:
                num_frames = file.File.open(file_name).info.num_frames
                frame_numbers = range(num_frames)
            for frame_number in frame_numbers:
                frames_to_write.append((file_name, frame_number))
        return frames_to_write

    def save_video_for_all_selected_frames(self):
        frames_to_write = self.get_selected_frames()
        if not frames_to_write:
            return
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, "Save video...", filter="QuickTime Movie (*.mov)")[0]
        if file_name:
            ext = os.path.splitext(file_name)[1]
            if not ext:
                file_name += ".mov"
            dialog = MassScreenshotAndVideoDialog(
                self, frames_to_write, should_save_video=True, video_file_name=file_name
            )
            dialog.show()
            return

    def save_screenshot_for_all_selected_frames(self):
        frames_to_write = self.get_selected_frames()
        if not frames_to_write:
            return
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(self, "Save screenshots to folder...")
        if dir_name:
            dialog = MassScreenshotAndVideoDialog(self, frames_to_write, dir_name)
            dialog.show()
            return


class MassScreenshotAndVideoDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent,
        frames_to_write,
        dir_name=None,
        should_save_video=False,
        video_file_name=None,
    ):
        super().__init__(parent)
        self.control = parent.main_window.control
        self.setModal(True)
        self.frames_to_write = frames_to_write
        self.images_written = []
        if not dir_name:
            dir_name = tempfile.mkdtemp()
            self.delete_dir = True
        else:
            self.delete_dir = False
        self.dir_name = dir_name
        self.should_save_video = should_save_video
        self.video_file_name = video_file_name
        self.vbox = QtWidgets.QVBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        if self.should_save_video:
            self.progress_bar.setMaximum(int(2.5 * len(frames_to_write)))
        else:
            self.progress_bar.setMaximum(len(frames_to_write))
        self.vbox.addWidget(self.progress_bar)
        self.setLayout(self.vbox)
        self.is_rejected = False
        self.process = None
        self.is_first_frame = True
        if self.should_save_video:
            self.setWindowTitle("Saving video...")
        else:
            self.setWindowTitle("Saving screenshots...")
        QTimer.singleShot(10, self.save_single_screenshot)

    def save_single_screenshot(self):
        if self.is_rejected:
            return
        current_frame = self.frames_to_write.pop(0)
        file_name, frame_number = current_frame
        width, height = 1920, 1080
        image_file_name = os.path.join(
            self.dir_name,
            "{}.{:06d}.png".format(os.path.basename(file_name), frame_number + 1),
        )
        self.control.visualize(file_name, frame_number)
        self.control.visualization.create_scene()
        self.control.visualization.save_screenshot(
            image_file_name,
            width,
            height,
            self.is_first_frame,
            not self.frames_to_write,
        )
        self.images_written.append(image_file_name)
        self.is_first_frame = False
        if self.frames_to_write:
            self.progress_bar.setValue(len(self.images_written))
            self.update()
            QTimer.singleShot(10, self.save_single_screenshot)
        elif self.should_save_video:
            QTimer.singleShot(10, self.save_video)
        else:
            self.done(0)

    def save_video(self):
        self.process = QProcess()
        self.process.start(
            "gr",
            ["../util/video_output.py", self.video_file_name] + self.images_written,
        )
        self.process.readyReadStandardOutput.connect(self.process_output)
        self.process.readyReadStandardError.connect(self.process_error)
        self.process.finished.connect(lambda *args: self.finished_video())

    def finished_video(self):
        if self.delete_dir:
            shutil.rmtree(self.dir_name)
        self.done(0)

    def process_output(self):
        output = self.process.readAllStandardOutput()
        for line in str(output).splitlines():
            try:
                number = int(line)
            except ValueError:
                pass
            else:
                self.progress_bar.setValue(len(self.images_written) + number)

    def process_error(self):
        output = self.process.readAllStandardError()
        sys.stderr.write(str(output, "utf-8"))

    def reject(self):
        self.is_rejected = True
        if self.process is not None:
            self.process.terminate()
        super(MassScreenshotAndVideoDialog, self).reject()
