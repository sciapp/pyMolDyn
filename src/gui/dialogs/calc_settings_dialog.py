# -*- coding: utf-8 -*-


from gui.dialogs.util.calc_table import CalculationTable, TableModel
from gui.dialogs.cutoff_history_dialog import CutoffHistoryDialog
from gui.util.labeled_combobox import LabeledComboBox
from core import calculation
from core import file
import collections
import datetime
import os.path
import itertools as it
from config.configuration import config
from config.cutoff_history import cutoff_history
from config.cutoff_history import HistoryEntry
from PyQt4 import QtGui, QtCore


class CalculationSettingsDialog(QtGui.QDialog):

    RES_MIN = 32
    RES_MAX = 1024
    RES_INTERVAL = 32

    def __init__(self, parent, file_frame_dict):
        QtGui.QDialog.__init__(self, parent)

        self.control = parent.control
        self.resolution = config.Computation.std_resolution
        self.filenames = file_frame_dict.keys()
        self.file_frame_dict = file_frame_dict

        self.init_gui()
        self.setWindowTitle("Calculation Settings")

    def init_gui(self):

        vbox            = QtGui.QVBoxLayout()
        hbox            = QtGui.QHBoxLayout()
        inner_layout    = QtGui.QVBoxLayout()
        button_hbox     = QtGui.QHBoxLayout()
        res_hbox        = QtGui.QHBoxLayout()

        self.res_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.res_slider.setMinimum(0)
        self.res_slider.setMaximum((self.RES_MAX - self.RES_MIN) / self.RES_INTERVAL)
        # self.res_slider.setTickInterval(1)
        # self.res_slider.setTickPosition(QtGui.QSlider.TicksBelow)
        self.res_slider.valueChanged[int].connect(self.slider_changing)
        self.res_slider.sliderReleased.connect(self.slider_released)

        self.lineedit   = QtGui.QLineEdit(self)
        self.lineedit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.lineedit.setMinimumSize(30, 1)
        self.lineedit.setMaximumSize(40, 40)
        self.lineedit.returnPressed.connect(self.lineedit_return)

        res_hbox.addWidget(QtGui.QLabel('resolution:', self))
        res_hbox.addWidget(self.res_slider)
        res_hbox.addWidget(self.lineedit)

        # set font
#        font = QFont("Courier New", 14)
#        table_view.setFont(font)
        # set column width to fit contents (set font first!)
        # enable sortingq
