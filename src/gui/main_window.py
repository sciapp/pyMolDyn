# -*- coding: utf-8 -*-


import os
from gui.tabs.file_tab import FileTabDock
from gui.tabs.view_tab import ViewTabDock
from gui.tabs.image_video_tab import ImageVideoTabDock
from gui.tabs.statistics_tab import StatisticsTabDock
from PySide import QtCore, QtGui
from gui.dialogs.settings_dialog import SettingsDialog
from util import message
from gl_stack import GLStack

import core.bonds
import core.control
#from core.data import Results
import visualization.visualization


class MainWindow(QtGui.QMainWindow):
    def __init__(self, control):
        QtGui.QMainWindow.__init__(self, None)

        self.control = control
        self.center = CentralWidget(self)
        self.file_dock = FileTabDock(self)
        self.view_dock = ViewTabDock(self)
        self.image_video_dock = ImageVideoTabDock(self)
        self.statistics_dock = StatisticsTabDock(self)

        self.docks = []

        self.shown_dataset = None

        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtGui.QTabWidget.North)

        for dock in (self.file_dock, self.view_dock, self.image_video_dock, self.statistics_dock):
            self.docks.append(dock)

        self.setCentralWidget(self.center)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.file_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.view_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.image_video_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.statistics_dock, QtCore.Qt.Vertical)

        for dock in self.docks[1:]:
            self.tabifyDockWidget(self.file_dock, dock)

        self.init_menu()

        self.show()
        # get Dock Widgets TabBar and set the first one to current
        self.file_dock.show()
        self.file_dock.raise_()

        # another workaround to do the same
        # tabbars = self.findChildren(QtGui.QTabBar)
        # tabbars[0].setCurrentIndex(0)

    def init_menu(self):
        open_action = QtGui.QAction('&Open dataset', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.file_dock.file_tab.open_file_dialog)

        settings_action = QtGui.QAction('&Settings', self)
        settings_action.setShortcut('Ctrl+I')
        settings_action.triggered.connect(self.show_settings)

        export_submenu = QtGui.QMenu("&Export", self)

        export_bonds_action = QtGui.QAction('Export &Bonds', self)
        export_bonds_action.setShortcut('Ctrl+1')
        export_bonds_action.triggered.connect(self.wrapper_export_bonds)

        export_bond_angles_action = QtGui.QAction('Export Bond &Angles', self)
        export_bond_angles_action.setShortcut('Ctrl+2')
        export_bond_angles_action.triggered.connect(self.wrapper_export_bond_angles)

        export_bond_dihedral_angles_action = QtGui.QAction('Export Bond &Dihedral Angles', self)
        export_bond_dihedral_angles_action.setShortcut('Ctrl+3')
        export_bond_dihedral_angles_action.triggered.connect(self.wrapper_export_bond_dihedral_angles)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(open_action)
        file_menu.addAction(settings_action)
        file_menu.addMenu(export_submenu)

        export_submenu.addAction(export_bonds_action)
        export_submenu.addAction(export_bond_angles_action)
        export_submenu.addAction(export_bond_dihedral_angles_action)

    def show_settings(self):
        SettingsDialog()
        self.control.update()
        self.statistics_dock.update_results(self.control.visualization.results)

    def wrapper_export_bonds(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export Bonds", "bonds.txt")
        if filename[0] != "":
            core.bonds.export_bonds(filename[0], self.control.visualization.results.atoms)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Saved to filename: %s"%(filename[0]))
            msgBox.exec_()

    def wrapper_export_bond_angles(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export Bond Angles", "bond_angles.txt")
        if filename[0] != "":
            core.bonds.export_bond_angles(filename[0], self.control.visualization.results.atoms)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Saved to filename: %s"%(filename[0]))
            msgBox.exec_()


    def wrapper_export_bond_dihedral_angles(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export Bond Dihedral Angles", "bond_dihedral_angles.txt")
        if filename[0] != "":
            core.bonds.export_bond_dihedral_angles(filename[0], self.control.visualization.results.atoms)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Saved to filename: %s"%(filename[0]))
            msgBox.exec_()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_M:
            if not self.isFullScreen():
                for dock in self.docks:
                    dock.hide()
                self.showFullScreen()
            else:
                for dock in self.docks:
                    dock.show()
                self.showNormal()

    def set_output_callbacks(self, progress_func, print_func, finish_func):
        message.set_output_callbacks(progress_func, print_func, finish_func)

    def updatestatus(self):
        results = self.control.results[-1][-1]
        self.shown_dataset = results
        status = str(results)
        self.statusBar().showMessage(status)
        self.statistics_dock.update_results(self.control.visualization.results)

#    def closeEvent(self, event):
#        reply = QtGui.QMessageBox.question(self, 'Message',
#            "Are you sure to quit?", QtGui.QMessageBox.Yes |
#            QtGui.QMessageBox.No, QtGui.QMessageBox.No)
#        if reply == QtGui.QMessageBox.Yes:
#            event.accept()
#        else:
#            event.ignore()


class CentralWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.control = parent.control
        self.setWindowTitle('pyMolDyn 2')
        self.widget_titles = (
                "3D View",
                "Radial Distribution",
                "Cavity Histograms")
        self.init_gui()

    def init_gui(self):
        self.gl_stack = GLStack(self)
        self.gl_widget = self.gl_stack.gl_widget
        combo = QtGui.QComboBox()
        for title in self.widget_titles:
            combo.addItem(title)
        combo.activated[str].connect(self.on_combo)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.gl_stack)
        layout.addWidget(combo)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(layout)

    def on_combo(self, string):
        index = self.widget_titles.index(string)
        self.gl_stack.setCurrentIndex(index)
