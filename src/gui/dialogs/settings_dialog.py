from PySide import QtCore, QtGui
import sys
from config.configuration import config, Configuration


class ColorSettingsPage(QtGui.QWidget):

    def __init__(self, parent, cfg):
        QtGui.QWidget.__init__(self, parent)

        self._config = cfg
        self.colors = {
            'background': 'Background',
            'bounding_box': 'Bounding Box',
            'cavity': 'Cavity',
            'domain': 'Domain',
            'alt_cavity': 'Alt. Cavity',
            'atoms': 'Atoms'
        }

        self.button_dict = {}
        vbox = QtGui.QVBoxLayout()
        vbox.setSpacing(5)
        for attr_str, btn_str in self.colors.iteritems():

            pix = QtGui.QPixmap(50, 50)
            cfg_clr = getattr(self._config, 'Colors')
            tmp = [int(f * 255) for f in getattr(cfg_clr, attr_str)]
            pix.fill(QtGui.QColor(*tmp))

            b = QtGui.QPushButton(btn_str, self)
            self.button_dict[attr_str] = b
            self.connect(b, QtCore.SIGNAL("clicked()"), lambda who=attr_str: self.show_color_dialog(who))
            b.setIcon(QtGui.QIcon(pix))

            tmp_hbox = QtGui.QHBoxLayout()
            tmp_hbox.addWidget(b)
            tmp_hbox.addStretch()
            vbox.addLayout(tmp_hbox)

        self.setLayout(vbox)
        self.show()

    def show_color_dialog(self, s):
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            pix = QtGui.QPixmap(50, 50)
            pix.fill(color)
            self.button_dict[s].setIcon(QtGui.QIcon(pix))
        for i, clr_val in enumerate(list(color.toTuple()[:3])):
            tmp_cfg_clr = getattr(self._config, 'Colors')
            getattr(tmp_cfg_clr, s)[i] = clr_val / 255.


class ComputationSettingsPage(QtGui.QWidget):

    def __init__(self, parent, cfg):
        QtGui.QWidget.__init__(self, parent)
        self._config = cfg
        self.values = {
            'atom_radius': 'atom radius'
        }

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
        self.path = {
            'result_dir': 'Result directory',
            'ffmpeg': 'ffmpeg path'
        }

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
        color_page  = ColorSettingsPage(tab_widget, self._tmp)
        path_page   = PathSettingsPage(tab_widget, self._tmp)
        comp_page   = ComputationSettingsPage(tab_widget, self._tmp)

        # Ok, Cancel and Restore defaults Buttons
        ok          = QtGui.QPushButton('Ok', self)
        cancel      = QtGui.QPushButton('Cancel', self)
        restore_btn = QtGui.QPushButton('Restore defaults', self)

        ok.clicked.connect(self.ok)
        cancel.clicked.connect(self.cancel)
        restore_btn.clicked.connect(self.restore_defaults)

        tab_widget.addTab(color_page, 'colors')
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
