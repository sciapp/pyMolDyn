# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui
import os.path
from core import calculation, volumes, file
from gui.dialogs.calc_settings_dialog import CalculationSettingsDialog
from gui.dialogs.progress_dialog import ProgressDialog
from config.configuration import config
from util.message import print_message, progress, finish


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

    def run(self):
        self.func(self.settings)


class FileTab(QtGui.QWidget):
    """
        tab 'file' in the main widget
    """

    def __init__(self, parent, main_window):
        QtGui.QWidget.__init__(self, parent)
        self.main_window = main_window
        self.progress_dialog = ProgressDialog(self)

        p = self.progress_dialog
        self.main_window.set_output_callbacks(p.progress, p.print_step, p.calculation_finished)
        self.control = main_window.control

        self.init_gui()

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()
        self.button_hbox = QtGui.QHBoxLayout()

        self.file_button = QtGui.QPushButton('Open', self)
        self.file_button.clicked.connect(self.open_file_dialog)
        self.button_hbox.addWidget(self.file_button)

        self.delete_button = QtGui.QPushButton('Delete', self)
        self.delete_button.clicked.connect(self.remove_selected_files)
        self.button_hbox.addWidget(self.delete_button)

        self.calculate_button = QtGui.QPushButton('Calculate', self)
        self.calculate_button.clicked.connect(self.calculate)
        self.button_hbox.addWidget(self.calculate_button)

        self.show_button = QtGui.QPushButton('Show', self)
        self.show_button.clicked.connect(self.show_selected_frame)
        self.button_hbox.addWidget(self.show_button)

        self.vbox.addLayout(self.button_hbox)

#        self.file_list = DragList(self)
#        self.file_list.itemDoubleClicked.connect(self.calculate)
#        self.file_list.itemSelectionChanged.connect(self.selection_changed)
#        self.vbox.addWidget(self.file_list)
#
#        for path in config.recent_files:
#            self.file_list.add_file(path)

        self.file_list = TreeList(self)
        self.vbox.addWidget(self.file_list)

        self.setLayout(self.vbox)

    def show_selected_frame(self):
        self.file_list.show_selected_frame()

    def selection_changed(self):
        sel = self.file_list.get_selection()
        if not sel or len(self.file_list.get_selection()) > 1:
            return

    def remove_selected_files(self):
        self.file_list.remove_selected_files()

    def open_file_dialog(self):
        filenames, _ = QtGui.QFileDialog.getOpenFileNames(self, 'Open dataset', '~')

        for fn in filenames:
            if fn:
                self.file_list.add_file(fn)

    def calculationcallback(self, func, settings):
        thread = CalculationThread(self, func, settings)
        thread.finished.connect(self.control.update)
        thread.finished.connect(self.main_window.updatestatus)
        thread.start()
        self.progress_dialog.exec_()

    def calculate(self):
        file_frame_dict = self.file_list.get_selection()
        if not file_frame_dict:
            QtGui.QMessageBox.information(self, 'Information', "Choose a dataset", QtGui.QMessageBox.Ok)
            return
        dia = CalculationSettingsDialog(self, file_frame_dict)
        settings, ok = dia.calculation_settings()
# TODO
#        if ok:
#            self.control.calculationcallback = self.calculationcallback
#            self.control.calculate(settings)

class TreeList(QtGui.QTreeWidget):

    def __init__(self,parent, data={}):
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
        for item in self.selectedItems():
            # items representing the whole dataset
            if (not item.data(0, 0).startswith('frame')):
                # select the children of the selected dataset
                 for i in range(item.childCount()):
                     c = item.child(i)
                     c.setSelected(True)

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

    def add_file(self, path):
        bname = os.path.basename(path)
        f = file.File.open(path)
        n_frames = f.info.num_frames

        if bname not in self.path_dict.keys() and path.endswith('.xyz'):
            self.path_dict[bname] = str(path)
            root = bname
            sib = ['frame {}'.format(i) for i in range(1, n_frames + 1)]
            self.append_item(root, sib)

            if path not in config.recent_files:
                config.add_recent_file(path)

    def show_selected_frame(self):
        sel = self.get_selection()
        filename = sel.keys()[0]
        frame = sel[filename][0]

        if frame == -1:
            if file.File.open(filename).info.num_frames > 1:
                frame = -2
            else:
                frame = 0

        if len(sel.keys()) > 1 or len(sel.values()[0]) > 1 or frame == -2:
            QtGui.QMessageBox.information(self, 'Information', "Choose a single frame to show", QtGui.QMessageBox.Ok)
            return

        self.control.visualize(filename, frame)
