# -*- coding: utf-8 -*-


from __future__ import absolute_import


from PyQt4 import QtGui, QtCore
from config.cutoff_history import cutoff_history
from config.cutoff_history import HistoryEntry
from gui.cutoff_history_table import CutoffHistoryTable


class CutoffHistoryDialog(QtGui.QDialog):
    def __init__(self, parent, elements, preferred_filenames_with_frames=None):
        super(CutoffHistoryDialog, self).__init__(parent)
        history = cutoff_history.filtered_history(elements,
                                                  preferred_filenames_with_frames=preferred_filenames_with_frames)
        self._init_ui(history)

    def _init_ui(self, history):
        self.gb_history = QtGui.QGroupBox('History')
        self.tw_cutoff = CutoffHistoryTable(history)
        self.pb_ok = QtGui.QPushButton('Ok')
        self.pb_ok.setEnabled(False)
        self.pb_cancel = QtGui.QPushButton('Cancel')

        self.la_main = QtGui.QVBoxLayout()
        self.la_history = QtGui.QVBoxLayout()
        self.la_ok_cancel = QtGui.QHBoxLayout()
        self.la_main.addWidget(self.gb_history)
        self.la_history.addWidget(self.tw_cutoff)
        self.la_ok_cancel.addStretch()
        self.la_ok_cancel.addWidget(self.pb_ok)
        self.la_ok_cancel.addStretch()
        self.la_ok_cancel.addWidget(self.pb_cancel)
        self.la_ok_cancel.addStretch()
        self.la_ok_cancel.setContentsMargins(0, 0, 0, 0)
        self.la_main.addLayout(self.la_ok_cancel)
        self.la_main.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.gb_history.setLayout(self.la_history)
        self.setLayout(self.la_main)

        self.tw_cutoff.itemSelectionChanged.connect(
            lambda *args: self.pb_ok.setEnabled(len(self.tw_cutoff.selectedIndexes()) > 0)
        )
        self.pb_ok.clicked.connect(lambda event: self.accept())
        self.pb_cancel.clicked.connect(lambda event: self.reject())

    def accept(self):
        cutoff_history.remove_list(self.tw_cutoff.history_entries_for_deletion)
        cutoff_history.save()
        return super(CutoffHistoryDialog, self).accept()

    @property
    def history(self):
        return self.tw_cutoff.history

    @property
    def selected_radii(self):
        return self.history[self.tw_cutoff.selectedIndexes()[0].row()].radii