#        table_view.setSortingEnabled(True)

        ok_button = QtGui.QPushButton('Ok', self)
        ok_button.setAutoDefault(False)
        ok_button.clicked.connect(self.ok)

        cancel_button = QtGui.QPushButton('Cancel', self)
        cancel_button.setAutoDefault(False)
        cancel_button.clicked.connect(self.cancel)

        button_hbox.addStretch()
        button_hbox.addWidget(ok_button)
        button_hbox.addStretch()
        button_hbox.addWidget(cancel_button)
        button_hbox.addStretch()

        self.table_view = CalculationTable(self)
        self.res_slider.setValue((self.resolution-self.RES_MIN)/self.RES_INTERVAL)
        self.update_table()

        self.surf_check = QtGui.QCheckBox('calculate surface based cavities', self)
        self.surf_check.setChecked(True)
        self.center_check = QtGui.QCheckBox('calculate center based cavities', self)
        self.overwrite_check = QtGui.QCheckBox('overwrite existing results', self)
        self.exporthdf5_check = QtGui.QCheckBox('export results as HDF5 files', self)
        self.exporttext_check = QtGui.QCheckBox('export results as text files', self)
        self.exportdir_radio_input = QtGui.QRadioButton('export to the directory of the input files', self)
        self.exportdir_radio_config = QtGui.QRadioButton('export to %s' % config.Path.result_dir, self)

        self.exportdir_radio_input.setChecked(True)

        covalence_radii_by_element = self.__get_all_covalence_radii_by_element()
        self.radii_widget = RadiiWidget(covalence_radii_by_element, self.file_frame_dict, self)

        inner_layout.addLayout(res_hbox)
        inner_layout.addWidget(self.table_view)
        inner_layout.addWidget(self.surf_check)
        inner_layout.addWidget(self.center_check)
        inner_layout.addWidget(self.overwrite_check)
        inner_layout.addWidget(self.exporthdf5_check)
        inner_layout.addWidget(self.exporttext_check)
        inner_layout.addWidget(self.exportdir_radio_input)
        inner_layout.addWidget(self.exportdir_radio_config)

        hbox.addLayout(inner_layout)
        hbox.addWidget(self.radii_widget)

        vbox.addLayout(hbox)
        vbox.addLayout(button_hbox)

        self.setLayout(vbox)

    def __get_all_covalence_radii_by_element(self):
        covalence_radii_by_element, elements_by_frame, element_combinations = self.__read_atom_info()
        return covalence_radii_by_element

    def __get_elements_by_frame(self):
        covalence_radii_by_element, elements_by_frame, element_combinations = self.__read_atom_info()
        return elements_by_frame

    def __get_element_combinations(self):
        covalence_radii_by_element, elements_by_frame, element_combinations = self.__read_atom_info()
        return element_combinations

    def __read_atom_info(self):
        method = self.__read_atom_info.__func__
        for attr in ('covalence_radii_by_element', 'elements_by_frame', 'element_combinations'):
            if not hasattr(method, attr):
                setattr(method, attr, None)

        if (method.covalence_radii_by_element is None or
            method.elements_by_frame is None or
            method.element_combinations is None):
            radii = {}
            elements_by_frame = {}
            element_combinations = set()
            for filepath, frames in self.file_frame_dict.iteritems():
                elements_by_frame[filepath] = {}
                inputfile = file.File.open(filepath)
                if frames == (-1, ):
                    frames = range(inputfile.info.num_frames)
                for frame in frames:
                    atoms = inputfile.getatoms(frame)
                    current_radii = atoms.covalence_radii_by_element
                    current_elements = atoms.elements
                    radii.update(current_radii)
                    elements_by_frame[filepath][frame] = current_elements
                    element_combinations.add(tuple(current_elements))
            method.covalence_radii_by_element = radii
            method.elements_by_frame = elements_by_frame
        return (method.covalence_radii_by_element, method.elements_by_frame, method.element_combinations)

    def __update_cutoff_history(self):
        timestamp = datetime.datetime.now()
        user_cutoff_radii = self.radii_widget.get_input_from_custom_table()
        elements = self.__get_all_covalence_radii_by_element().keys()
        if not isinstance(user_cutoff_radii, collections.Iterable):
            user_cutoff_radii = dict((elem, user_cutoff_radii) for elem in elements)
        elements_by_frame = self.__get_elements_by_frame()
        new_history = []
        for filepath, frames in self.file_frame_dict.iteritems():
            filename = os.path.basename(filepath)
            file_elements = elements_by_frame[filepath]
            for frame in frames:
                elements = file_elements[frame]
                frame_cutoff_radii = dict((elem, user_cutoff_radii[elem]) for elem in elements)
                history_entry = HistoryEntry(filename, frame, timestamp, frame_cutoff_radii)
                new_history.append(history_entry)
        cutoff_history.extend(new_history)
        cutoff_history.save()

    def update_table(self):
        # get timestamps for selected frames for each file

        # surface based
        surface_ts = []
        center_ts = []
        for i, ts in enumerate(self.timestamps(center_based=False)):
            frames = (range(file.File.open(self.filenames[i]).info.num_frames)
                      if self.file_frame_dict[self.filenames[i]][0] == -1
                      else self.file_frame_dict[self.filenames[i]])
            surface_ts.append([])
            for frame in frames:
                surface_ts[i].append(ts[frame])

        # center based timestamps for the given frames
        center_ts = []
        for i, ts in enumerate(self.timestamps(center_based=True)):
            frames = (range(file.File.open(self.filenames[i]).info.num_frames) \
                      if self.file_frame_dict[self.filenames[i]][0] == -1 \
                      else self.file_frame_dict[self.filenames[i]])
            center_ts.append([])
            for frame in frames:
                center_ts[i].append(ts[frame])

        # reduce to a single value per file
        surface_ts = ["X" if "X" in ts else ts[0] for ts in surface_ts]
        center_ts = ["X" if "X" in ts else ts[0] for ts in center_ts]
        basenames = [os.path.basename(path) for path in self.filenames]
        frames = [str([frame + 1 for frame in self.file_frame_dict[f]])[1:-1] if not self.file_frame_dict[f][0] == -1 else 'all' for f in self.filenames]

        data_list = zip(basenames, surface_ts, center_ts, frames)

        # set table data
        header = ['dataset', 'surface based', 'center based', 'frames']
        table_model = TableModel(self, data_list, header)
        self.table_view.setModel(table_model)
        self.table_view.resizeColumnsToContents()

        # calculate table size to set its minimum size
        width = (self.table_view.model().columnCount(self.table_view) - 1) + self.table_view.verticalHeader().width()
        for i in range(self.table_view.model().columnCount(self.table_view)):
            width += self.table_view.columnWidth(i)
        self.table_view.setMinimumWidth(width)

        height = (self.table_view.model().rowCount(self.table_view) - 1) + self.table_view.horizontalHeader().height()
        for i in range(self.table_view.model().rowCount(self.table_view)):
            height += self.table_view.rowHeight(i)
        self.table_view.setMinimumHeight(height)

    def lineedit_return(self):
        try:
            self.resolution = int(self.lineedit.text())
            value = (self.resolution - self.RES_MIN) / self.RES_INTERVAL
            self.res_slider.setValue(value)
            self.update_table()
        except ValueError:
            pass

    def slider_changing(self, value):
        self.lineedit.setText(str(value * self.RES_INTERVAL + self.RES_MIN))

    def slider_released(self):
        self.resolution = self.res_slider.value() * self.RES_INTERVAL + self.RES_MIN
        self.update_table()

    def timestamps(self, center_based=False):
        return [self.control.calculation.calculatedframes(
                os.path.abspath(fn),
                self.resolution,
                not center_based,
                center_based).prettystrings()
                for fn in self.filenames]

    def ok(self):
        self.lineedit_return()
        self.__update_cutoff_history()
        self.done(QtGui.QDialog.Accepted)

    def cancel(self):
        self.done(QtGui.QDialog.Rejected)

    def calculation_settings(self):
        calc_settings = None
        while True:
            ok = self.exec_()
            if ok != QtGui.QDialog.Accepted:
                break
            try:
                cutoff_radii = self.radii_widget.get_input_from_custom_table()
                surface_based = self.surf_check.isChecked()
                center_based = self.center_check.isChecked()
                overwrite = self.overwrite_check.isChecked()
                exporthdf5 = self.exporthdf5_check.isChecked()
                exporttext = self.exporttext_check.isChecked()
                if self.exportdir_radio_config.isChecked():
                    exportdir = config.Path.result_dir
                else:
                    exportdir = None
                calc_settings = calculation.CalculationSettings(datasets=self.file_frame_dict,
                                                                resolution=self.resolution,
                                                                cutoff_radii=cutoff_radii,
                                                                domains=True,
                                                                surface_cavities=surface_based,
                                                                center_cavities=center_based,
                                                                recalculate=overwrite,
                                                                exporthdf5=exporthdf5,
                                                                exporttext=exporttext,
                                                                exportdir=exportdir)
                break
            except ValueError:
                pass

        return (calc_settings, ok)


