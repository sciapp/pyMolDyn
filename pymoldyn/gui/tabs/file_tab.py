import functools
import os.path

from PySide6 import QtCore, QtWidgets

from ...config.configuration import config
from ...core import file
from ...core.file import File
from ...util import message
from ..dialogs.calc_settings_dialog import CalculationSettingsDialog
from ..dialogs.progress_dialog import ProgressDialog
from ..gl_widget import GLWidget, UpdateGLEvent


class FileTabDock(QtWidgets.QDockWidget):
    """
    DockWidget for the 'file'-tab
    """

    def __init__(self, parent):
        QtWidgets.QDockWidget.__init__(self, "file", parent)
        self.setWidget(QtWidgets.QWidget(self))

        self.layout = QtWidgets.QHBoxLayout()
        self.file_tab = FileTab(self.widget(), parent)

        self.layout.addWidget(self.file_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)


class CalculationThread(QtCore.QThread):
    """
    Thread to calculate the cavities
    """

    def __init__(self, parent, func, settings):
        QtCore.QThread.__init__(self, parent)
        self.func = func
        self.settings = settings
        self._exited_with_errors = False

    @property
    def exited_with_errors(self):
        return self._exited_with_errors

    def run(self):
        try:
            self.func(self.settings)
        except Exception as e:
            self._exited_with_errors = True
            message.error(str(e))
            message.finish()
            raise


class FileTab(QtWidgets.QWidget):
    """
    tab 'file' in the main widget
    """

    def __init__(self, parent, main_window):
        QtWidgets.QWidget.__init__(self, parent)
        self.main_window = main_window
        self.progress_dialog = ProgressDialog(self)
        self.most_recent_path = "~"

        self.control = main_window.control

        self.init_gui()
        self.guessed_volumes_for = set()
        self.last_shown_filename_with_frame = None

    def init_gui(self):
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(0)
        self.button_hbox = QtWidgets.QHBoxLayout()
        self.button_hbox.setSpacing(10)

        self.file_button = QtWidgets.QPushButton("Open", self)
        self.file_button.setDefault(True)
        self.file_button.clicked.connect(self.open_file_dialog)
        self.button_hbox.addWidget(self.file_button)

        self.delete_button = QtWidgets.QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.remove_selected_files)
        self.delete_button.setDisabled(True)
        self.button_hbox.addWidget(self.delete_button)

        self.calculate_button = QtWidgets.QPushButton("Calculate", self)
        self.calculate_button.clicked.connect(self.calculate)
        self.calculate_button.setDisabled(True)
        self.button_hbox.addWidget(self.calculate_button)

        self.show_button = QtWidgets.QPushButton("Show", self)
        self.show_button.clicked.connect(self.show_selected_frame)
        self.show_button.setDisabled(True)
        self.button_hbox.addWidget(self.show_button)

        self.vbox.addLayout(self.button_hbox)

        self.button2_hbox = QtWidgets.QHBoxLayout()
        self.button2_hbox.setSpacing(10)

        self.select_all_button = QtWidgets.QPushButton("Select all frames", self)
        self.select_all_button.clicked.connect(self.select_all)
        self.select_all_button.setDisabled(True)
        self.button2_hbox.addWidget(self.select_all_button)

        self.select_nth_button = QtWidgets.QPushButton("Select every nth frame...", self)
        self.select_nth_button.clicked.connect(self.select_nth)
        self.select_nth_button.setDisabled(True)
        self.button2_hbox.addWidget(self.select_nth_button)

        self.vbox.addLayout(self.button2_hbox)

        #        self.file_list = DragList(self)
        #        self.file_list.itemDoubleClicked.connect(self.calculate)
        #        self.file_list.itemSelectionChanged.connect(self.selection_changed)
        #        self.vbox.addWidget(self.file_list)
        #
        #        for path in config.recent_files:
        #            self.file_list.add_file(path)

        self.file_list = TreeList(self)
        self.vbox.addSpacing(10)
        self.vbox.addWidget(self.file_list)

        self.setLayout(self.vbox)

    def select_all(self):
        self.file_list.select_all()

    def select_nth(self):
        n, okay = QtWidgets.QInputDialog.getInt(self, "Set n", "", 1, 1)
        if okay:
            self.file_list.select_nth(n)

    def show_selected_frame(self):
        self.last_shown_filename_with_frame = self.file_list.show_selected_frame()

    def selection_changed(self):
        sel = self.file_list.get_selection()
        if not sel or len(self.file_list.get_selection()) > 1:
            return

    def remove_selected_files(self):
        self.enable_files_in_menu()
        self.file_list.remove_selected_files()

    def enable_files_in_menu(self):
        actions = self.main_window.recent_files_submenu.actions()
        selected = self.file_list.selectedItems()
        if not selected:
            return
        text = None
        subitem = selected[0]
        item = subitem.parent()

        # if sheet contains only one frame and this is deleted, the parent will be also deleted
        if subitem.text(0).startswith("frame") and ((item.childCount() == 1) or (item.childCount() == len(selected))):
            text = item.text(0)
            for action in actions:
                if action.text().endswith(text):
                    action.setEnabled(True)
                    item.takeChild(item.indexOfChild(subitem))
                    self.file_list.removeItemWidget(subitem, 0)
                    self.file_list.takeTopLevelItem(self.file_list.indexOfTopLevelItem(item))
                    self.file_list.removeItemWidget(item, 0)
                    del self.file_list.path_dict[text]
        else:
            for sel in selected:
                # tree_list elements get only reenabled in menu if the whole sheet is removed from file_list
                if sel.text(0).startswith("frame"):
                    continue

                for action in actions:
                    if action.text() == self.file_list.path_dict[sel.text(0)]:
                        action.setEnabled(True)

    def disable_files_in_menu_and_open(self, path):
        for action in self.main_window.recent_files_submenu.actions():
            if action.text() == path:
                action.setDisabled(True)
        try:
            self.file_list.add_file(path)
        except ValueError as e:
            QtWidgets.QMessageBox.information(self, "Information", str(e), QtWidgets.QMessageBox.Ok)
            return

    def open_file_dialog(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self, "Open dataset", self.most_recent_path)[0]
        for path in filenames:
            if path:
                self.disable_files_in_menu_and_open(path)
                self.main_window.update_submenu_recent_files()

    def calculationcallback(self, func, settings):
        def enable_screenshot_button_on_success(self, was_successful):
            if was_successful():
                self.file_list._enable_screenshot_button()

        self.thread = CalculationThread(self, func, settings)
        self.thread.finished.connect(
            functools.partial(
                self.control.update,
                was_successful=lambda: not self.thread.exited_with_errors,
            )
        )
        self.thread.finished.connect(
            functools.partial(
                self.main_window.updatestatus,
                was_successful=lambda: not self.thread.exited_with_errors,
            )
        )
        self.thread.finished.connect(
            functools.partial(
                enable_screenshot_button_on_success,
                self,
                was_successful=lambda: not self.thread.exited_with_errors,
            )
        )
        self.thread.start()
        self.progress_dialog.exec_()

    def calculate(self, file_frame_dict=None):
        if not file_frame_dict:
            file_frame_dict = self.file_list.get_selection()
        dia = CalculationSettingsDialog(self, file_frame_dict)
        settings, ok = dia.calculation_settings()

        if ok:
            self.control.calculationcallback = self.calculationcallback
            self.control.calculate(settings)
            self.last_shown_filename_with_frame = (
                list(file_frame_dict.keys())[-1],
                list(file_frame_dict.values())[-1][-1],
            )


