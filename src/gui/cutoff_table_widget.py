# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from PyQt4 import QtCore, QtGui


class CutoffTableWidget(QtGui.QTableWidget):
    class CutoffLineEdit(QtGui.QLineEdit):
        focus_in = QtCore.pyqtSignal()

        def __init__(self, *args, **kwargs):
            super(CutoffTableWidget.CutoffLineEdit, self).__init__(*args, **kwargs)

        def focusInEvent(self, event):
            super(CutoffTableWidget.CutoffLineEdit, self).focusInEvent(event)
            self.focus_in.emit()

    text_edited = QtCore.pyqtSignal()

    def __init__(self, radii, parent=None):
        super(CutoffTableWidget, self).__init__(len(radii), 2, parent)
        self._radii = radii
        self._init_ui()

    def _init_ui(self):
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setHorizontalHeaderLabels(("Covalent Radius", "Cutoff Radius"))
        self.setVerticalHeaderLabels(self._radii.keys())
        for i in range(len(self._radii)):
            self.setItem(i, 0, QtGui.QTableWidgetItem())
            self.item(i, 0).setText(str(self._radii.values()[i]))
            current_line_edit = CutoffTableWidget.CutoffLineEdit()
            current_line_edit.textEdited.connect(self.text_edited)
            current_line_edit.focus_in.connect(lambda row_index=i: self._line_edit_focus_in(row_index))
            self.setCellWidget(i, 1, current_line_edit)
        self.setShowGrid(True)

    def _line_edit_focus_in(self, row_index):
        self.setCurrentIndex(self.model().index(row_index, 1))

    def keyPressEvent(self, event):
        key_code = event.key()
        if key_code == QtCore.Qt.Key_Tab or key_code == QtCore.Qt.Key_Backtab:
                index_increment = 1 if key_code == QtCore.Qt.Key_Tab else -1
                row_index = (self.currentIndex().row() + index_increment + len(self._radii)) % len(self._radii)
                self.setCurrentIndex(self.model().index(row_index, 1))
        else:
            super(CutoffTableWidget, self).keyPressEvent(event)
