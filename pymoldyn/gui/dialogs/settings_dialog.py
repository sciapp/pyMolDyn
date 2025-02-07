import sys
from collections import OrderedDict

from PySide6 import QtCore, QtGui, QtWidgets

from ...config.configuration import Configuration, config
from ...config.cutoff_history import cutoff_history
from ...config.cutoff_presets import cutoff_presets
from ..cutoff_history_table import CutoffHistoryTable
from ..cutoff_preset_table import CutoffPresetTable
from ..gl_widget import GLWidget, UpdateGLEvent


class GraphicsSettingsPage(QtWidgets.QWidget):

    def __init__(self, parent, cfg):
        QtWidgets.QWidget.__init__(self, parent)

        self._config = cfg
        self.values = OrderedDict(
            (
                ("atom_radius", "atom radius"),
                ("bond_radius", "bond radius"),
            )
        )

        self.lineedit_dict = {}
        grid = QtWidgets.QGridLayout()
        for i, (attr_str, label) in enumerate(self.values.items()):
            cfg_comp = getattr(self._config, "OpenGL")

            label = QtWidgets.QLabel(label, self)
            line_edit = QtWidgets.QLineEdit(self)
            line_edit.setText(str(getattr(cfg_comp, attr_str)))
            self.lineedit_dict[attr_str] = line_edit
            line_edit.textChanged.connect(self.any_change)
            grid.addWidget(label, i, 0)
            grid.addWidget(line_edit, i, 1)

        self.colors = OrderedDict(
            (
                ("background", "Background"),
                ("bounding_box", "Bounding Box"),
                ("bonds", "Bonds"),
                ("domain", "Cavity (domain)"),
                ("surface_cavity", "Cavity (surface method)"),
                ("center_cavity", "Cavity (Center method)"),
            )
        )

        self.button_dict = {}
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(5)
        for index, (attr_str, btn_str) in enumerate(self.colors.items()):

            pix = QtGui.QPixmap(50, 50)
            cfg_clr = getattr(self._config, "Colors")
            tmp = [int(f * 255) for f in getattr(cfg_clr, attr_str)]
            current_color = QtGui.QColor(*tmp)
            pix.fill(current_color)

            b = QtWidgets.QPushButton(None, self)
            b.setFixedSize(50, 50)
            b.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.button_dict[attr_str] = b
            b.clicked.connect(lambda _, arg1=attr_str, arg2=current_color: self.show_color_dialog(arg1, arg2))
            b.setIcon(QtGui.QIcon(pix))

            layout.addWidget(b, index, 0)
            layout.addWidget(QtWidgets.QLabel(btn_str, self), index, 1)

        box = QtWidgets.QVBoxLayout()
        box.addLayout(grid)
        box.addStretch()
        box.addLayout(layout)
        self.setLayout(box)
        self.setLayout(box)
        self.show()

    def keyPressEvent(self, event):
        pass

    def any_change(self):
        cfg_comp = getattr(self._config, "OpenGL")
        for i, (attr_str, label) in enumerate(self.values.items()):
            try:
                setattr(cfg_comp, attr_str, float(self.lineedit_dict[attr_str].text()))
            except ValueError:
                setattr(cfg_comp, attr_str, 0.0)

    def show_color_dialog(self, s, previous_color):
        color = QtWidgets.QColorDialog.getColor(initial=previous_color)
        if color.isValid():
            pix = QtGui.QPixmap(50, 50)
            pix.fill(color)
            self.button_dict[s].setIcon(QtGui.QIcon(pix))
            for i, clr_val in enumerate(color.getRgb()[:3]):
                tmp_cfg_clr = getattr(self._config, "Colors")
                getattr(tmp_cfg_clr, s)[i] = clr_val / 255.0


