import functools
import os
import os.path

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

from .. import core
from .._version import __version__
from ..config.configuration import config
from ..util import message
from .dialogs.about_dialog import AboutDialog
from .dialogs.settings_dialog import SettingsDialog
from .gl_stack import GLStack
from .gl_widget import UpdateGLEvent
from .tabs.file_tab import FileTabDock
from .tabs.image_video_tab import ImageVideoTabDock
from .tabs.log_tab import LogTabDock
from .tabs.statistics_tab import StatisticsTabDock
from .tabs.view_tab import ViewTabDock

WEBSITE_URL = "https://pgi-jcns.fz-juelich.de/portal/pages/pymoldyn-doc.html"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, control):
        QtWidgets.QMainWindow.__init__(self, None)
        QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)

        self.control = control
        self.center = CentralWidget(self)
        self.file_dock = FileTabDock(self)
        self.view_dock = ViewTabDock(self)
        self.view_dock.setVisible(False)
        self.image_video_dock = ImageVideoTabDock(self)
        self.statistics_dock = StatisticsTabDock(self)
        self.log_dock = LogTabDock(self)
        self._error_wrapper = None

        p = self.file_dock.file_tab.progress_dialog
        self.set_output_callbacks(
            p.progress,
            p.print_step,
            p.calculation_finished,
            self.show_error,
            self.log_dock.append_log,
        )

        self.docks = []

        self.shown_dataset = None

        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtWidgets.QTabWidget.North)

        self.setCentralWidget(self.center)

        for dock in (
            self.file_dock,
            self.view_dock,
            self.image_video_dock,
            self.statistics_dock,
            self.log_dock,
        ):
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock, QtCore.Qt.Vertical)
            self.docks.append(dock)

        for dock in (self.view_dock, self.statistics_dock):
            self.tabifyDockWidget(self.file_dock, dock)

        # this variable is used to open the FileDialog in the propper path
        self.file_dock.file_tab.most_recent_path = "~"

        self.menubar = None
        self.file_menu = None
        self.recent_files_submenu = None
        self.init_menu()

        self.setWindowTitle("pyMolDyn v%s" % __version__)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.show()
        # get Dock Widgets TabBar and set the first one to current
        self.file_dock.show()
        self.file_dock.raise_()

        # another workaround to do the same
        # tabbars = self.findChildren(QtWidgets.QTabBar)
        # tabbars[0].setCurrentIndex(0)

    def init_menu(self):
        open_action = QtGui.QAction("&Open dataset", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.file_dock.file_tab.open_file_dialog)

        settings_action = QtGui.QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+I")
        settings_action.triggered.connect(self.show_settings)

        export_submenu = QtWidgets.QMenu("&Export", self)

        export_bonds_action = QtGui.QAction("Export &Bonds", self)
        export_bonds_action.setShortcut("Ctrl+1")
        export_bonds_action.triggered.connect(self.wrapper_export_bonds)

        export_bond_angles_action = QtGui.QAction("Export Bond &Angles", self)
        export_bond_angles_action.setShortcut("Ctrl+2")
        export_bond_angles_action.triggered.connect(self.wrapper_export_bond_angles)

        export_bond_dihedral_angles_action = QtGui.QAction("Export Bond &Dihedral Angles", self)
        export_bond_dihedral_angles_action.setShortcut("Ctrl+3")
        export_bond_dihedral_angles_action.triggered.connect(self.wrapper_export_bond_dihedral_angles)

        export_domains_action = QtGui.QAction("Export Cavity Information (domains)", self)
        export_domains_action.setShortcut("Ctrl+4")
        export_domains_action.triggered.connect(self.wrapper_export_domains)

        export_surface_cavities_action = QtGui.QAction("Export Cavity Information (surface method)", self)
        export_surface_cavities_action.setShortcut("Ctrl+5")
        export_surface_cavities_action.triggered.connect(self.wrapper_export_surface_cavities)

        export_center_cavities_action = QtGui.QAction("Export Cavity Information (center method)", self)
        export_center_cavities_action.setShortcut("Ctrl+6")
        export_center_cavities_action.triggered.connect(self.wrapper_export_center_cavities)

        website_action = QtGui.QAction("&pyMolDyn website", self)
        website_action.setShortcut("F1")
        website_action.triggered.connect(self.show_website)

        about_action = QtGui.QAction("&About", self)
        about_action.triggered.connect(self.show_about_box)

        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(open_action)
        self.file_menu.addAction(settings_action)
        self.file_menu.addMenu(export_submenu)

        self.init_submenu_recent_files()
        self.file_menu.addMenu(self.recent_files_submenu)

        export_submenu.addAction(export_bonds_action)
        export_submenu.addAction(export_bond_angles_action)
        export_submenu.addAction(export_bond_dihedral_angles_action)
        export_submenu.addAction(export_domains_action)
        export_submenu.addAction(export_surface_cavities_action)
        export_submenu.addAction(export_center_cavities_action)

        help_menu = self.menubar.addMenu("&Help")
        help_menu.addAction(website_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

    def show_error(self, error_message):
        QtCore.QMetaObject.invokeMethod(
            self,
            "_show_error",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, error_message),
        )

    @QtCore.Slot(str)
    def _show_error(self, error_message):
        QtWidgets.QMessageBox.information(self, "Information", error_message)

    def show_settings(self):
        SettingsDialog()
        self.control.update()
        self.statistics_dock.update_results(self.control.visualization.results)

    def show_website(self):
        url = QtCore.QUrl(WEBSITE_URL)
        QtGui.QDesktopServices.openUrl(url)

    def show_about_box(self):
        AboutDialog(
            self,
            "pyMolDyn is a molecule viewer which is capable of computing molecular cavities.",
            (
                ("Florian Rhiem", "f.rhiem@fz-juelich.de"),
                ("Fabian Beule", "f.beule@fz-juelich.de"),
                ("David Knodt", "d.knodt@fz-juelich.de"),
                ("Ingo Meyer", "i.meyer@fz-juelich.de"),
                ("Torben Moll", "t.moll@fz-juelich.de"),
                ("Florian Macherey", "f.macherey@fz-juelich.de"),
            ),
        ).show()

    def init_submenu_recent_files(self):
        self.recent_files_submenu = QtWidgets.QMenu("&Recent files", self)
        if (not config.recent_files) or (config.recent_files == [""]):
            self.recent_files_submenu.setDisabled(True)
        else:
            self.recent_files_submenu.setEnabled(True)
            for f in config.recent_files:
                f_action = QtGui.QAction(f, self)
                f_action.triggered.connect(functools.partial(self.wrapper_recent_files, f))
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
            new_action.triggered.connect(functools.partial(self.wrapper_recent_files, most_recent_file))

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
        actions_in_menu[0].setShortcut("Alt+1")
        for action in actions_in_menu[1:]:
            action.setShortcut("")
        self.recent_files_submenu.update()

    def wrapper_recent_files(self, f):
        if f:
            self.file_dock.file_tab.disable_files_in_menu_and_open(f)
            self.update_submenu_recent_files()

    def wrapper_export_bonds(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export Bonds", "bonds.txt")[0]
        if filename:
            core.bonds.export_bonds(filename, self.control.visualization.results.atoms)
            QtWidgets.QMessageBox.information(self, "Export Bonds", "Saved to filename: %s" % (filename))

    def wrapper_export_bond_angles(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export Bond Angles", "bond_angles.txt")[0]
        if filename:
            core.bonds.export_bond_angles(filename, self.control.visualization.results.atoms)
            QtWidgets.QMessageBox.information(self, "Export Bond Angles", "Saved to filename: %s" % (filename))

    def wrapper_export_bond_dihedral_angles(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Bond Dihedral Angles", "bond_dihedral_angles.txt"
        )[0]
        if filename:
            core.bonds.export_bond_dihedral_angles(filename, self.control.visualization.results.atoms)
            QtWidgets.QMessageBox.information(
                self,
                "Export Bond Dihedral Angles",
                "Saved to filename: %s" % (filename),
            )

    def wrapper_export_domains(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export Cavity Information (domains)", "domains")[0]
        if filename:
            filenames = self.control.visualization.results.domains.totxt(filename + "_{property}.txt")
            QtWidgets.QMessageBox.information(
                self,
                "Export Cavity Information (domains)",
                "Saved to filenames: %s" % (", ".join(filenames)),
            )

    def wrapper_export_surface_cavities(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Cavity Information (surface method)", "surface_cavities"
        )[0]
        if filename:
            filenames = self.control.visualization.results.surface_cavities.totxt(filename + "_{property}.txt")
            QtWidgets.QMessageBox.information(
                self,
                "Export Cavity Information (surface method)",
                "Saved to filenames: %s" % (", ".join(filenames)),
            )

    def wrapper_export_center_cavities(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Cavity Information (center method)", "center_cavities"
        )[0]
        if filename:
            filenames = self.control.visualization.results.center_cavities.totxt(filename + "_{property}.txt")
            QtWidgets.QMessageBox.information(
                self,
                "Export Cavity Information (center method)",
                "Saved to filenames: %s" % (", ".join(filenames)),
            )

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

    def set_output_callbacks(self, progress_func, print_func, finish_func, error_func, log_func):
        message.set_output_callbacks(progress_func, print_func, finish_func, error_func, log_func)

    def updatestatus(self, was_successful=lambda: True):
        if was_successful and self.control.results is not None:
            results = self.control.results[-1][-1]
            self.shown_dataset = results
            visualization_settings = self.control.visualization.settings
            status = results.description(
                domain_volume=visualization_settings.show_domains,
                surface_cavity_volume=visualization_settings.show_surface_cavities,
                center_cavity_volume=visualization_settings.show_center_cavities,
            )
            self.statusBar().showMessage(status)
            self.statistics_dock.update_results(self.control.visualization.results)
            self.view_dock.setVisible(True)
            self.view_dock.view_tab.update_cavity_buttons(self.control.visualization.results, None)
            self.center.gl_stack.updatestatus()
            QtWidgets.QApplication.postEvent(self.center.gl_stack.gl_widget, UpdateGLEvent())


class CentralWidget(QtWidgets.QWidget):

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.control = parent.control
        self.setWindowTitle("pyMolDyn 2")
        self.widget_titles = (
            "3D View",
            "Pair Distribution Functions",
            "Cavity Histograms",
        )
        self.init_gui()

    def init_gui(self):
        self.gl_stack = GLStack(self, self.parent())
        self.gl_widget = self.gl_stack.gl_widget
        self.combo = QtWidgets.QComboBox()
        for title in self.widget_titles:
            self.combo.addItem(title)
        self.combo.activated.connect(self.on_combo)  # removed [str] from activated

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.gl_stack)
        layout.addWidget(self.combo)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(layout)

    def on_combo(self, index):
        self.gl_stack.activate(index)