class RadiiWidget(QtGui.QWidget):
    def __init__(self, radii, file_frame_dict, parent=None):
        super(RadiiWidget, self).__init__(parent)
        self._radii = radii
        self._file_frame_dict = file_frame_dict
        self._preferred_filenames_with_frames = dict((os.path.basename(filepath), frames)
                                                     for filepath, frames in self._file_frame_dict.iteritems())
        self._init_ui()
        self._init_cutoff_radii()

    def _init_ui(self):
        # self.setStyleSheet("background-color: white;")
        # self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        # Fixed Radio Button
        self.rb_fixed = QtGui.QRadioButton("Fixed Radius:")
        self.le_fixed = QtGui.QLineEdit()
        self.le_fixed.setMinimumWidth(150)
        self.le_fixed.setVisible(False)
        self.rb_fixed.toggled.connect(self.rb_fixed_clicked)

        # QStackedWidget le_fixed
        self.tmp1 = QtGui.QWidget()
        self.sw_fixed = QtGui.QStackedWidget()
        self.sw_fixed.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.sw_fixed.addWidget(self.le_fixed)
        self.sw_fixed.addWidget(self.tmp1)
        self.sw_fixed.setCurrentIndex(1)

        # Custom Radio Button + Table
        self.rb_custom = QtGui.QRadioButton("Custom:")
        self.tw_cutoff = QtGui.QTableWidget(len(self._radii), 2)
        self.tw_cutoff.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.tw_cutoff.setHorizontalHeaderLabels(("Covalent Radius", "Cutoff Radius"))
        self.tw_cutoff.setVerticalHeaderLabels(self._radii.keys())
        for i in range(len(self._radii)):
            self.tw_cutoff.setItem(i, 0, QtGui.QTableWidgetItem())
            self.tw_cutoff.item(i, 0).setText(str(self._radii.values()[i]))
            self.tw_cutoff.setCellWidget(i, 1, QtGui.QLineEdit())
        self.tw_cutoff.setShowGrid(True)
        self.rb_custom.toggled.connect(self.rb_custom_clicked)

        # Preset Combo Box
        self.cb_preset = LabeledComboBox("Preset")
        self.cb_preset.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        # History button
        self.pb_history = QtGui.QPushButton("History", self)
        self.pb_history.setMinimumWidth(0)
        self.pb_history.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.pb_history.clicked.connect(self.pb_history_clicked)

        # Preset save
        self.cb_preset_save = QtGui.QCheckBox("Save as Preset", self)
        self.te_preset_save = QtGui.QLineEdit()
        self.te_preset_save.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        self.la_main = QtGui.QGridLayout()
        self.la_main.setContentsMargins(0, 0, 0, 0)
        self.la_fixed = QtGui.QHBoxLayout()
        self.la_fixed.setContentsMargins(0, 0, 0, 0)
        self.la_custom = QtGui.QHBoxLayout()
        self.la_custom.setContentsMargins(0, 0, 0, 0)
        self.la_preset_save = QtGui.QHBoxLayout()
        self.la_preset_save.setContentsMargins(0, 0, 0, 0)

        self.la_fixed.addWidget(self.rb_fixed)
        self.la_fixed.addWidget(self.sw_fixed)
        self.la_main.addLayout(self.la_fixed, 0, 0, 1, 2)
        self.la_custom.addWidget(self.rb_custom)
        self.la_main.addLayout(self.la_custom, 1, 0, 1, 2)
        self.la_main.addWidget(self.tw_cutoff, 2, 0, 1, 2)
        self.la_main.addWidget(self.cb_preset, 3, 0, 1, 1)
        self.la_main.addWidget(self.pb_history, 3, 1, 1, 1)
        self.la_preset_save.addWidget(self.cb_preset_save)
        self.la_preset_save.addWidget(self.te_preset_save)
        self.la_main.addLayout(self.la_preset_save, 4, 0, 1, 2)

        self.setLayout(self.la_main)

        self.rb_fixed.toggle()

    def _init_cutoff_radii(self, cutoff_radii=None):
        elements = self._radii.keys()
        if cutoff_radii is None:
            filtered_history = cutoff_history.filtered_history(elements, preferred_filenames_with_frames=
                                                               self._preferred_filenames_with_frames)
            if not filtered_history:
                cutoff_radii = config.Computation.std_cutoff_radius
            else:
                cutoff_radii = filtered_history[0].radii
        if not isinstance(cutoff_radii, collections.Iterable):
            cutoff_radii = dict((elem, float(cutoff_radii)) for elem in elements)
        # Check if all cutoff radii are equal
        if len(set(cutoff_radii.values())) == 1:
            self.rb_fixed.toggle()
            self.le_fixed.setText(str(cutoff_radii.values()[0]))
        else:
            self.rb_custom.toggle()
            for i, elem in enumerate(self._radii):
                self.tw_cutoff.cellWidget(i, 1).setText(str(cutoff_radii[elem]))

    def rb_fixed_clicked(self):
        self.sw_fixed.setCurrentIndex(0)

    def rb_custom_clicked(self):
        self.sw_fixed.setCurrentIndex(1)

    def pb_history_clicked(self):
        cutoff_history_dialog = CutoffHistoryDialog(self, self._radii.keys(), self._preferred_filenames_with_frames)
        return_value = cutoff_history_dialog.exec_()
        if return_value == QtGui.QDialog.Rejected:
            return
        self._init_cutoff_radii(cutoff_history_dialog.selected_radii)

    def get_input_from_custom_table(self):
        if self.rb_fixed.isChecked() and hasattr(self, "le_fixed"):
            try:
                radius_as_text = self.le_fixed.text()
                radius = float(radius_as_text)
                return radius
            except ValueError:
                message = QtGui.QMessageBox()
                message.setStandardButtons(QtGui.QMessageBox.Ok)
                message.setText("Incorrect input: {}".format(radius_as_text))
                message.exec_()
                raise

        if self.rb_custom.isChecked():
            elem_to_cutoff_radius = {}
            for i, elem in enumerate(self._radii):
                try:
                    current_radius_as_text = self.tw_cutoff.cellWidget(i, 1).text()
                    current_radius = float(current_radius_as_text)
                    elem_to_cutoff_radius[elem] = current_radius
                except ValueError:
                    message = QtGui.QMessageBox()
                    message.setStandardButtons(QtGui.QMessageBox.Ok)
                    message.setText("Incorrect input: {}".format(current_radius_as_text))
                    message.exec_()
                    raise
            return elem_to_cutoff_radius
