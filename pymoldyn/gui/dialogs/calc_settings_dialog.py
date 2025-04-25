import collections
import collections.abc
import datetime
import itertools as it
import os.path
import re

from PySide6 import QtCore, QtWidgets

from ...config.configuration import config
from ...config.cutoff_history import HistoryEntry, cutoff_history
from ...config.cutoff_presets import Preset, cutoff_presets
from ...core import calculation, file
from ..cutoff_preset_combobox import CutoffPresetComboBox
from ..cutoff_table_widget import CutoffTableWidget
from .cutoff_history_dialog import CutoffHistoryDialog
from .util.calc_table import CalculationTable, TableModel


class CalculationSettingsDialog(QtWidgets.QDialog):

    RES_MIN = 32
    RES_MAX = 1024
    RES_INTERVAL = 32

    def __init__(self, parent, file_frame_dict):
        super().__init__(parent)

        self.control = parent.control
        self.resolution = config.Computation.std_resolution
        self.filenames = [f for f in file_frame_dict.keys()]
        self.file_frame_dict = file_frame_dict

        self.init_gui()
        self.setWindowTitle("Calculation Settings")

    def init_gui(self):

        vbox = QtWidgets.QVBoxLayout()
        hbox = QtWidgets.QHBoxLayout()
        inner_layout = QtWidgets.QVBoxLayout()
        button_hbox = QtWidgets.QHBoxLayout()
        res_hbox = QtWidgets.QHBoxLayout()

        self.res_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.res_slider.setMinimum(0)
        self.res_slider.setMaximum((self.RES_MAX - self.RES_MIN) / self.RES_INTERVAL)
        # self.res_slider.setTickInterval(1)
        # self.res_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.res_slider.valueChanged[int].connect(self.slider_changing)
        self.res_slider.sliderReleased.connect(self.slider_released)

        self.lineedit = QtWidgets.QLineEdit(self)
        self.lineedit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.lineedit.setMinimumSize(30, 1)
        self.lineedit.setMaximumSize(40, 40)
        self.lineedit.returnPressed.connect(self.lineedit_return)

        res_hbox.addWidget(QtWidgets.QLabel("resolution:", self))
        res_hbox.addWidget(self.res_slider)
        res_hbox.addWidget(self.lineedit)

        # set font
        #        font = QFont("Courier New", 14)
        #        table_view.setFont(font)
        # set column width to fit contents (set font first!)
        # enable sortingq
        #        table_view.setSortingEnabled(True)

        ok_button = QtWidgets.QPushButton("Ok", self)
        ok_button.setAutoDefault(False)
        ok_button.clicked.connect(self.ok)

        cancel_button = QtWidgets.QPushButton("Cancel", self)
        cancel_button.setAutoDefault(False)
        cancel_button.clicked.connect(self.cancel)

        button_hbox.addStretch()
        button_hbox.addWidget(ok_button)
        button_hbox.addStretch()
        button_hbox.addWidget(cancel_button)
        button_hbox.addStretch()

        self.table_view = CalculationTable(self)
        self.res_slider.setValue((self.resolution - self.RES_MIN) / self.RES_INTERVAL)
        self.update_table()

        def create_separator():
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Sunken)
            line.setLineWidth(1)
            return line

        self.surf_check = QtWidgets.QCheckBox("calculate surface based cavities", self)
        self.surf_check.setChecked(True)
        self.center_check = QtWidgets.QCheckBox("calculate center based cavities", self)
        self.gyration_tensor_check = QtWidgets.QCheckBox("calculate gyration tensor parameters", self)
        self.gyration_tensor_check.setToolTip("squared_gyration_radius, asphericity, acylindricity, anisotropy")
        self.overwrite_check = QtWidgets.QCheckBox("overwrite existing results", self)
        self.exporthdf5_check = QtWidgets.QCheckBox("export results as HDF5 files", self)
        self.exporttext_check = QtWidgets.QCheckBox("export results as text files", self)
        self.exportsingletext_check = QtWidgets.QCheckBox("export results as single text file", self)
        self.exportdir_radio_input = QtWidgets.QRadioButton("export to the directory of the input files", self)
        self.exportdir_radio_config = QtWidgets.QRadioButton("export to %s" % config.Path.result_dir, self)

        self.exportdir_radio_input.setChecked(True)

        self.exportdir_radio_group = QtWidgets.QButtonGroup(self)
        self.exportdir_radio_group.addButton(self.exportdir_radio_input)
        self.exportdir_radio_group.addButton(self.exportdir_radio_config)

        covalence_radii_by_element = self.__get_all_covalence_radii_by_element()
        self.radii_widget = RadiiWidget(covalence_radii_by_element, self.file_frame_dict, self)

        inner_layout.addLayout(res_hbox)
        inner_layout.addWidget(self.table_view)
        inner_layout.addWidget(self.surf_check)
        inner_layout.addWidget(self.center_check)
        inner_layout.addWidget(self.gyration_tensor_check)
        inner_layout.addWidget(create_separator())
        inner_layout.addWidget(self.overwrite_check)
        inner_layout.addWidget(self.exporthdf5_check)
        inner_layout.addWidget(self.exporttext_check)
        inner_layout.addWidget(self.exportsingletext_check)
        inner_layout.addWidget(create_separator())
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
        for attr in (
            "covalence_radii_by_element",
            "elements_by_frame",
            "element_combinations",
        ):
            if not hasattr(method, attr):
                setattr(method, attr, None)

        if (
            method.covalence_radii_by_element is None
            or method.elements_by_frame is None
            or method.element_combinations is None
        ):

            radii = {}
            elements_by_frame = {}
            element_combinations = set()
            for filepath, frames in self.file_frame_dict.items():
                elements_by_frame[filepath] = {}
                inputfile = file.File.open(filepath)
                if frames == (-1,):
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
        return (
            method.covalence_radii_by_element,
            method.elements_by_frame,
            method.element_combinations,
        )

    def __update_cutoff_history(self):
        timestamp = datetime.datetime.now()
        user_cutoff_radii = self.radii_widget.cutoff_radii
        elements = self.__get_all_covalence_radii_by_element().keys()
        if not isinstance(user_cutoff_radii, collections.abc.Iterable):
            user_cutoff_radii = dict((elem, user_cutoff_radii) for elem in elements)
        elements_by_frame = self.__get_elements_by_frame()
        new_history = []
        for filepath, frames in self.file_frame_dict.items():
            filename = os.path.basename(filepath)
            file_elements = elements_by_frame[filepath]
            for frame in frames:
                elements = file_elements[frame]
                frame_cutoff_radii = dict((elem, user_cutoff_radii[elem]) for elem in elements)
                history_entry = HistoryEntry(filename, frame, timestamp, frame_cutoff_radii)
                new_history.append(history_entry)
        cutoff_history.extend(new_history)
        cutoff_history.save()

    def __update_cutoff_presets(self):
        save_preset_name = self.radii_widget.save_preset_name
        if save_preset_name is not None:
            user_cutoff_radii = self.radii_widget.cutoff_radii
            cutoff_presets.add(Preset(save_preset_name, user_cutoff_radii))
            cutoff_presets.save()

    def update_table(self):
        # get timestamps for selected frames for each file

        # surface based
        surface_ts = []
        center_ts = []
        for i, ts in enumerate(self.timestamps(center_based=False)):
            frames = (
                range(file.File.open(self.filenames[i]).info.num_frames)
                if self.file_frame_dict[self.filenames[i]][0] == -1
                else self.file_frame_dict[self.filenames[i]]
            )
            surface_ts.append([])
            for frame in frames:
                ts, temp = it.tee(ts)
                surface_ts[i].append(list(temp)[frame])

        # center based timestamps for the given frames
        center_ts = []
        for i, ts in enumerate(self.timestamps(center_based=True)):
            frames = (
                range(file.File.open(self.filenames[i]).info.num_frames)
                if self.file_frame_dict[self.filenames[i]][0] == -1
                else self.file_frame_dict[self.filenames[i]]
            )
            center_ts.append([])
            for frame in frames:
                ts, temp = it.tee(ts)
                center_ts[i].append(list(temp)[frame])

        # reduce to a single value per file
        surface_ts = ["X" if "X" in ts else ts[0] for ts in surface_ts]
        center_ts = ["X" if "X" in ts else ts[0] for ts in center_ts]
        basenames = [os.path.basename(path) for path in self.filenames]
        frames = [
            (
                str([frame + 1 for frame in self.file_frame_dict[f]])[1:-1]
                if not self.file_frame_dict[f][0] == -1
                else "all"
            )
            for f in self.filenames
        ]

        data_list = zip(basenames, surface_ts, center_ts, frames)

        # set table data
        header = ["dataset", "surface based", "center based", "frames"]
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
        return [
            self.control.calculation.calculatedframes(
                file.get_abspath(fn), self.resolution, not center_based, center_based
            ).prettystrings()
            for fn in self.filenames
        ]

    def ok(self):
        self.lineedit_return()
        self.__update_cutoff_history()
        self.__update_cutoff_presets()
        self.done(QtWidgets.QDialog.Accepted)

    def cancel(self):
        self.done(QtWidgets.QDialog.Rejected)

    def calculation_settings(self):
        calc_settings = None
        while True:
            ok = self.exec_()
            if ok != QtWidgets.QDialog.Accepted:
                break
            try:
                cutoff_radii = self.radii_widget.cutoff_radii
                surface_based = self.surf_check.isChecked()
                center_based = self.center_check.isChecked()
                gyration_tensor = self.gyration_tensor_check.isChecked()
                overwrite = self.overwrite_check.isChecked()
                exporthdf5 = self.exporthdf5_check.isChecked()
                exporttext = self.exporttext_check.isChecked()
                exportsingletext = self.exportsingletext_check.isChecked()
                if self.exportdir_radio_config.isChecked():
                    exportdir = os.path.expanduser(config.Path.result_dir)
                else:
                    exportdir = None
                calc_settings = calculation.CalculationSettings(
                    datasets=self.file_frame_dict,
                    resolution=self.resolution,
                    cutoff_radii=cutoff_radii,
                    domains=True,
                    surface_cavities=surface_based,
                    center_cavities=center_based,
                    gyration_tensor=gyration_tensor,
                    recalculate=overwrite,
                    exporthdf5=exporthdf5,
                    exporttext=exporttext,
                    exportsingletext=exportsingletext,
                    exportdir=exportdir,
                )
                break
            except ValueError:
                pass

        return (calc_settings, ok)


