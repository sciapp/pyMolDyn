# -*- coding: utf-8 -*-
from gui.dialogs.util.calc_table import CalculationTable, TableModel
from gui.dialogs.util.framechooser import LabeledFrameChooser
from core import calculation
import os.path
from config.configuration import config
from PySide import QtGui, QtCore

class CalculationSettingsDialog(QtGui.QDialog):

    FRAME_MIN = 32
    FRAME_MAX = 1024

    def __init__(self, parent, filenames):
        QtGui.QDialog.__init__(self, parent)

        self.init_gui(filenames)
        self.setWindowTitle("Calculation Settings")
    
    def init_gui(self, filenames):

        vbox            = QtGui.QVBoxLayout() 
        button_hbox     = QtGui.QHBoxLayout() 
        res_hbox        = QtGui.QHBoxLayout()
        self.resolution = config.Computation.std_resolution

        self.filenames  = filenames
        self.basenames  = [os.path.basename(path) for path in filenames]
        self.res_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.res_slider.setMinimum(self.FRAME_MIN)
        self.res_slider.setMaximum(self.FRAME_MAX)
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

        if len(self.filenames) == 1:
            self.n_frames    = calculation.count_frames(filenames[0])
            if not self.n_frames == 1:
                calc_frames = calculation.calculated_frames(filenames[0], self.resolution)
                self.frame_chooser = LabeledFrameChooser(self, 1, self.n_frames, calc_frames, 'Frame')
                self.frame_chooser.value_changed.connect(self.update_table)
        
        self.table_view = CalculationTable(self)
        self.res_slider.setValue(self.resolution)
        self.update_table()

        self.surf_check = QtGui.QCheckBox('calculate surface based cavities', self)
        self.surf_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.center_check = QtGui.QCheckBox('calculate center based cavities', self)

        vbox.addLayout(res_hbox)
        vbox.addWidget(self.table_view)
        vbox.addWidget(self.surf_check)
        vbox.addWidget(self.center_check)
        if len(self.filenames) == 1 and not self.n_frames == 1:
            vbox.addWidget(self.frame_chooser)
        vbox.addLayout(button_hbox)
        self.setLayout(vbox)

    def update_table(self):
        if len(self.filenames) == 1:
            if not self.n_frames == 1:
                sel = self.frame_chooser.value()
            else:
                sel = [1]
        else:
            sel = [-1]
        data_list  = [(os.path.basename(filename),
                        calculation.timestamp(filename, self.resolution, center_based=True, frames=sel),
                        calculation.timestamp(filename, self.resolution, center_based=False, frames=sel))
                        for filename in enumerate(self.filenames)]

        header = ['dataset', 'surface based', 'center based']
        table_model = TableModel(self, data_list, header)
        self.table_view.setModel(table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

    def update_frame_chooser(self, resolution):
        if len(self.filenames) == 1 and self.n_frames != 1:
            calc_frames = calculation.calculated_frames(self.filenames[0], resolution)
            self.frame_chooser.set_calculated_frames(calc_frames)

    def lineedit_return(self):
        try:
            self.resolution = int(self.lineedit.text())
            self.res_slider.setValue(self.resolution)
            self.update_table()
            self.update_frame_chooser(self.resolution)
        except ValueError:
            pass
            #print 'Enter a valid number'

    def slider_changing(self, resolution):
        self.lineedit.setText(str(resolution))

    def slider_released(self):
        self.resolution = self.res_slider.value()
        self.update_table()
        self.update_frame_chooser(self.resolution)

    def ok(self):
        self.done(QtGui.QDialog.Accepted)

    def cancel(self):
        self.done(QtGui.QDialog.Rejected)

    def calculation_settings(self):
        ok = self.exec_()
        if len(self.filenames) > 1:
            frames = [-1]
        elif self.n_frames == 1:
            frames = [1]
        else:
            frames = self.frame_chooser.value()
        surface_based = self.surf_check.checkState() == QtCore.Qt.CheckState.Checked
        center_based = self.center_check.checkState() == QtCore.Qt.CheckState.Checked
        return calculation.CalculationSettings(self.filenames,
                                               self.res_slider.value(),
                                               frames,
                                               surface_based,
                                               center_based), \
                                               ok
