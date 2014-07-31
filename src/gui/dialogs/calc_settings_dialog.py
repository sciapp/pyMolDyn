# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from gui.dialogs.util.calc_table import *
from gui.dialogs.util.framechooser import LabeledFrameChooser
import calculation
import os.path 


class CalculationSettingsDialog(QtGui.QDialog):

    FRAME_MIN = 32
    FRAME_MAX = 1024

    def __init__(self, parent=None, filenames=[]):
        QtGui.QDialog.__init__(self, parent)

        self.init_gui(filenames)
        self.setWindowTitle("Calculation Settings")
    
    def init_gui(self, filenames):

        vbox            = QtGui.QVBoxLayout() 
        button_hbox     = QtGui.QHBoxLayout() 
        res_hbox        = QtGui.QHBoxLayout()

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
        # enable sorting
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
        
        resolution = 64
        if len(self.filenames) == 1:
            n_frames    = calculation.count_frames(filenames[0])
            calc_frames = calculation.calculated_frames(filenames[0], resolution)
            self.frame_chooser = LabeledFrameChooser(self, 1, n_frames, calc_frames, 'Frame')
        
        self.table_view = CalculationTable(self)
        self.update_table(resolution)
        self.res_slider.setValue(resolution)
        
        self.checkbox = QtGui.QCheckBox('calculate center based cavities', self)

        vbox.addLayout(res_hbox)
        vbox.addWidget(self.table_view)
        vbox.addWidget(self.checkbox)
        if len(self.filenames) == 1:
            vbox.addWidget(self.frame_chooser)
        vbox.addLayout(button_hbox)
        self.setLayout(vbox)

    def update_table(self, resolution):
        if len(self.filenames) == 1:
            sel = self.frame_chooser.value()
            #do while
            j = 0
            data_list  = [(filename, self.timestamp(self.filenames[i], resolution, center_based=True), self.timestamp(self.filenames[i], resolution, center_based=False)) for i, filename in enumerate(self.basenames)]
            j += 1
            while j < len(sel) and not calculation.calculated(filename, sel[j], resolution, False):
                data_list  = [(filename, self.timestamp(self.filenames[i], resolution, center_based=True), self.timestamp(self.filenames[i], resolution, center_based=False)) for i, filename in enumerate(self.basenames)]
                j += 1
        else:
            data_list  = [(filename, self.timestamp(self.filenames[i], resolution, center_based=True), self.timestamp(self.filenames[i], resolution, center_based=False)) for i, filename in enumerate(self.basenames)]
        
        header = ['dataset', 'surface based', 'center based']
        table_model = TableModel(self, data_list, header)
        self.table_view.setModel(table_model)
        
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

    def update_frame_chooser(self, resolution):
        if len(self.filenames) == 1:
            calc_frames = calculation.calculated_frames(self.filenames[0], resolution)
            self.frame_chooser.set_calculated_frames(calc_frames)

    def lineedit_return(self):
        try:
            resolution = int(self.lineedit.text())
            self.res_slider.setValue(resolution)
            self.update_table(resolution)
            self.update_frame_chooser(resolution)
        except ValueError:
            pass
            #print 'Enter a valid number'

    def slider_changing(self, resolution):
        self.lineedit.setText(str(resolution))

    def slider_released(self):
        resolution = self.res_slider.value()
        self.update_table(resolution)
        self.update_frame_chooser(resolution)

    def timestamp(self, filename, resolution, center_based, frame_nr=-1):
        import h5py

        if os.path.isfile(filename):
            if frame_nr == -1:
                if all([calculation.calculated(filename, frame_nr, resolution, False) for frame_nr in range(1, calculation.count_frames(filename)+1)]):
                    if center_based:
                        if not all([calculation.calculated(filename, frame_nr, resolution, True) for frame_nr in range(1, calculation.count_frames(filename)+1)]):
                            return 'X'
                    base_name = ''.join(os.path.basename(filename).split(".")[:-1])
                    exp_name = "../results/{}.hdf5".format(base_name)
                    with h5py.File(exp_name, "r") as file:
                        for calc in file['frame{}'.format(frame_nr)].values():
                            if calc.attrs['resolution'] == resolution:
                                return calc.attrs['timestamp']
            elif calculation.calculated(filename, frame_nr, resolution, False):
                return self.timestamp(filename, resolution, False, frame_nr)
        return 'X' 

    def ok(self):
        self.done(QtGui.QDialog.Accepted)
    
    def cancel(self):
        self.done(QtGui.QDialog.Rejected)

    def calculation_settings(self):
        ok = self.exec_()
        frames = [-1] if len(self.filenames) > 1 else self.frame_chooser.value()
        center_based = True if self.checkbox.checkState() == QtCore.Qt.CheckState.Checked else False
        #print 'center_based', center_based
        return self.res_slider.value(), frames, center_based, ok