class ComputationSettingsPage(QtWidgets.QWidget):

    def __init__(self, parent, cfg):
        QtWidgets.QWidget.__init__(self, parent)
        self._config = cfg
        self.values = OrderedDict((("std_cutoff_radius", "default cutoff radius"),))

        self.lineedit_dict = {}
        box = QtWidgets.QVBoxLayout()
        grid = QtWidgets.QGridLayout()
        for i, (attr_str, label) in enumerate(self.values.items()):
            cfg_comp = getattr(self._config, "Computation")

            label = QtWidgets.QLabel(label, self)
            line_edit = QtWidgets.QLineEdit(self)
            line_edit.setText(str(getattr(cfg_comp, attr_str)))
            self.lineedit_dict[attr_str] = line_edit

            # self.connect(line_edit, QtCore.SIGNAL("editingFinished()"), lambda who=attr_str: self.value_edited(who))
            line_edit.textChanged.connect(self.any_change)
            grid.addWidget(label, i, 0)
            grid.addWidget(line_edit, i, 1)

        self.tw_cutoff_history = CutoffHistoryTable(cutoff_history.history)
        pb_clear_cutoff_history = QtWidgets.QPushButton(
            self.style().standardIcon(QtWidgets.QStyle.SP_TrashIcon),
            "Clear cutoff history",
        )
        pb_clear_cutoff_history.clicked.connect(self.clear_cutoff_history_requested)
        if len(cutoff_history.history) == 0:
            self.tw_cutoff_history.setVisible(False)
            pb_clear_cutoff_history.setVisible(False)

        self.tw_cutoff_presets = CutoffPresetTable(cutoff_presets.presets)
        pb_clear_cutoff_presets = QtWidgets.QPushButton(
            self.style().standardIcon(QtWidgets.QStyle.SP_TrashIcon),
            "Clear cutoff presets",
        )
        pb_clear_cutoff_presets.clicked.connect(self.clear_cutoff_presets_requested)
        if len(cutoff_presets.presets) == 0:
            self.tw_cutoff_presets.setVisible(False)
            pb_clear_cutoff_presets.setVisible(False)

        box.addLayout(grid)
        box.addWidget(self.tw_cutoff_history, 0, QtCore.Qt.AlignHCenter)
        box.addWidget(pb_clear_cutoff_history, 0, QtCore.Qt.AlignRight)
        box.addWidget(self.tw_cutoff_presets, 0, QtCore.Qt.AlignHCenter)
        box.addWidget(pb_clear_cutoff_presets, 0, QtCore.Qt.AlignRight)
        box.addStretch()
        self.setLayout(box)
        self.show()

    def clear_cutoff_history_requested(self):
        message = QtWidgets.QMessageBox()
        message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message.setText(
            "Do you really want to clear the cutoff radii history for all previous done calculations?\n\n"
            + "(The history data will be cleared when you hit the ok button of the settings dialog.)"
        )
        answer = message.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            self.tw_cutoff_history.clear_entries()

    def clear_cutoff_presets_requested(self):
        message = QtWidgets.QMessageBox()
        message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message.setText(
            "Do you really want to delete all cutoff presets?\n\n"
            + "(The presets will be removed irrevocably when you hit the ok button of the settings dialog.)"
        )
        answer = message.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            self.tw_cutoff_presets.clear_entries()

    def any_change(self):
        cfg_comp = getattr(self._config, "Computation")
        for i, (attr_str, label) in enumerate(self.values.items()):
            setattr(cfg_comp, attr_str, float(self.lineedit_dict[attr_str].text()))

    # def value_edited(self, s):
    #     cfg_comp = getattr(self._config, 'Computation')
    #     setattr(cfg_comp, s, float(self.lineedit_dict[s].text()))
    #     print 'VALUE EDITED'


class PathSettingsPage(QtWidgets.QWidget):

    def __init__(self, parent, cfg):
        QtWidgets.QWidget.__init__(self, parent)

        self._config = cfg
        self.path = OrderedDict(
            (
                ("cache_dir", "Cache directory"),
                ("result_dir", "Result directory"),
                ("ffmpeg", "ffmpeg path"),
            )
        )

        self.lineedit_dict = {}
        box = QtWidgets.QVBoxLayout()
        grid = QtWidgets.QGridLayout()
        for i, (attr_str, label) in enumerate(self.path.items()):
            cfg_path = getattr(self._config, "Path")

            label = QtWidgets.QLabel(label, self)
            line_edit = QtWidgets.QLineEdit(self)
            line_edit.setText(getattr(cfg_path, attr_str))
            self.lineedit_dict[attr_str] = line_edit

            line_edit.editingFinished.connect(lambda who=attr_str: self.path_edited(who))
            grid.addWidget(label, i, 0)
            grid.addWidget(line_edit, i, 1)
        box.addLayout(grid)
        box.addStretch()
        self.setLayout(box)
        self.show()

    def path_edited(self, s):
        cfg_path = getattr(self._config, "Path")
        setattr(cfg_path, s, str(self.lineedit_dict[s].text()))


class SettingsDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        # temporary Configuration which saves the current changes
        self._tmp = Configuration()
        self._tmp.read()

        vbox = QtWidgets.QVBoxLayout()
        tab_widget = QtWidgets.QTabWidget()
        graphics_page = GraphicsSettingsPage(tab_widget, self._tmp)
        path_page = PathSettingsPage(tab_widget, self._tmp)
        comp_page = ComputationSettingsPage(tab_widget, self._tmp)
        self.cutoff_history_entries_for_deletion = lambda: comp_page.tw_cutoff_history.history_entries_for_deletion
        self.cutoff_preset_entries_for_deletion = lambda: comp_page.tw_cutoff_presets.preset_entries_for_deletion

        # Ok, Cancel and Restore defaults Buttons
        ok = QtWidgets.QPushButton("Ok", self)
        cancel = QtWidgets.QPushButton("Cancel", self)
        restore_btn = QtWidgets.QPushButton("Restore defaults", self)

        ok.clicked.connect(self.ok)
        cancel.clicked.connect(self.cancel)
        restore_btn.clicked.connect(self.restore_defaults)

        tab_widget.addTab(graphics_page, "graphics")
        tab_widget.addTab(path_page, "path")
        tab_widget.addTab(comp_page, "computation")

        vbox.addWidget(tab_widget)

        hbox = QtWidgets.QHBoxLayout()
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
        cutoff_history.remove_list(self.cutoff_history_entries_for_deletion())
        cutoff_history.save()
        cutoff_presets.remove_list(self.cutoff_preset_entries_for_deletion())
        cutoff_presets.save()
        self.accept()
        for widget in QtWidgets.QApplication.topLevelWidgets():
            for gl_widget in widget.findChildren(GLWidget):
                gl_widget.update_needed = True
                QtWidgets.QApplication.postEvent(gl_widget, UpdateGLEvent())

    def restore_defaults(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Message",
            "Are you sure to restore the defaults?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self._tmp = Configuration()
            self._tmp.save()
            config.read()
            self.accept()

    def cancel(self):
        self.reject()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    config.read()
    dia = SettingsDialog()
    sys.exit(app.exec_())
