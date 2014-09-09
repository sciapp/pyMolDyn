# -*- coding: utf-8 -*-

from core import calculation
from gui.tabs.file_tab import FileTabDock
from gui.tabs.view_tab import ViewTabDock
from gui.tabs.image_video_tab import ImageVideoTabDock
from gui.gl_widget import GLWidget
from PySide import QtCore, QtGui


class MainWindow(QtGui.QMainWindow):
    def __init__(self, control):
        QtGui.QMainWindow.__init__(self, None)

        self.center             = CentralWidget(self)
        self.file_dock          = FileTabDock(self)
        self.view_dock          = ViewTabDock(self)
        self.image_video_dock   = ImageVideoTabDock(self)
        self.control            = control

        self.docks = []

        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtGui.QTabWidget.North)

        for dock in (self.file_dock, self.view_dock, self.image_video_dock):
            self.docks.append(dock)

        self.setCentralWidget(self.center)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.file_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.view_dock, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.image_video_dock, QtCore.Qt.Vertical)

        for dock in self.docks[1:]:
            self.tabifyDockWidget(self.file_dock, dock)

        self.init_menu()

        self.show()

    def init_menu(self):
        open_action = QtGui.QAction('&Open dataset', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.file_dock.file_tab.open_file_dialog)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(open_action)

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
        calculation.set_output_callbacks(progress_func, print_func, finish_func)

    def show_dataset(self, volume, filename, frame_nr, resolution, use_center_points):
        self.statusBar().showMessage(filename)
        self.center.show_dataset(volume, filename, frame_nr, resolution, use_center_points)

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
        self.setWindowTitle('pyMolDyn 2')
        self.init_gui()
 
    def init_gui(self):
        self.gl_widget  = GLWidget(self)

        main_layout = QtGui.QHBoxLayout()
        main_layout.addWidget(self.gl_widget)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(main_layout)

    def show_dataset(self, volume, filename, frame_nr, resolution, use_center_points):
        self.gl_widget.show_dataset(volume, filename, frame_nr, resolution, use_center_points)
