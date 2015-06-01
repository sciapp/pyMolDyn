# -*- coding: utf-8 -*-

from functools import partial
from PySide import QtGui, QtCore


class ViewTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'view'-tab
    """

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "view", parent)
        self.setWidget(QtGui.QWidget())

        self.layout = QtGui.QHBoxLayout()
        self.view_tab = ViewTab(self.widget(), parent)

        self.layout.addWidget(self.view_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable
                         | QtGui.QDockWidget.DockWidgetFloatable)


class ViewTab(QtGui.QWidget):
    """
        tab 'view' in the main widget
    """

    def __init__(self, parent, main_window):
        QtGui.QWidget.__init__(self, parent)
        self.gl_widget = main_window.center.gl_widget
        #self.vis_settings = self.gl_widget.vis.settings
        self.init_gui()

    def init_gui(self):
        vbox = QtGui.QVBoxLayout()
        group_box = QtGui.QGroupBox('view settings', self)
        view_box = QtGui.QVBoxLayout()

        self.box_check = QtGui.QCheckBox('show bounding box', self)
        self.atom_check = QtGui.QCheckBox('show atoms', self)
        self.bonds_check = QtGui.QCheckBox('show bonds', self)
        self.domain_check = QtGui.QCheckBox('show domains', self)
        self.cavity_check = QtGui.QCheckBox('show cavities (surface method)', self)
        self.alt_cav_check = QtGui.QCheckBox('show cavities (center method)', self)

        # TODO synch with dataset
        # self.box_check.setCheckState(self.vis_settings.show_bounding_box)
        # self.atom_check.setCheckState(self.vis_settings.show_atoms)
        # self.domain_check.setCheckState(self.vis_settings.show_domains)
        # self.cavity_check.setCheckState(self.vis_settings.show_cavities)
        # self.alt_cav_check.setCheckState(self.vis_settings.show_alt_cavities)

        self.box_check.setChecked(True)
        self.atom_check.setChecked(True)
        self.bonds_check.setChecked(True)
        self.domain_check.setChecked(False)
        self.cavity_check.setChecked(True)
        self.alt_cav_check.setChecked(False)

        self.box_check.stateChanged.connect(partial(self.on_checkbox,
                                                    self.box_check))
        self.atom_check.stateChanged.connect(partial(self.on_checkbox,
                                                     self.atom_check))
        self.bonds_check.stateChanged.connect(partial(self.on_checkbox,
                                                      self.bonds_check))
        self.domain_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.domain_check))
        self.cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.cavity_check))
        self.alt_cav_check.stateChanged.connect(partial(self.on_checkbox,
                                                        self.alt_cav_check))

        self.update_cavity_buttons()

        view_box.addWidget(self.box_check)
        view_box.addWidget(self.atom_check)
        view_box.addWidget(self.bonds_check)
        view_box.addWidget(self.domain_check)
        view_box.addWidget(self.cavity_check)
        view_box.addWidget(self.alt_cav_check)
        group_box.setLayout(view_box)

        vbox.addWidget(group_box)
        vbox.addStretch()
        self.setLayout(vbox)
        self.show()

    def update_cavity_buttons(self):
        if self.cavity_check.isChecked() and not self.alt_cav_check.isChecked():
            self.cavity_check.setEnabled(True)
            self.alt_cav_check.setDisabled(True)
        elif self.alt_cav_check.isChecked() and not self.cavity_check.isChecked():
            self.cavity_check.setDisabled(True)
            self.alt_cav_check.setEnabled(True)
        elif not (self.cavity_check.isChecked() and self.alt_cav_check.isChecked()):
            self.cavity_check.setEnabled(True)
            self.alt_cav_check.setEnabled(True)

    def on_checkbox(self, check_box, check_state):
        settings = self.gl_widget.vis.settings
        settings.show_bounding_box = self.box_check.isChecked()
        settings.show_atoms = self.atom_check.isChecked()
        if check_box == self.atom_check:
            if not settings.show_atoms:
                self.bonds_check.setEnabled(False)
                self.bonds_check.setChecked(False)
            else:
                self.bonds_check.setEnabled(True)
                if settings.show_bonds:
                    self.bonds_check.setChecked(True)
                else:
                    self.bonds_check.setChecked(False)
        if self.bonds_check.isEnabled():
            settings.show_bonds = self.bonds_check.isChecked()

        self.update_cavity_buttons()

        settings.show_domains = self.domain_check.isChecked()
        settings.show_cavities = self.cavity_check.isChecked()
        settings.show_alt_cavities = self.alt_cav_check.isChecked()

        self.gl_widget.create_scene()
