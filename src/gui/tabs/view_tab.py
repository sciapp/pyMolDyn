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
        self.results = None
        self.init_gui()

    def init_gui(self):
        vbox = QtGui.QVBoxLayout()
        group_box = QtGui.QGroupBox('view settings', self)
        view_box = QtGui.QVBoxLayout()

        self.box_check = QtGui.QCheckBox('show bounding box', self)
        self.atom_check = QtGui.QCheckBox('show atoms', self)
        self.bonds_check = QtGui.QCheckBox('show bonds', self)
        self.domain_check = QtGui.QCheckBox('show domains', self)
        self.surface_cavity_check = QtGui.QCheckBox('show cavities (surface method)', self)
        self.center_cavity_check = QtGui.QCheckBox('show cavities (center method)', self)

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
        self.surface_cavity_check.setChecked(True)
        self.center_cavity_check.setChecked(False)

        self.box_check.stateChanged.connect(partial(self.on_checkbox,
                                                    self.box_check))
        self.atom_check.stateChanged.connect(partial(self.on_checkbox,
                                                     self.atom_check))
        self.bonds_check.stateChanged.connect(partial(self.on_checkbox,
                                                      self.bonds_check))
        self.domain_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.domain_check, clicked_box="domain"))
        self.surface_cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.surface_cavity_check, clicked_box="surface_cavity"))
        self.center_cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                        self.center_cavity_check, clicked_box="center_cavity"))

        self.domain_check.setDisabled(True)
        self.surface_cavity_check.setDisabled(True)
        self.center_cavity_check.setDisabled(True)
        self.update_cavity_buttons(self.results, None)

        view_box.addWidget(self.box_check)
        view_box.addWidget(self.atom_check)
        view_box.addWidget(self.bonds_check)
        view_box.addWidget(self.domain_check)
        view_box.addWidget(self.surface_cavity_check)
        view_box.addWidget(self.center_cavity_check)
        group_box.setLayout(view_box)

        vbox.addWidget(group_box)
        vbox.addStretch()
        self.setLayout(vbox)
        self.show()

    def update_cavity_buttons(self, results, clicked_box=None):
        self.results = results

        if self.results is None:
            return

        if self.results.domains is None:
            self.domain_check.setDisabled(True)
            self.surface_cavity_check.setDisabled(True)
            self.center_cavity_check.setDisabled(True)
            return

        # enable elements depending on, if they are computed
        if self.results.domains is not None:
            self.domain_check.setEnabled(True)
        if self.results.center_cavities is not None:
            self.center_cavity_check.setEnabled(True)
        if self.results.surface_cavities is not None:
            self.surface_cavity_check.setEnabled(True)

        if clicked_box is None:
            return

        # un- / check elements depending on current selection
        if clicked_box == "surface_cavity" and self.surface_cavity_check.isChecked():
            self.domain_check.setChecked(False)
            self.center_cavity_check.setChecked(False)
        elif ((clicked_box == "center_cavity" and self.center_cavity_check.isChecked())
                or (clicked_box == "domain" and self.domain_check.isChecked())):
            self.surface_cavity_check.setChecked(False)

    def on_checkbox(self, check_box, check_state, clicked_box=None):
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

        #self.domain_check.setDisabled(True)
        #self.cavity_check.setDisabled(True)
        #self.alt_cav_check.setDisabled(True)
        #print "bla2"
        self.update_cavity_buttons(self.results, clicked_box)


        settings.show_domains = self.domain_check.isChecked()
        settings.show_cavities = self.surface_cavity_check.isChecked()
        settings.show_alt_cavities = self.center_cavity_check.isChecked()

        self.gl_widget.create_scene()