class RadiiWidget(QtWidgets.QWidget):
    class RadiiType:
        FIXED = 0
        CUSTOM = 1

    def __init__(self, radii, file_frame_dict, parent=None):
        super().__init__(parent)
        self._radii = radii
        self._file_frame_dict = file_frame_dict
        self._preferred_filenames_with_frames = dict(
            (os.path.basename(filepath), frames) for filepath, frames in self._file_frame_dict.items()
        )
        self._discard_preset_choice_on_next_rb_click = True  # Default value is True
        self._selected_radii_type = RadiiWidget.RadiiType.FIXED
        self._init_ui()
        self._init_cutoff_radii()

    def _init_ui(self):
        # Fixed Radio Button
        self.rb_fixed = QtWidgets.QRadioButton("Fixed Radius:")
        self.le_fixed = QtWidgets.QLineEdit()
        self.le_fixed.setMinimumWidth(150)
        self.le_fixed.setVisible(False)
        self.le_fixed.textEdited.connect(self.le_fixed_text_edited)
        self.rb_fixed.clicked.connect(self.rb_fixed_clicked)

        # QStackedWidget le_fixed
        self.tmp1 = QtWidgets.QWidget()
        self.sw_fixed = QtWidgets.QStackedWidget()
        self.sw_fixed.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.sw_fixed.addWidget(self.le_fixed)
        self.sw_fixed.addWidget(self.tmp1)
        self.sw_fixed.setCurrentIndex(1)

        # Custom Radio Button + Table
        self.rb_custom = QtWidgets.QRadioButton("Custom:")
        self.tw_cutoff = CutoffTableWidget(self._radii)
        self.tw_cutoff.text_edited.connect(self.tw_cutoff_text_edited)
        self.rb_custom.clicked.connect(self.rb_custom_clicked)

        # Preset Combo Box
        self.cb_preset = CutoffPresetComboBox()
        self.cb_preset.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.cb_preset.preset_selected.connect(self.cb_preset_selected)

        # History button
        self.pb_history = QtWidgets.QPushButton("History", self)
        self.pb_history.setMinimumWidth(0)
        self.pb_history.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.pb_history.setAutoDefault(False)
        self.pb_history.clicked.connect(self.pb_history_clicked)
        if (
            len(
                cutoff_history.filtered_history(
                    self._radii.keys(),
                    preferred_filenames_with_frames=self._preferred_filenames_with_frames,
                )
            )
            == 0
        ):
            self.pb_history.setVisible(False)

        # Preset save
        self.cb_preset_save = QtWidgets.QCheckBox("Save as Preset", self)
        self.le_preset_save = QtWidgets.QLineEdit()
        self.le_preset_save.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.le_preset_save.textChanged.connect(self.le_preset_save_changed)

        self.la_main = QtWidgets.QGridLayout()
        self.la_main.setContentsMargins(0, 0, 0, 0)
        self.la_fixed = QtWidgets.QHBoxLayout()
        self.la_fixed.setContentsMargins(0, 0, 0, 0)
        self.la_custom = QtWidgets.QHBoxLayout()
        self.la_custom.setContentsMargins(0, 0, 0, 0)
        self.la_preset_save = QtWidgets.QHBoxLayout()
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
        self.la_preset_save.addWidget(self.le_preset_save)
        self.la_main.addLayout(self.la_preset_save, 4, 0, 1, 2)

        self.setLayout(self.la_main)

        self.rb_fixed.click()

    def _init_cutoff_radii(self, cutoff_radii=None):
        elements = self._radii.keys()
        if cutoff_radii is None:
            filtered_history = cutoff_history.filtered_history(
                elements,
                preferred_filenames_with_frames=self._preferred_filenames_with_frames,
            )
            if not filtered_history:
                cutoff_radii = config.Computation.std_cutoff_radius
            else:
                cutoff_radii = filtered_history[0].radii
        self.cutoff_radii = cutoff_radii

    def rb_fixed_clicked(self):
        self.sw_fixed.setCurrentIndex(0)
        if self._selected_radii_type != RadiiWidget.RadiiType.FIXED and self._discard_preset_choice_on_next_rb_click:
            self.cb_preset.discard_preset_choice()
            self._selected_radii_type = RadiiWidget.RadiiType.FIXED
        self._discard_preset_choice_on_next_rb_click = True

    def rb_custom_clicked(self):
        self.sw_fixed.setCurrentIndex(1)
        if self._selected_radii_type != RadiiWidget.RadiiType.CUSTOM and self._discard_preset_choice_on_next_rb_click:
            self.cb_preset.discard_preset_choice()
            self._selected_radii_type = RadiiWidget.RadiiType.CUSTOM
        self._discard_preset_choice_on_next_rb_click = True

    def le_fixed_text_edited(self):
        self.cb_preset.discard_preset_choice()

    def tw_cutoff_text_edited(self):
        self.cb_preset.discard_preset_choice()
        self.rb_custom.click()
        self.cb_preset.discard_preset_choice()

    def pb_history_clicked(self):
        cutoff_history_dialog = CutoffHistoryDialog(self, self._radii.keys(), self._preferred_filenames_with_frames)
        return_value = cutoff_history_dialog.exec_()
        if return_value == QtWidgets.QDialog.Rejected:
            return
        self._init_cutoff_radii(cutoff_history_dialog.selected_radii)

    def le_preset_save_changed(self, text):
        self.cb_preset_save.setChecked(text.strip() != "")

    def cb_preset_selected(self, selected_preset):
        self.cutoff_radii = selected_preset.radii

    @property
    def save_preset_name(self):
        if not self.cb_preset_save.isChecked():
            return None
        preset_name = self.le_preset_save.text().strip()
        if not re.match("[a-zA-Z0-9_]+", preset_name):
            message = QtWidgets.QMessageBox()
            message.setStandardButtons(QtWidgets.QMessageBox.Ok)
            message.setText(
                "{} is not valid preset name. Only A-Z, a-z, 0-9 and _ are valid characters".format(preset_name)
            )
            message.exec_()
            return None
        return preset_name

    @property
    def cutoff_radii(self):
        if self.rb_fixed.isChecked() and hasattr(self, "le_fixed"):
            try:
                radius_as_text = self.le_fixed.text()
                radius = float(radius_as_text)
                return radius
            except ValueError:
                message = QtWidgets.QMessageBox()
                message.setStandardButtons(QtWidgets.QMessageBox.Ok)
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
                    message = QtWidgets.QMessageBox()
                    message.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    message.setText("Incorrect input: {}".format(current_radius_as_text))
                    message.exec_()
                    raise
            return elem_to_cutoff_radius

    @cutoff_radii.setter
    def cutoff_radii(self, cutoff_radii):
        elements = self._radii.keys()
        if not isinstance(cutoff_radii, collections.abc.Iterable):
            cutoff_radii = dict((elem, float(cutoff_radii)) for elem in elements)
        # Check if all cutoff radii are equal
        if len(set(cutoff_radii.values())) == 1:
            self._discard_preset_choice_on_next_rb_click = False
            self.rb_fixed.click()
            self.le_fixed.setText(str(list(cutoff_radii.values())[0]))
        else:
            self._discard_preset_choice_on_next_rb_click = False
            self.rb_custom.click()
            for i, elem in enumerate(self._radii):
                self.tw_cutoff.cellWidget(i, 1).setText(str(cutoff_radii[elem]))
