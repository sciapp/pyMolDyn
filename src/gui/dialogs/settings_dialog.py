from PyQt4 import QtCore, QtGui
import sys
import functools
from config.configuration import config, Configuration
from gui.gl_widget import UpdateGLEvent, GLWidget
from collections import OrderedDict


class GraphicsSettingsPage(QtGui.QWidget):

    def __init__(self, parent, cfg):
        QtGui.QWidget.__init__(self, parent)

        self._config = cfg
        self.values = OrderedDict((('atom_radius', 'atom radius'), ('bond_radius', 'bond radius'), ))

        self.lineedit_dict = {}
        grid = QtGui.QGridLayout()
        for i, (attr_str, label) in enumerate(self.values.iteritems()):
            cfg_comp = getattr(self._config, 'OpenGL')

            l = QtGui.QLabel(label, self)
            t = QtGui.QLineEdit(self)
            t.setText(str(getattr(cfg_comp, attr_str)))
            self.lineedit_dict[attr_str] = t
            t.textChanged.connect(self.any_change)
            grid.addWidget(l, i, 0)
            grid.addWidget(t, i, 1)

        self.colors = OrderedDict((('background', 'Background'),
                                  ('bounding_box', 'Bounding Box'),
                                  ('bonds', 'Bonds'),
                                  ('domain', 'Cavity (domain)'),
                                  ('surface_cavity', 'Cavity (surface method)'),
                                  ('center_cavity', 'Cavity (Center method)')))

        self.button_dict = {}
        layout = QtGui.QGridLayout()
        layout.setSpacing(5)
        for index, (attr_str, btn_str) in enumerate(self.colors.iteritems()):

            pix = QtGui.QPixmap(50, 50)
            cfg_clr = getattr(self._config, 'Colors')
            tmp = [int(f * 255) for f in getattr(cfg_clr, attr_str)]
            current_color = QtGui.QColor(*tmp)
            pix.fill(current_color)

            b = QtGui.QPushButton(None, self)
            b.setFixedSize(50, 50)
            b.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.button_dict[attr_str] = b
            b.clicked.connect(lambda _, arg1=attr_str, arg2=current_color : self.show_color_dialog(arg1, arg2))
            b.setIcon(QtGui.QIcon(pix))

            layout.addWidget(b, index, 0)
            layout.addWidget(QtGui.QLabel(btn_str, self), index, 1)

        box = QtGui.QVBoxLayout()
        box.addLayout(grid)
        box.addStretch()
        box.addLayout(layout)
        self.setLayout(box)
        self.setLayout(box)
        self.show()

    def keyPressEvent(self, event):
        pass

    def any_change(self):
        cfg_comp = getattr(self._config, 'OpenGL')
        for i, (attr_str, label) in enumerate(self.values.iteritems()):
            setattr(cfg_comp, attr_str, float(self.lineedit_dict[attr_str].text()))

    def show_color_dialog(self, s, previous_color):
        color = QtGui.QColorDialog.getColor(initial=previous_color)
        if color.isValid():
            pix = QtGui.QPixmap(50, 50)
            pix.fill(color)
            self.button_dict[s].setIcon(QtGui.QIcon(pix))
            for i, clr_val in enumerate(color.getRgb()[:3]):
                tmp_cfg_clr = getattr(self._config, 'Colors')
                getattr(tmp_cfg_clr, s)[i] = clr_val / 255.


