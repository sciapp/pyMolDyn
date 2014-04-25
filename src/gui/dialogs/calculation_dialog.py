# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from gui.dialogs.util.calc_table import *
from gui.dialogs.util.framechooser import LabeledFrameChooser
import calculation
import os.path 


class CalculationDialog(QtGui.QDialog):

    FRAME_MIN = 32
    FRAME_MAX = 1024

    def __init__(self, parent=None, filenames=[]):
        QtGui.QDialog.__init__(self, parent)

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
        button_hbox.addWidget(ok_button)

        cancel_button = QtGui.QPushButton('Cancel', self)
        cancel_button.setAutoDefault(False)
        cancel_button.clicked.connect(self.cancel)
        button_hbox.addWidget(cancel_button)
        
        resolution = 64
        
        self.table_view = CalculationTable(self)
        self.update_table(resolution)
        self.res_slider.setValue(resolution)

        vbox.addLayout(res_hbox)
        vbox.addWidget(self.table_view)

        if len(filenames) == 1:
            n_frames    = calculation.count_frames(filenames[0])
            calc_frames = calculation.calculated_frames(filenames[0], resolution)
            self.frame_chooser = LabeledFrameChooser(None, 0, n_frames, calc_frames, 'Frame')
            vbox.addWidget(self.frame_chooser)

        vbox.addLayout(button_hbox)
        self.setLayout(vbox)
        self.setWindowTitle("Calculation Settings")
    
    def update_table(self, resolution):
        self.lineedit.setText(str(resolution))

        data_list  = [(filename, self.timestamp(self.filenames[i], resolution, surface_based=True), self.timestamp(self.filenames[i], resolution, surface_based=False)) for i, filename in enumerate(self.basenames)]
        header = ['dataset', 'surface based', 'center based']
        
        table_model = TableModel(self, data_list, header)
        self.table_view.setModel(table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

    def lineedit_return(self):
        try:
            resolution = int(self.lineedit.text())
            self.res_slider.setValue(resolution)
            self.update_table(resolution)
        except ValueError:
            pass
            #print 'Enter a valid number'

    def slider_changing(self, resolution):
        self.lineedit.setText(str(resolution))

    def slider_released(self):
        self.update_table(self.res_slider.value())

    def timestamp(self, filename, resolution, surface_based):
        import h5py
        print filename

        if os.path.isfile(filename):
            if all([calculation.calculated(filename, frame_nr, resolution, True) for frame_nr in range(1, calculation.count_frames(filename)+1)]):
                if surface_based:
                    if not all([calculation.calculated(filename, frame_nr, resolution, False) for frame_nr in range(1, calculation.count_frames(filename)+1)]):
                        return 'X'
                base_name = ''.join(os.path.basename(filename).split(".")[:-1])
                exp_name = "results/{}.hdf5".format(base_name)
                with h5py.File(exp_name, "r") as file:
                    for calc in file['frame1'.format()].values():
                        if calc.attrs['resolution'] == resolution:
                            return calc.attrs['timestamp']
        return 'X' 

    def ok(self):
        self.done(QtGui.QDialog.Accepted)
    
    def cancel(self):
        self.done(QtGui.QDialog.Rejected)

    def calculation_settings(self):
        ok = self.exec_()
        frames = [-1] if len(self.filenames) > 1 else self.frame_chooser.value()
        return self.res_slider.value(), frames, ok
