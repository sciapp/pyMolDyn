# -*- coding: utf-8 -*-

from functools import partial
import itertools
from PyQt4 import QtGui, QtCore
from gui.object_select_widget import ObjectSelectWidget

counter = itertools.count(0)
class ObjectTypeId(object):
    ATOM = counter.next()
    DOMAIN = counter.next()
    CENTER_BASED_CAVITY = counter.next()
    SURFACE_BASED_CAVITY = counter.next()

del counter


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
        view_layout = QtGui.QVBoxLayout()

        # normal checkboxes are not used to prevent alignment problems between the different check box types
        self.box_check = ObjectSelectWidget('show bounding box', self, add_index_selector=False)
        self.atom_check = ObjectSelectWidget('show atoms', self)
        self.bonds_check = ObjectSelectWidget('show bonds', self, add_index_selector=False)
        self.domain_check = ObjectSelectWidget('show domains', self)
        self.surface_cavity_check = ObjectSelectWidget('show cavities (surface method)', self)
        self.center_cavity_check = ObjectSelectWidget('show cavities (center method)', self)

        # TODO synch with dataset
        # self.box_check.setCheckState(self.vis_settings.show_bounding_box)
        # self.all_atom_check.setCheckState(self.vis_settings.show_atoms)
        # self.all_domain_check.setCheckState(self.vis_settings.show_domains)
        # self.all_surface_cavity_check.setCheckState(self.vis_settings.show_surface_cavities)
        # self.all_center_cavity_check.setCheckState(self.vis_settings.show_center_cavities)

        self.box_check.setChecked(True)
        self.atom_check.setChecked(True)
        self.bonds_check.setChecked(True)
        self.domain_check.setChecked(False)
        self.surface_cavity_check.setChecked(True)
        self.center_cavity_check.setChecked(False)

        self.box_check.state_changed.connect(partial(self.on_checkbox, self.box_check))
        self.atom_check.state_changed.connect(partial(self.on_checkbox, self.atom_check,
                                                      clicked_box=ObjectTypeId.ATOM))
        self.bonds_check.state_changed.connect(partial(self.on_checkbox, self.bonds_check))
        self.domain_check.state_changed.connect(partial(self.on_checkbox, self.domain_check,
                                                        clicked_box=ObjectTypeId.DOMAIN))
        self.surface_cavity_check.state_changed.connect(partial(self.on_checkbox, self.surface_cavity_check,
                                                                clicked_box=ObjectTypeId.SURFACE_BASED_CAVITY))
        self.center_cavity_check.state_changed.connect(partial(self.on_checkbox, self.center_cavity_check,
                                                               clicked_box=ObjectTypeId.CENTER_BASED_CAVITY))

        self.atom_check.selection_indices_changed.connect(partial(self.object_indices_changed,
                                                                  object_type_id=ObjectTypeId.ATOM))
        self.domain_check.selection_indices_changed.connect(partial(self.object_indices_changed,
                                                                    object_type_id=ObjectTypeId.DOMAIN))
        self.surface_cavity_check.selection_indices_changed.connect(partial(self.object_indices_changed,
                                                                            object_type_id=ObjectTypeId.SURFACE_BASED_CAVITY))
        self.center_cavity_check.selection_indices_changed.connect(partial(self.object_indices_changed,
                                                                           object_type_id=ObjectTypeId.CENTER_BASED_CAVITY))

        self.domain_check.setDisabled(True)
        self.surface_cavity_check.setDisabled(True)
        self.center_cavity_check.setDisabled(True)
        self.update_cavity_buttons(self.results, None)

        view_layout.addWidget(self.box_check)
        view_layout.addWidget(self.atom_check)
        view_layout.addWidget(self.bonds_check)
        view_layout.addWidget(self.domain_check)
        view_layout.addWidget(self.surface_cavity_check)
        view_layout.addWidget(self.center_cavity_check)
        group_box.setLayout(view_layout)

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
        else:
            self.domain_check.setEnabled(True)

        # enable elements depending on, if they are computed
        self.surface_cavity_check.setEnabled(self.results.surface_cavities is not None)
        self.center_cavity_check.setEnabled(self.results.center_cavities is not None)

        # un- / check elements depending on current selection
        if clicked_box is None:
            return

        if clicked_box == ObjectTypeId.SURFACE_BASED_CAVITY:
            is_checked = self.surface_cavity_check.isChecked()
            if is_checked:
                self.domain_check.setChecked(False)
                self.center_cavity_check.setChecked(False)
        elif clicked_box == ObjectTypeId.CENTER_BASED_CAVITY:
            is_checked = self.center_cavity_check.isChecked()
            if is_checked:
                self.surface_cavity_check.setChecked(False)
        elif clicked_box == ObjectTypeId.DOMAIN:
            is_checked = self.domain_check.isChecked()
            if is_checked:
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

        self.update_cavity_buttons(self.results, clicked_box)
        settings.show_domains = self.domain_check.isChecked()
        if check_box == self.domain_check and check_box.isChecked():
            settings.visible_domain_indices = check_box.indices
        settings.show_surface_cavities = self.surface_cavity_check.isChecked()
        if check_box == self.surface_cavity_check and check_box.isChecked():
            settings.visible_surface_cavity_indices = check_box.indices
        settings.show_center_cavities = self.center_cavity_check.isChecked()
        if check_box == self.center_cavity_check and check_box.isChecked():
            settings.visible_center_cavity_indices = check_box.indices
        self.gl_widget.create_scene()

    def object_indices_changed(self, indices, object_type_id, update_scene=True):
        object_type_id2attribute_name = {
            ObjectTypeId.ATOM: 'visible_atom_indices',
            ObjectTypeId.DOMAIN: 'visible_domain_indices',
            ObjectTypeId.CENTER_BASED_CAVITY: 'visible_center_cavity_indices',
            ObjectTypeId.SURFACE_BASED_CAVITY: 'visible_surface_cavity_indices',
        }

        setattr(self.gl_widget.vis.settings, object_type_id2attribute_name[object_type_id], indices)
        if update_scene:
            self.gl_widget.create_scene()
