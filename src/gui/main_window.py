# -*- coding: utf-8 -*-


import os
from gui.tabs.file_tab import FileTabDock
from gui.tabs.view_tab import ViewTabDock
from gui.tabs.image_video_tab import ImageVideoTabDock
from gui.tabs.statistics_tab import StatisticsTabDock
from PyQt4 import QtCore, QtGui
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.about_dialog import AboutDialog
from gui.gl_widget import UpdateGLEvent
from util import message
from gl_stack import GLStack
from _version import __version__
import functools
import os.path
from config.configuration import config

import core.bonds
import core.control
#from core.data import Results

WEBSITE_URL = 'https://pgi-jcns.fz-juelich.de/portal/pages/pymoldyn-gui.html'

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
            if not dock == self.image_video_dock:
                self.tabifyDockWidget(self.file_dock, dock)

        # this variable is used to open the FileDialog in the propper path
        self.file_dock.file_tab.most_recent_path = "~"

        self.menubar = None
        self.file_menu = None
        self.recent_files_submenu = None
        self.init_menu()

        self.setWindowTitle('pyMolDyn v%s' % __version__)
        self.setWindowIcon(QtGui.QIcon('icon.png'))

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

        website_action = QtGui.QAction('&pyMolDyn website', self)
        website_action.setShortcut('F1')
        website_action.triggered.connect(self.show_website)

        about_action = QtGui.QAction('&About', self)
        about_action.triggered.connect(self.show_about_box)

        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu('&File')
        self.file_menu.addAction(open_action)
        self.file_menu.addAction(settings_action)
        self.file_menu.addMenu(export_submenu)

        self.init_submenu_recent_files()
        self.file_menu.addMenu(self.recent_files_submenu)

        export_submenu.addAction(export_bonds_action)
        export_submenu.addAction(export_bond_angles_action)
        export_submenu.addAction(export_bond_dihedral_angles_action)


        help_menu = self.menubar.addMenu('&Help')
        help_menu.addAction(website_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

    def show_settings(self):
        SettingsDialog()
        self.control.update()
        self.statistics_dock.update_results(self.control.visualization.results)

    def show_website(self):
        url = QtCore.QUrl(WEBSITE_URL)
        QtGui.QDesktopServices.openUrl(url)

    def show_about_box(self):
        AboutDialog(self, 'pyMolDyn is a molecule viewer which is capable of computing molecular cavities.',
                    (('Florian Rhiem', 'f.rhiem@fz-juelich.de'),
                     ('Fabian Beule', 'f.beule@fz-juelich.de'),
                     ('David Knodt', 'd.knodt@fz-juelich.de'),
                     ('Ingo Heimbach', 'i.heimbach@fz-juelich.de'),
                     ('Florian Macherey', 'f.macherey@fz-juelich.de'))).show()

    def init_submenu_recent_files(self):
        self.recent_files_submenu = QtGui.QMenu("&Recent files", self)
        if (not config.recent_files) or (config.recent_files == ['']):
            self.recent_files_submenu.setDisabled(True)
        else:
            self.recent_files_submenu.setEnabled(True)
            for f in config.recent_files:
                f_action = QtGui.QAction(f, self)
                f_action.triggered.connect(lambda arg=f: self.wrapper_recent_files(arg))
                self.recent_files_submenu.addAction(f_action)

            self.file_dock.file_tab.most_recent_path = os.path.dirname(config.recent_files[0])
            self._submenu_add_shortcut_for_first_item()

    def update_submenu_recent_files(self):
        if not config.recent_files:
            return

        most_recent_file = config.recent_files[0]
        if not most_recent_file:
            return

        actions_in_menu = self.recent_files_submenu.actions()
        actions_in_menu_str = [s.text() for s in actions_in_menu]

        if most_recent_file in actions_in_menu_str:
            index = actions_in_menu_str.index(most_recent_file)
            if index == 0:
                return

            self.recent_files_submenu.removeAction(actions_in_menu[index])
            self.recent_files_submenu.insertAction(actions_in_menu[0], actions_in_menu[index])
        else:
            new_action = QtGui.QAction(most_recent_file, self)
            new_action.triggered.connect(lambda arg=most_recent_file: self.wrapper_recent_files(arg))

            if not actions_in_menu:
                self.recent_files_submenu.setEnabled(True)
                self.recent_files_submenu.addAction(new_action)
            else:
                self.recent_files_submenu.insertAction(actions_in_menu[0], new_action)
                self.recent_files_submenu.actions()[0].setDisabled(True)

                if len(actions_in_menu) == 5:
                    self.recent_files_submenu.removeAction(actions_in_menu[4])

        self.file_dock.file_tab.most_recent_path = os.path.dirname(most_recent_file)
        self._submenu_add_shortcut_for_first_item()
        self.recent_files_submenu.update()

    def _submenu_add_shortcut_for_first_item(self):
        actions_in_menu = self.recent_files_submenu.actions()
        actions_in_menu[0].setShortcut('Alt+1')
        for action in actions_in_menu[1:]:
            action.setShortcut('')
        self.recent_files_submenu.update()

    def wrapper_recent_files(self, f):
        if f:
            self.file_dock.file_tab.disable_files_in_menu_and_open(f)
            self.update_submenu_recent_files()

    def wrapper_export_bonds(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export Bonds", "bonds.txt")
        if filename:
            core.bonds.export_bonds(filename, self.control.visualization.results.atoms)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Saved to filename: %s"%(filename))
            msgBox.exec_()

    def wrapper_export_bond_angles(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export Bond Angles", "bond_angles.txt")
        if filename:
            core.bonds.export_bond_angles(filename, self.control.visualization.results.atoms)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Saved to filename: %s"%(filename))
            msgBox.exec_()


    def wrapper_export_bond_dihedral_angles(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Export Bond Dihedral Angles", "bond_dihedral_angles.txt")
        if filename:
            core.bonds.export_bond_dihedral_angles(filename, self.control.visualization.results.atoms)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Saved to filename: %s"%(filename))
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
        self.view_dock.view_tab.update_cavity_buttons(self.control.visualization.results, None)
        # update GL scene
        self.center.gl_stack.gl_widget.update_needed = True
        QtGui.QApplication.postEvent(self.center.gl_stack.gl_widget, UpdateGLEvent())

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
        self.combo = QtGui.QComboBox()
        for title in self.widget_titles:
            self.combo.addItem(title)
        self.combo.activated[str].connect(self.on_combo)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.gl_stack)
        layout.addWidget(self.combo)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(layout)

    def on_combo(self, string):
        index = self.widget_titles.index(string)
        self.gl_stack.setCurrentIndex(index)
