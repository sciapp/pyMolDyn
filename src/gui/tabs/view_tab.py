# -*- coding: utf-8 -*-

from PySide import QtGui, QtCore


class ViewTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'view'-tab
    """

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "view", parent)
        self.setWidget(QtGui.QWidget())

        self.layout     = QtGui.QHBoxLayout()
        self.view_tab   = ViewTab(self.widget(), parent)

        self.layout.addWidget(self.view_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)


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
        self.domain_check = QtGui.QCheckBox('show domains', self)
        self.cavity_check = QtGui.QCheckBox('show cavities', self)
        self.alt_cav_check = QtGui.QCheckBox('show alt. cavities', self)

        #TODO synch with dataset
        # self.box_check.setCheckState(self.vis_settings.show_bounding_box)
        # self.atom_check.setCheckState(self.vis_settings.show_atoms)
        # self.domain_check.setCheckState(self.vis_settings.show_domains)
        # self.cavity_check.setCheckState(self.vis_settings.show_cavities)
        # self.alt_cav_check.setCheckState(self.vis_settings.show_alt_cavities)

        self.box_check.setCheckState(QtCore.Qt.CheckState.Checked if True else QtCore.Qt.CheckState.Unchecked)
        self.atom_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.domain_check.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.cavity_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.alt_cav_check.setCheckState(QtCore.Qt.CheckState.Unchecked)

        self.box_check.stateChanged.connect(self.on_checkbox)
        self.atom_check.stateChanged.connect(self.on_checkbox)
        self.domain_check.stateChanged.connect(self.on_checkbox)
        self.cavity_check.stateChanged.connect(self.on_checkbox)
        self.alt_cav_check.stateChanged.connect(self.on_checkbox)

        view_box.addWidget(self.box_check)
        view_box.addWidget(self.atom_check)
        view_box.addWidget(self.domain_check)
        view_box.addWidget(self.cavity_check)
        view_box.addWidget(self.alt_cav_check)
        group_box.setLayout(view_box)

        vbox.addWidget(group_box)
        vbox.addStretch()
        self.setLayout(vbox)
        self.show()

    def on_checkbox(self):
        settings = self.gl_widget.vis.settings
        settings.show_bounding_box = self.box_check.checkState() == QtCore.Qt.CheckState.Checked
        settings.show_atoms = self.atom_check.checkState() == QtCore.Qt.CheckState.Checked
        settings.show_domains = self.domain_check.checkState() == QtCore.Qt.CheckState.Checked
        settings.show_cavities = self.cavity_check.checkState() == QtCore.Qt.CheckState.Checked
        settings.show_alt_cavities = self.alt_cav_check.checkState() == QtCore.Qt.CheckState.Checked

        self.gl_widget.create_scene()