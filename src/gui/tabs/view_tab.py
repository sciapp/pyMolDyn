# -*- coding: utf-8 -*-

from functools import partial
from PyQt4 import QtGui, QtCore


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
        self.all_atom_check = QtGui.QCheckBox('show all atoms', self)
        self.bonds_check = QtGui.QCheckBox('show bonds', self)
        self.all_domain_check = QtGui.QCheckBox('show all domains', self)
        self.some_domain_box = QtGui.QHBoxLayout()
        self.some_domain_check = QtGui.QCheckBox('show domains with indices', self)
        self.some_domain_text = QtGui.QLineEdit(self)
        self.some_domain_box.addWidget(self.some_domain_check)
        self.some_domain_box.addWidget(self.some_domain_text)
        self.all_surface_cavity_check = QtGui.QCheckBox('show all cavities (surface method)', self)
        self.some_surface_cavity_box = QtGui.QHBoxLayout()
        self.some_surface_cavity_check = QtGui.QCheckBox('show cavities (surface method) with indices', self)
        self.some_surface_cavity_text = QtGui.QLineEdit(self)
        self.some_surface_cavity_box.addWidget(self.some_surface_cavity_check)
        self.some_surface_cavity_box.addWidget(self.some_surface_cavity_text)
        self.all_center_cavity_check = QtGui.QCheckBox('show all cavities (center method)', self)
        self.some_center_cavity_box = QtGui.QHBoxLayout()
        self.some_center_cavity_check = QtGui.QCheckBox('show cavities (center method) with indices', self)
        self.some_center_cavity_text = QtGui.QLineEdit(self)
        self.some_center_cavity_box.addWidget(self.some_center_cavity_check)
        self.some_center_cavity_box.addWidget(self.some_center_cavity_text)

        # TODO synch with dataset
        # self.box_check.setCheckState(self.vis_settings.show_bounding_box)
        # self.all_atom_check.setCheckState(self.vis_settings.show_atoms)
        # self.all_domain_check.setCheckState(self.vis_settings.show_domains)
        # self.all_surface_cavity_check.setCheckState(self.vis_settings.show_surface_cavities)
        # self.all_center_cavity_check.setCheckState(self.vis_settings.show_center_cavities)

        self.box_check.setChecked(True)
        self.all_atom_check.setChecked(True)
        self.bonds_check.setChecked(True)
        self.all_domain_check.setChecked(False)
        self.all_surface_cavity_check.setChecked(True)
        self.all_center_cavity_check.setChecked(False)

        self.box_check.stateChanged.connect(partial(self.on_checkbox,
                                                    self.box_check))
        self.all_atom_check.stateChanged.connect(partial(self.on_checkbox,
                                                     self.all_atom_check))
        self.bonds_check.stateChanged.connect(partial(self.on_checkbox,
                                                      self.bonds_check))
        self.all_domain_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.all_domain_check, clicked_box="all_domains"))
        self.some_domain_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.some_domain_check, clicked_box="some_domains"))
        self.all_surface_cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.all_surface_cavity_check, clicked_box="all_surface_cavities"))
        self.some_surface_cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                       self.some_surface_cavity_check, clicked_box="some_surface_cavities"))
        self.all_center_cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                        self.all_center_cavity_check, clicked_box="all_center_cavities"))
        self.some_center_cavity_check.stateChanged.connect(partial(self.on_checkbox,
                                                        self.some_center_cavity_check, clicked_box="some_center_cavities"))

        self.some_domain_text.textChanged.connect(self.some_domain_text_changed)
        self.some_surface_cavity_text.textChanged.connect(self.some_surface_cavity_text_changed)
        self.some_center_cavity_text.textChanged.connect(self.some_center_cavity_text_changed)

        self.all_domain_check.setDisabled(True)
        self.some_domain_check.setDisabled(True)
        self.some_domain_text.setDisabled(True)
        self.all_surface_cavity_check.setDisabled(True)
        self.some_surface_cavity_check.setDisabled(True)
        self.some_surface_cavity_text.setDisabled(True)
        self.all_center_cavity_check.setDisabled(True)
        self.some_center_cavity_check.setDisabled(True)
        self.some_center_cavity_text.setDisabled(True)
        self.update_cavity_buttons(self.results, None)

        view_box.addWidget(self.box_check)
        view_box.addWidget(self.all_atom_check)
        view_box.addWidget(self.bonds_check)
        view_box.addWidget(self.all_domain_check)
        view_box.addLayout(self.some_domain_box)
        view_box.addWidget(self.all_surface_cavity_check)
        view_box.addLayout(self.some_surface_cavity_box)
        view_box.addWidget(self.all_center_cavity_check)
        view_box.addLayout(self.some_center_cavity_box)
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
            self.all_domain_check.setDisabled(True)
            self.some_domain_check.setDisabled(True)
            self.some_domain_text.setDisabled(True)
            self.all_surface_cavity_check.setDisabled(True)
            self.all_center_cavity_check.setDisabled(True)
            self.some_surface_cavity_check.setDisabled(True)
            self.some_center_cavity_check.setDisabled(True)
            return
        else:
            self.all_domain_check.setEnabled(True)
            self.some_domain_check.setEnabled(True)
            self.some_domain_text.setEnabled(True)

        # enable elements depending on, if they are computed
        self.all_surface_cavity_check.setEnabled(self.results.surface_cavities is not None)
        self.some_surface_cavity_check.setEnabled(self.results.surface_cavities is not None)
        self.some_surface_cavity_text.setEnabled(self.results.surface_cavities is not None)
        self.all_center_cavity_check.setEnabled(self.results.center_cavities is not None)
        self.some_center_cavity_check.setEnabled(self.results.center_cavities is not None)
        self.some_center_cavity_text.setEnabled(self.results.center_cavities is not None)

        # un- / check elements depending on current selection
        if clicked_box is None:
            return

        if clicked_box == "all_surface_cavities" and self.all_surface_cavity_check.isChecked():
            self.all_domain_check.setChecked(False)
            self.some_domain_check.setChecked(False)
            self.all_center_cavity_check.setChecked(False)
            self.some_center_cavity_check.setChecked(False)
            self.some_surface_cavity_check.setChecked(False)
        elif clicked_box == "some_surface_cavities" and self.some_surface_cavity_check.isChecked():
            self.all_domain_check.setChecked(False)
            self.some_domain_check.setChecked(False)
            self.all_center_cavity_check.setChecked(False)
            self.some_center_cavity_check.setChecked(False)
            self.all_surface_cavity_check.setChecked(False)
        elif clicked_box == "all_center_cavities" and self.all_center_cavity_check.isChecked():
            self.all_surface_cavity_check.setChecked(False)
            self.some_surface_cavity_check.setChecked(False)
            self.some_center_cavity_check.setChecked(False)
        elif clicked_box == "some_center_cavities" and self.some_center_cavity_check.isChecked():
            self.all_surface_cavity_check.setChecked(False)
            self.some_surface_cavity_check.setChecked(False)
            self.all_center_cavity_check.setChecked(False)
        elif clicked_box == 'all_domains' and self.all_domain_check.isChecked():
            self.some_domain_check.setChecked(False)
            self.all_surface_cavity_check.setChecked(False)
            self.some_surface_cavity_check.setChecked(False)
        elif clicked_box == 'some_domains' and self.some_domain_check.isChecked():
            self.all_domain_check.setChecked(False)
            self.all_surface_cavity_check.setChecked(False)
            self.some_surface_cavity_check.setChecked(False)


    def on_checkbox(self, check_box, check_state, clicked_box=None):
        settings = self.gl_widget.vis.settings
        settings.show_bounding_box = self.box_check.isChecked()
        settings.show_atoms = self.all_atom_check.isChecked()
        if check_box == self.all_atom_check:
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

        #self.all_domain_check.setDisabled(True)
        #self.all_surface_cavity_check.setDisabled(True)
        #self.all_center_cavity_check.setDisabled(True)
        self.update_cavity_buttons(self.results, clicked_box)
        settings.show_domains = self.all_domain_check.isChecked() or self.some_domain_check.isChecked()
        if check_box == self.all_domain_check and check_box.isChecked():
            settings.visible_domain_indices = None
        if check_box == self.some_domain_check and check_box.isChecked():
            indices = self.get_indices_from_line_edit(self.some_domain_text)
            settings.visible_domain_indices = indices
        settings.show_surface_cavities = self.all_surface_cavity_check.isChecked() or self.some_surface_cavity_check.isChecked()
        if check_box == self.all_surface_cavity_check and check_box.isChecked():
            settings.visible_surface_cavity_indices = None
        if check_box == self.some_surface_cavity_check and check_box.isChecked():
            indices = self.get_indices_from_line_edit(self.some_surface_cavity_text)
            settings.visible_surface_cavity_indices = indices
        settings.show_center_cavities = self.all_center_cavity_check.isChecked() or self.some_center_cavity_check.isChecked()
        if check_box == self.all_center_cavity_check and check_box.isChecked():
            settings.visible_center_cavity_indices = None
        if check_box == self.some_center_cavity_check and check_box.isChecked():
            indices = self.get_indices_from_line_edit(self.some_center_cavity_text)
            settings.visible_center_cavity_indices = indices
        self.gl_widget.create_scene()

    def get_indices_from_line_edit(self, line_edit):
        if line_edit.text().strip().endswith(','):
            return None
        try:
            return list(int(i)-1 for i in line_edit.text().split(','))
        except ValueError:
            return []

    def some_domain_text_changed(self):
        indices = self.get_indices_from_line_edit(self.some_domain_text)
        if indices is not None and self.some_domain_check.isChecked():
            self.gl_widget.vis.settings.visible_domain_indices = indices
            self.gl_widget.create_scene()

    def some_surface_cavity_text_changed(self):
        indices = self.get_indices_from_line_edit(self.some_surface_cavity_text)
        if indices is not None and self.some_surface_cavity_check.isChecked():
            self.gl_widget.vis.settings.visible_surface_cavity_indices = indices
            self.gl_widget.create_scene()

    def some_center_cavity_text_changed(self):
        indices = self.get_indices_from_line_edit(self.some_center_cavity_text)
        if indices is not None and self.some_center_cavity_check.isChecked():
            self.gl_widget.vis.settings.visible_center_cavity_indices = indices
            self.gl_widget.create_scene()