class ComputationSettingsPage(QtGui.QWidget):

    def __init__(self, parent, cfg):
        QtGui.QWidget.__init__(self, parent)
        self._config = cfg
        self.values = OrderedDict((('std_cutoff_radius', 'cutoff radius'), ))

        self.lineedit_dict = {}
        box  = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()
        for i, (attr_str, label) in enumerate(self.values.iteritems()):
            cfg_comp = getattr(self._config, 'Computation')

            l = QtGui.QLabel(label, self)
            t = QtGui.QLineEdit(self)
            t.setText(str(getattr(cfg_comp, attr_str)))
            self.lineedit_dict[attr_str] = t

            # self.connect(t, QtCore.SIGNAL("editingFinished()"), lambda who=attr_str: self.value_edited(who))
            t.textChanged.connect(self.any_change)
            grid.addWidget(l, i, 0)
            grid.addWidget(t, i, 1)
        box.addLayout(grid)
        box.addStretch()
        self.setLayout(box)
        self.show()

    def any_change(self):
        cfg_comp = getattr(self._config, 'Computation')
        for i, (attr_str, label) in enumerate(self.values.iteritems()):
            setattr(cfg_comp, attr_str, float(self.lineedit_dict[attr_str].text()))
    # def value_edited(self, s):
    #     cfg_comp = getattr(self._config, 'Computation')
    #     setattr(cfg_comp, s, float(self.lineedit_dict[s].text()))
    #     print 'VALUE EDITED'


class PathSettingsPage(QtGui.QWidget):

    def __init__(self, parent, cfg):
        QtGui.QWidget.__init__(self, parent)

        self._config = cfg
        self.path = OrderedDict((('cache_dir', 'Cache directory'),
                                ('result_dir', 'Result directory'),
                                ('ffmpeg', 'ffmpeg path')))

        self.lineedit_dict = {}
        box  = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()
        for i, (attr_str, label) in enumerate(self.path.iteritems()):
            cfg_path = getattr(self._config, 'Path')

            l = QtGui.QLabel(label, self)
            t = QtGui.QLineEdit(self)
            t.setText(getattr(cfg_path, attr_str))
            self.lineedit_dict[attr_str] = t

            self.connect(t, QtCore.SIGNAL("editingFinished()"), lambda who=attr_str: self.path_edited(who))
            grid.addWidget(l, i, 0)
            grid.addWidget(t, i, 1)
        box.addLayout(grid)
        box.addStretch()
        self.setLayout(box)
        self.show()

    def path_edited(self, s):
        cfg_path = getattr(self._config, 'Path')
        setattr(cfg_path, s, str(self.lineedit_dict[s].text()))


class SettingsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # temporary Configuration which saves the current changes
        self._tmp   = Configuration()
        self._tmp.read()

        vbox        = QtGui.QVBoxLayout()
        tab_widget  = QtGui.QTabWidget()
        graphics_page  = GraphicsSettingsPage(tab_widget, self._tmp)
        path_page   = PathSettingsPage(tab_widget, self._tmp)
        comp_page   = ComputationSettingsPage(tab_widget, self._tmp)

        # Ok, Cancel and Restore defaults Buttons
        ok          = QtGui.QPushButton('Ok', self)
        cancel      = QtGui.QPushButton('Cancel', self)
        restore_btn = QtGui.QPushButton('Restore defaults', self)

        ok.clicked.connect(self.ok)
        cancel.clicked.connect(self.cancel)
        restore_btn.clicked.connect(self.restore_defaults)

        tab_widget.addTab(graphics_page, 'graphics')
        tab_widget.addTab(path_page, 'path')
        tab_widget.addTab(comp_page, 'computation')

        vbox.addWidget(tab_widget)

        hbox    = QtGui.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(ok)
        hbox.addStretch()
        hbox.addWidget(cancel)
        hbox.addStretch()
        hbox.addWidget(restore_btn)
        hbox.addStretch()

        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.exec_()

    def ok(self):
        global config
        self._tmp.save()
        config.read()
        self.accept()
        for widget in QtGui.QApplication.topLevelWidgets():
            for gl_widget in widget.findChildren(GLWidget):
                gl_widget.update_needed = True
                QtGui.QApplication.postEvent(gl_widget, UpdateGLEvent())

    def restore_defaults(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
           "Are you sure to restore the defaults?", QtGui.QMessageBox.Yes |
           QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self._tmp   = Configuration()
            self._tmp.save()
            config.read()
            self.accept()

    def cancel(self):
        self.reject()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    config.read()
    dia = SettingsDialog()
    sys.exit(app.exec_())
