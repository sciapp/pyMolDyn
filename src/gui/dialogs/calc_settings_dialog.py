# -*- coding: utf-8 -*-


from gui.dialogs.util.calc_table import CalculationTable, TableModel
from core import calculation
from core import file
import os.path
import itertools as it
from config.configuration import config
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

        print self.file_frame_dict

        self.init_gui()
        self.setWindowTitle("Calculation Settings")

    def init_gui(self):

        hbox            = QtGui.QHBoxLayout()
        vbox            = QtGui.QVBoxLayout()
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

        vbox.addLayout(res_hbox)
        vbox.addWidget(self.table_view)
        vbox.addWidget(self.surf_check)
        vbox.addWidget(self.center_check)
        vbox.addWidget(self.overwrite_check)
        vbox.addWidget(self.exporthdf5_check)
        vbox.addWidget(self.exporttext_check)
        vbox.addWidget(self.exportdir_radio_input)
        vbox.addWidget(self.exportdir_radio_config)

        vbox.addLayout(button_hbox)
        hbox.addLayout(vbox)

        covalence_radii_by_element = self.__get_all_covalence_radii_by_element()
        radii_widget = RadiiWidget(covalence_radii_by_element, self)

        hbox.addWidget(radii_widget)

        self.setLayout(hbox)

    def __get_all_covalence_radii_by_element(self):
        radii = {}
        for filepath, frames in self.file_frame_dict.iteritems():
            inputfile = file.File.open(filepath)
            if frames == (-1, ):
                frames = range(inputfile.info.num_frames)
            for frame in frames:
                current_radii = inputfile.getatoms(frame).covalence_radii_by_element
                radii.update(current_radii)
        return radii

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
            #print 'Enter a valid number'

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
        self.done(QtGui.QDialog.Accepted)

    def cancel(self):
        self.done(QtGui.QDialog.Rejected)

    def calculation_settings(self):
        ok = self.exec_()
        surface_based = self.surf_check.isChecked()
        center_based = self.center_check.isChecked()
        overwrite = self.overwrite_check.isChecked()
        exporthdf5 = self.exporthdf5_check.isChecked()
        exporttext = self.exporttext_check.isChecked()
        if self.exportdir_radio_config.isChecked():
            exportdir = config.Path.result_dir
        else:
            exportdir = None

        return (calculation.CalculationSettings(datasets=self.file_frame_dict,
                                                resolution=self.resolution,
                                                domains=True,
                                                surface_cavities=surface_based,
                                                center_cavities=center_based,
                                                recalculate=overwrite,
                                                exporthdf5=exporthdf5,
                                                exporttext=exporttext,
                                                exportdir=exportdir),
                ok)


class RadiiWidget(QtGui.QWidget):
    def __init__(self, radii, parent=None):

        self.radii = radii

        super(RadiiWidget, self).__init__(parent)

        self.createCovalentTableBox()
        self.createMenuBox()

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.covalentTableBox, 0, 0)
        mainLayout.addWidget(self.menuBox, 1, 0)

        self.setLayout(mainLayout)


    def createMenuBox(self):

        self.menuBox = QtGui.QGroupBox("Menu")
        layout = QtGui.QGridLayout()

        #Fixed Radio Button
        self.fixed = QtGui.QRadioButton("Fixed Radius:")
        self.fixed.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.radiusEdit = QtGui.QLineEdit()
        self.radiusEdit.setMinimumWidth(150)
        self.radiusEdit.setVisible(False)
        self.radiusEdit.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.fixed.toggled.connect(self.fixed_clicked)

        #Custom Radio Button
        self.custom = QtGui.QRadioButton("Custom:")
        self.custom.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.createCustomTable()
        self.customTable.setVisible(False)
        self.custom.toggled.connect(self.custom_clicked)

        #QStackedWidget customTable
        self.tmp1 = QtGui.QWidget()
        self.stackedWidgetCustomTable = QtGui.QStackedWidget()
        self.stackedWidgetCustomTable.addWidget(self.customTable)
        self.stackedWidgetCustomTable.addWidget(self.tmp1)
        self.stackedWidgetCustomTable.setCurrentIndex(1)

        #QStrackedWidget radiusEdit
        self.tmp2 = QtGui.QWidget()
        self.stackedWidgetRadiusEdit = QtGui.QStackedWidget()
        self.stackedWidgetRadiusEdit.addWidget(self.radiusEdit)
        self.stackedWidgetRadiusEdit.addWidget(self.tmp2)
        self.stackedWidgetRadiusEdit.setCurrentIndex(1)

        layout.addWidget(self.fixed, 0, 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.stackedWidgetRadiusEdit, 0, 1, QtCore.Qt.AlignTop)
        layout.addWidget(self.custom, 1, 0, 1, 2, QtCore.Qt.AlignTop)
        layout.addWidget(self.stackedWidgetCustomTable, 2, 0, 1, 2, QtCore.Qt.AlignTop)

        self.menuBox.setLayout(layout)


    def fixed_clicked(self):

        self.stackedWidgetCustomTable.setCurrentIndex(1)
        self.stackedWidgetRadiusEdit.setCurrentIndex(0)


    def custom_clicked(self):

        self.stackedWidgetCustomTable.setCurrentIndex(0)
        self.stackedWidgetRadiusEdit.setCurrentIndex(1)


    def createCovalentTableBox(self):

        self.covalentTableBox = QtGui.QGroupBox("Table")
        layoutTableBox = QtGui.QGridLayout()
        covalentTable = QtGui.QTableWidget(1, len(self.radii))
        covalentTable.setMinimumHeight(0)
        covalentTable.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
        covalentTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        covalentTable.setHorizontalHeaderLabels(self.radii.keys())
        covalentTable.setVerticalHeaderLabels(("Covalent Radius", ))

        for i in range(len(self.radii)):
            covalentTable.setItem(0, i, QtGui.QTableWidgetItem())
            covalentTable.item(0, i).setText(str(self.radii.values()[i]))
        covalentTable.setShowGrid(True)

        layoutTableBox.addWidget(covalentTable, 0, 0)
        self.covalentTableBox.setLayout(layoutTableBox)


    def __get_input_from_CustomTable(self):

        if self.fixed.isChecked() and hasattr(self, "radiusEdit"):
            try:
                radius = self.radiusEdit.text()
                float(radius)
                return radius
            except ValueError:
                message = QtGui.QMessageBox()
                message.setStandardButtons(QtGui.QMessageBox.Ok)
                message.setText("Incorrect Entry")
                message.exec_()

        if self.custom.isChecked():
            customList = []
            for i in range(len(self.radii)):
                try:
                    custom = self.customTable.cellWidget(0, i).text()
                    float(custom)
                    customList.append(custom)
                except ValueError:
                    message = QtGui.QMessageBox()
                    message.setStandardButtons(QtGui.QMessageBox.Ok)
                    message.setText("Incorrect Entry")
                    message.exec_()
                    break
            return customList


    def createCustomTable(self):

        self.customTable = QtGui.QTableWidget(1, len(self.radii))
        self.customTable.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
        self.customTable.setHorizontalHeaderLabels(self.radii.keys())
        self.customTable.setVerticalHeaderLabels(("Custom Radius", ))

        for i in range(len(self.radii)):
            self.customTable.setCellWidget(0, i, QtGui.QLineEdit())
        self.customTable.setShowGrid(True)