class TreeList(QtWidgets.QTreeWidget):

    def __init__(self, parent, data={}):
        QtWidgets.QTreeWidget.__init__(self, parent)

        self.control = parent.control
        self.setColumnCount(1)
        self.path_dict = {}

        for root, sib in data.items():
            self.append_item(root, sib)

        self.setHeaderHidden(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMouseTracking(True)
        self.itemSelectionChanged.connect(self.selection_changed)

    def append_item(self, root, sib):
        item = QtWidgets.QTreeWidgetItem(self)
        item.setText(0, root)
        if sib:
            for s in sib:
                tmp = QtWidgets.QTreeWidgetItem(item)
                tmp.setText(0, s)
                item.addChild(tmp)
        self.addTopLevelItem(item)

    def acceptable_drop_urls(self, e):
        if e.mimeData().hasUrls():
            for url in e.mimeData().urls():
                if url.scheme() == "file" and os.path.isfile(url.path()):
                    yield url

    def dragEnterEvent(self, e):
        if any(self.acceptable_drop_urls(e)):
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if any(self.acceptable_drop_urls(e)):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if any(self.acceptable_drop_urls(e)):
            e.accept()
        else:
            e.ignore()
        # actually add the files
        for url in self.acceptable_drop_urls(e):
            self.add_file(url.path())

    def mouseDoubleClickEvent(self, e):
        if self.parent().show_button.isEnabled():
            self.parent().show_selected_frame()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Return and self.parent().show_button.isEnabled():
            self.parent().show_selected_frame()
        else:
            super().keyPressEvent(e)

    def selection_changed(self):
        frames_selected = 0
        for item in self.selectedItems():
            # items representing the whole dataset
            if not item.data(0, 0).startswith("frame"):
                # select the children of the selected dataset
                for i in range(item.childCount()):
                    c = item.child(i)
                    c.setSelected(True)
                    frames_selected += 1
            else:
                frames_selected += 1
        any_frame_selected = len(self.selectedItems()) > 0
        self.parent().delete_button.setEnabled(any_frame_selected)
        self.parent().calculate_button.setEnabled(any_frame_selected)
        only_one_frame_available = self.topLevelItemCount() == 1 and self.topLevelItem(0).childCount() == 1
        self.parent().show_button.setEnabled(
            frames_selected == 1 or (not any_frame_selected and only_one_frame_available)
        )
        parent = self.parent()
        while parent.parent():
            parent = parent.parent()
        main_window = parent
        image_video_tab = main_window.image_video_dock.image_video_tab
        image_video_tab.mass_screenshot_button.setEnabled(any_frame_selected)
        image_video_tab.video_button.setEnabled(any_frame_selected)

    def files_changed(self):
        any_files_available = self.topLevelItemCount() > 0
        self.parent().select_all_button.setEnabled(any_files_available)
        self.parent().select_nth_button.setEnabled(any_files_available)
        self.parent().file_button.setDefault(not any_files_available)
        self.selection_changed()

    def get_selection(self):
        sel = {}
        for item in self.selectedItems():
            content = str(item.data(0, 0))
            if not content.startswith("frame"):
                sel[self.path_dict[content]] = [-1]
            else:
                parent_content = str(item.parent().data(0, 0))
                if self.path_dict[parent_content] in sel:
                    if not sel[self.path_dict[parent_content]][0] == -1:
                        sel[self.path_dict[parent_content]].append(int(content[6:]) - 1)
                else:
                    sel[self.path_dict[parent_content]] = [int(content[6:]) - 1]
        return sel

    def remove_selected_files(self):
        # delete childs
        del_files = self.selectedItems()
        for i, item in enumerate(del_files):
            content = str(item.data(0, 0))
            if content.startswith("frame"):
                item.parent().takeChild(item.parent().indexOfChild(item))
                self.removeItemWidget(item, 0)
                del del_files[i]

        # delete top level items
        for item in self.selectedItems():
            content = str(item.data(0, 0))
            if not content.startswith("frame"):
                self.takeTopLevelItem(self.indexOfTopLevelItem(item))
                self.removeItemWidget(item, 0)
                del self.path_dict[content]

        self.files_changed()

    def add_file(self, path):
        bname = os.path.basename(path)
        f = file.File.open(path)
        n_frames = f.info.num_frames

        if bname not in self.path_dict.keys() and File.exists(path):
            self.path_dict[bname] = str(path)
            root = bname
            sib = ["frame {}".format(i) for i in range(1, n_frames + 1)]
            self.append_item(root, sib)

            if path not in config.recent_files:
                config.add_recent_file(path)
            else:
                index = config.recent_files.index(path)
                config.recent_files.pop(index)
                config.add_recent_file(path)

        self.files_changed()

    def show_selected_frame(self):
        # if there is just one file with one frame, select that frame automatically
        if self.topLevelItemCount() == 1 and self.topLevelItem(0).childCount() == 1:
            self.select_all()

        sel = self.get_selection()

        filename = list(sel.keys())[0]
        frame = sel[filename][0]

        if frame == -1:
            if file.File.open(filename).info.num_frames > 1:
                frame = -2
            else:
                frame = 0

        f = file.File.open(filename)
        if filename not in self.parent().guessed_volumes_for and f.info.volume_guessed:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle("Missing cell shape description")
            msgBox.setTextFormat(QtCore.Qt.RichText)
            msgBox.setText(
                "This file does not contain information about the "
                "cell shape. Should pyMolDyn use an orthorhombic "
                "shape?<br />"
                "You can find information about the different cell "
                "shapes shapes in the "
                '<a href="https://pgi-jcns.fz-juelich.de/portal/pages/pymoldyn-doc.html#cell-shape-description">'
                "pyMolDyn documentation</a>"
            )
            msgBox.addButton(QtWidgets.QMessageBox.Yes)
            msgBox.addButton(QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
            msgBox.setEscapeButton(QtWidgets.QMessageBox.No)
            response = msgBox.exec_()
            if response == QtWidgets.QMessageBox.No:
                return
            self.parent().guessed_volumes_for.add(filename)

        self.control.visualize(filename, frame)

        widget = self
        while not hasattr(widget, "updatestatus"):
            widget = widget.parent()
        widget.updatestatus()

        # update GL scene
        for widget in QtWidgets.QApplication.topLevelWidgets():
            for gl_widget in widget.findChildren(GLWidget):
                gl_widget.update_needed = True
                QtWidgets.QApplication.postEvent(gl_widget, UpdateGLEvent())

        self._enable_screenshot_button()

        return filename, frame

    def _enable_screenshot_button(self, enable=True):
        parent = self.parent()
        while parent.parent():
            parent = parent.parent()
        main_window = parent
        image_video_tab = main_window.image_video_dock.image_video_tab
        image_video_tab.screenshot_button.setEnabled(enable)

    def select_all(self):
        self.select_nth(1)

    def select_nth(self, n):
        assert int(n) == n and n > 0
        for file_index in range(self.topLevelItemCount()):
            item = self.topLevelItem(file_index)
            if n == 1:
                item.setSelected(True)
            else:
                item.setSelected(False)
                item.setExpanded(True)
            # select every nth child and unselect the others
            for frame_index in range(item.childCount()):
                c = item.child(frame_index)
                c.setSelected(frame_index % n == 0)
