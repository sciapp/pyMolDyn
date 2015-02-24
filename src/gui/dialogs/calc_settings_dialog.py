# -*- coding: utf-8 -*-


from gui.dialogs.util.calc_table import CalculationTable, TableModel
from core import calculation
import os.path
from config.configuration import config
from PySide import QtGui, QtCore


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
        self.surf_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.center_check = QtGui.QCheckBox('calculate center based cavities', self)
        self.overwrite_check = QtGui.QCheckBox('overwrite existing results', self)

        vbox.addLayout(res_hbox)
        vbox.addWidget(self.table_view)
        vbox.addWidget(self.surf_check)
        vbox.addWidget(self.center_check)
        vbox.addWidget(self.overwrite_check)

        vbox.addLayout(button_hbox)
        self.setLayout(vbox)

    def update_table(self):
        # get timestamps for selected frames for each file
        surface_ts = [[ts[s] for s in self.file_frame_dict[self.filenames[i]]] for i, ts in enumerate(self.timestamps(center_based=False))]
        center_ts = [[ts[s] for s in self.file_frame_dict[self.filenames[i]]] for i, ts in enumerate(self.timestamps(center_based=True))]
        # reduce to a single value per file
        surface_ts = ["X" if "X" in ts else ts[0] for ts in surface_ts]
        center_ts = ["X" if "X" in ts else ts[0] for ts in center_ts]
        basenames = [os.path.basename(path) for path in self.filenames]
        frames = [str(self.file_frame_dict[f])[1:-1] if not self.file_frame_dict[f][0] == -1 else 'all' for f in self.filenames]

        data_list = zip(basenames, surface_ts, center_ts, frames)

        header = ['dataset', 'surface based', 'center based', 'frames']
        table_model = TableModel(self, data_list, header)
        self.table_view.setModel(table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

    def lineedit_return(self):
        try:
            self.resolution = int(self.lineedit.text())
            self.res_slider.setValue(self.resolution)
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
        surface_based = self.surf_check.checkState() == QtCore.Qt.CheckState.Checked
        center_based = self.center_check.checkState() == QtCore.Qt.CheckState.Checked
        overwrite = self.overwrite_check.checkState() == QtCore.Qt.CheckState.Checked

        print  self.file_frame_dict, \
               self.resolution, \
               True, \
               surface_based, \
               center_based, \
               overwrite, \
               ok

#        return calculation.CalculationSettings(self.file_frame_dict,
#                                               self.resolution,
#                                               True,
#                                               surface_based,
#                                               center_based,
#                                               overwrite), \
#                                               ok
