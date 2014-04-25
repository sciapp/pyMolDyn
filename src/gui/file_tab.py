# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui
import sys
import os.path
import calculation
from gui.dialogs.calculation_dialog import CalculationDialog

class FileTabDock(QtGui.QDockWidget):
    '''
        DockWidget to the 'file'-tab
    '''
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self,"file", parent)
        self.setWidget(QtGui.QWidget())

        self.layout     = QtGui.QHBoxLayout()
        self.file_tab   = FileTab(self.widget())

        self.layout.addWidget(self.file_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

class FileTab(QtGui.QWidget):
    '''
        tab 'file' in the main widget
    '''

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self,parent)
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
        
        self.vbox.addLayout(self.button_hbox)

        self.file_list = DragList(self)
        self.file_list.itemDoubleClicked.connect(self.calculate)
        self.file_list.itemSelectionChanged.connect(self.selection_changed)
        self.vbox.addWidget(self.file_list)

        self.setLayout(self.vbox)

    def selection_changed(self):
        sel = self.file_list.get_selection()
        if not sel or len(self.file_list.get_selection()) > 1:
            return
        filename = sel[0]

    def remove_selected_files(self):
        self.file_list.remove_selected_files()

    def open_file_dialog(self):
        filenames, _ = QtGui.QFileDialog.getOpenFileNames(self, 'Open dataset', '~')

        for fn in filenames:
            if fn:
                self.file_list.add_file(fn)

    def calculate(self):
        filename = self.file_list.get_selection()[0]
#        if calculation.calculated(filename):
#            print 'berechnet'
        #show dialog
        dia = CalculationDialog(self, self.file_list.get_selection())
        resolution, frame, ok = dia.calculation_settings()
        if ok:
            print 'res:', resolution, 'frame:', frame
        else:
            print 'Cancel'
            
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
#        return [str(item.text()) for item in self.selectedItems()]
        return [self.datalist[str(item.text())] for item in self.selectedItems()]

