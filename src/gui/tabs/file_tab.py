# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import os.path
import functools
from core import calculation, volumes, file
from gui.dialogs.calc_settings_dialog import CalculationSettingsDialog
from gui.dialogs.progress_dialog import ProgressDialog
from config.configuration import config
from util.message import print_message, progress, finish
from gui.gl_widget import GLWidget, UpdateGLEvent
from core.file import File
from util import message


class FileTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'file'-tab
    """
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "file", parent)
        self.setWidget(QtGui.QWidget(self))

        self.layout     = QtGui.QHBoxLayout()
        self.file_tab   = FileTab(self.widget(), parent)

        self.layout.addWidget(self.file_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)


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
            message.error(e)
            message.finish()


class FileTab(QtGui.QWidget):
    """
        tab 'file' in the main widget
    """

    def __init__(self, parent, main_window):
        QtGui.QWidget.__init__(self, parent)
        self.main_window = main_window
        self.progress_dialog = ProgressDialog(self)
        self.most_recent_path = "~"

        p = self.progress_dialog
        self.main_window.set_output_callbacks(p.progress, p.print_step, p.calculation_finished, lambda e: QtCore.QMetaObject.invokeMethod(self, '_error', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, e.message)))
        self.control = main_window.control

        self.init_gui()

    @QtCore.pyqtSlot(str)
    def _error(self, error_message):
        QtGui.QMessageBox.information(self, 'Information', error_message, QtGui.QMessageBox.Ok)

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setSpacing(0)
        self.button_hbox = QtGui.QHBoxLayout()
        self.button_hbox.setSpacing(10)

        self.file_button = QtGui.QPushButton('Open', self)
        self.file_button.setDefault(True)
        self.file_button.clicked.connect(self.open_file_dialog)
        self.button_hbox.addWidget(self.file_button)

        self.delete_button = QtGui.QPushButton('Delete', self)
        self.delete_button.clicked.connect(self.remove_selected_files)
        self.delete_button.setDisabled(True)
        self.button_hbox.addWidget(self.delete_button)

        self.calculate_button = QtGui.QPushButton('Calculate', self)
        self.calculate_button.clicked.connect(self.calculate)
        self.calculate_button.setDisabled(True)
        self.button_hbox.addWidget(self.calculate_button)

        self.show_button = QtGui.QPushButton('Show', self)
        self.show_button.clicked.connect(self.show_selected_frame)
        self.show_button.setDisabled(True)
        self.button_hbox.addWidget(self.show_button)

        self.vbox.addLayout(self.button_hbox)

        self.button2_hbox = QtGui.QHBoxLayout()
        self.button2_hbox.setSpacing(10)

        self.select_all_button = QtGui.QPushButton('Select all frames', self)
        self.select_all_button.clicked.connect(self.select_all)
        self.select_all_button.setDisabled(True)
        self.button2_hbox.addWidget(self.select_all_button)

        self.select_nth_button = QtGui.QPushButton('Select every nth frame...', self)
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
        n, okay = QtGui.QInputDialog.getInt(self, "Set n", "", 1, 1)
        if okay:
            self.file_list.select_nth(n)

    def show_selected_frame(self):
        self.file_list.show_selected_frame()

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
            QtGui.QMessageBox.information(self, 'Information', e.message, QtGui.QMessageBox.Ok)
            return

    def open_file_dialog(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(self, 'Open dataset', self.most_recent_path)
        for path in filenames:
            if path:
                #print path

                #print self.main_window.recent_files_submenu.actions()
                self.disable_files_in_menu_and_open(path)
                self.main_window.update_submenu_recent_files()


    def calculationcallback(self, func, settings):
        thread = CalculationThread(self, func, settings)
        thread.finished.connect(functools.partial(self.control.update, was_successful=lambda : thread.exited_with_errors))
        thread.finished.connect(functools.partial(self.main_window.updatestatus, was_successful=lambda : thread.exited_with_errors))
        thread.start()
        self.progress_dialog.exec_()

    def calculate(self):
        file_frame_dict = self.file_list.get_selection()
        dia = CalculationSettingsDialog(self, file_frame_dict)
        settings, ok = dia.calculation_settings()

        if ok:
            self.control.calculationcallback = self.calculationcallback
            self.control.calculate(settings)

class TreeList(QtGui.QTreeWidget):

    def __init__(self, parent, data={}):
        QtGui.QTreeWidget.__init__(self, parent)

        self.control = parent.control
        self.setColumnCount(1)
        self.path_dict = {}

        for root, sib in data.iteritems():
            self.append_item(root, sib)

        self.setHeaderHidden(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        #self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        #self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setMouseTracking(True)
        self.itemSelectionChanged.connect(self.selection_changed)

    def append_item(self, root, sib):
        item = QtGui.QTreeWidgetItem(self)
        item.setText(0, root)
        if sib:
            for s in sib:
                tmp = QtGui.QTreeWidgetItem(item)
                tmp.setText(0, s)
                item.addChild(tmp)
        self.addTopLevelItem(item)

    def mimeTypes(self):
        print 'mimeTypes'
        return ['text/uri-list', 'application/x-qabstractitemmodeldatalist']

    def supportedDropActions(self):
        print('supportedDropAction', self.defaultDropAction())
        return QtCore.Qt.MoveAction

    def dragEnterEvent(self, e):
        self.setState(QtGui.QAbstractItemView.DraggingState)
        print 'DRAG', e.mimeData().formats()
        if e.mimeData().hasUrls():
            if e.mimeData().urls()[0].scheme() == 'file':
                e.accept()
        e.ignore()

    def mimeData(self, *args, **kwargs):
        print('mimeData', args, kwargs)

    def dropMimeData(self, *args, **kwargs):
        print('dropMimeData', args, kwargs)

    def dropEvent(self, e):
        print 'dropEvent'
        for f in e.mimeData().urls():
            if os.path.isfile(f.path()):
                self.add_file(f.path())

    def selection_changed(self):
        frames_selected = 0
        for item in self.selectedItems():
            # items representing the whole dataset
            if not item.data(0, 0).startswith('frame'):
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
        self.parent().show_button.setEnabled(frames_selected == 1)

    def files_changed(self):
        any_files_available = self.topLevelItemCount() > 0
        self.parent().select_all_button.setEnabled(any_files_available)
        self.parent().select_nth_button.setEnabled(any_files_available)
        self.parent().file_button.setDefault(not any_files_available)

    def get_selection(self):
        sel = {}
        for item in self.selectedItems():
            content = str(item.data(0, 0))
            if not content.startswith('frame'):
                sel[self.path_dict[content]] = [-1]
            else:
                parent_content = str(item.parent().data(0, 0))
                if sel.has_key(self.path_dict[parent_content]):
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
            if content.startswith('frame'):
                item.parent().takeChild(item.parent().indexOfChild(item))
                self.removeItemWidget(item, 0)
                del del_files[i]

        # delete top level items
        for item in self.selectedItems():
            content = str(item.data(0, 0))
            if not content.startswith('frame'):
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
            sib = ['frame {}'.format(i) for i in range(1, n_frames + 1)]
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

        filename = sel.keys()[0]
        frame = sel[filename][0]

        if frame == -1:
            if file.File.open(filename).info.num_frames > 1:
                frame = -2
            else:
                frame = 0

        self.control.visualize(filename, frame)

        widget = self
        while not hasattr(widget, "updatestatus"):
            widget = widget.parent()
        widget.updatestatus()

        # update GL scene
        for widget in QtGui.QApplication.topLevelWidgets():
            for gl_widget in widget.findChildren(GLWidget):
                gl_widget.update_needed = True
                QtGui.QApplication.postEvent(gl_widget, UpdateGLEvent())

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
