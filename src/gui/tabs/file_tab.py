# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui
import os.path
from core import calculation, volumes
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
    def __init__(self, parent, settings):
        QtCore.QThread.__init__(self, parent)
        self.settings = settings

    def run(self):
        calculation.calculate(self.settings)


class FileTab(QtGui.QWidget):
    """
        tab 'file' in the main widget
    """

    def __init__(self, parent, main_window):
        QtGui.QWidget.__init__(self, parent)
        self.init_gui()
        self.main_window = main_window
        self.progress_dialog = ProgressDialog(self)

        p = self.progress_dialog
        self.main_window.set_output_callbacks(p.progress, p.print_step, p.calculation_finished)

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

        self.vbox.addLayout(self.button_hbox)

        self.file_list = DragList(self)
        self.file_list.itemDoubleClicked.connect(self.calculate)
        self.file_list.itemSelectionChanged.connect(self.selection_changed)
        self.vbox.addWidget(self.file_list)

#        for f in os.listdir("../xyz"):
#            if f.endswith(".xyz"):
#                self.file_list.add_file(os.path.join("../xyz", f))
        # load recent files
        for path in config.recent_files:
            self.file_list.add_file(path)

        self.setLayout(self.vbox)

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

    def calculate(self):
        filenames = map(str, self.file_list.get_selection())
        if len(filenames) == 0:
            QtGui.QMessageBox.information(self, 'Information', "Choose a dataset", QtGui.QMessageBox.Ok)
            return
        dia = CalculationSettingsDialog(self, filenames)
        settings, ok = dia.calculation_settings()

        if ok:
            calculated = [calculation.calculated(fn, frame, settings.resolution, False) for frame in settings.frames for fn in settings.filenames]
            if any(calculated):
                #show Yes No Dialog
                reply = QtGui.QMessageBox.warning(self,
                                                'Warning',
                                                "Are you sure that the existing results should be overwritten?",
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.No:
                    return
            thread = CalculationThread(self, settings)
            thread.start()
            self.progress_dialog.exec_()
            thread.wait()

            self.main_window.show_dataset(fn, settings.frames[-1], settings.resolution)
    #
    # def calculate_frames(self, filename, frame_nr, resolution, use_center_points):
    #     if calculation.calculated(filename, frame_nr, resolution, True):
    #         base_name = ''.join(os.path.basename(filename).split(".")[:-1])
    #         exp_name = "{}{}.hdf5".format(config.Path.result_dir, base_name)
    #         calculation.delete_center_cavity_information(exp_name, frame_nr, resolution)
    #
    #     if use_center_points:
    #         if not calculation.calculated(filename, frame_nr, resolution, False):
    #             thread = CalculationThread(self, filename, frame_nr, resolution, False)
    #             thread.start()
    #             self.progress_dialog.exec_()
    #             thread.wait()
    #
    #     thread = CalculationThread(self, filename, frame_nr, resolution, use_center_points)
    #     thread.start()
    #     self.progress_dialog.exec_()


class DragList(QtGui.QListWidget):
    def __init__(self, parent):
        super(DragList, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.datalist = {}

    def dragMoveEvent(self, event):
        pass

    def add_file(self, path):
        bname = os.path.basename(path)
        if bname not in self.datalist and path.endswith('.xyz'):
            self.datalist[bname] = path
            self.addItem(bname)
            if path not in config.recent_files:
                print path
                config.add_recent_file(path)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            if e.mimeData().urls()[0].scheme() == 'file':
                e.accept()
            else:
                e.ignore()
        else:
            e.ignore()

    def dropEvent(self, e):
        for f in e.mimeData().urls():
            if os.path.isfile(f.path()):
                self.add_file(f.path())

    def remove_selected_files(self):
        for item in self.selectedItems():
            row = self.row(item)
            self.takeItem(row)
            del self.datalist[item.text()]

    def get_selection(self):
        return [self.datalist[str(item.text())] for item in self.selectedItems()]
