# -*- coding: utf-8 -*-


from __future__ import absolute_import


import collections
from PyQt4 import QtGui, QtCore
from gui.util.table_fit_mixin import TableFitMixin


class CutoffHistoryTable(QtGui.QTableWidget, TableFitMixin):
    HEADER_LABELS = ('Filename', 'Frame', 'Time', 'Cutoff')

    class CutoffTable(QtGui.QTableWidget, TableFitMixin):
        def __init__(self, radii):
            QtGui.QTableWidget.__init__(self, 1, len(radii))
            TableFitMixin.__init__(self, scrollbar_extra_space=(0, 0))
            self._radii = collections.OrderedDict(sorted(radii.items()))    # Sorted by element name
            self._init_ui()

        def _init_ui(self):
            self.setHorizontalHeaderLabels(self._radii.keys())
            self.setVerticalHeaderLabels(('  ', ))
            self.setShowGrid(True)
            self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
            for i, cutoff_radius in enumerate(self._radii.itervalues()):
                item = QtGui.QTableWidgetItem(str(cutoff_radius))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                self.setItem(0, i, item)

    class EntryActionWidget(QtGui.QWidget):

        remove = QtCore.pyqtSignal()

        def __init__(self, parent=None):
            super(CutoffHistoryTable.EntryActionWidget, self).__init__(parent)
            self._init_ui()

        def _init_ui(self):
            self.bt_remove = QtGui.QPushButton(self.style().standardIcon(QtGui.QStyle.SP_TitleBarCloseButton), '')
            self.bt_remove.setFixedSize(30, 30)
            self.bt_remove.setFlat(True)
            self.bt_remove.clicked.connect(lambda event: self.remove.emit())
            self.la_main = QtGui.QHBoxLayout()
            self.la_main.addWidget(self.bt_remove)
            self.la_main.setContentsMargins(15, 0, 15, 0)
            self.setLayout(self.la_main)

    def __init__(self, history):
        QtGui.QTableWidget.__init__(self, len(history), len(self.HEADER_LABELS) + 1)
        TableFitMixin.__init__(self, size_hint_only=True, scrollbar_extra_space=(-1, 2))
        self._history = list(history)
        self._orig_index_to_row_index = range(len(self._history))
        self._indices_to_remove = set()
        self._init_ui()

    def _init_ui(self):
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalHeaderLabels(self.HEADER_LABELS + ('', ))
        self.setVerticalHeaderLabels(map(str, range(len(self._history))))
        self.setShowGrid(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        for i, entry in enumerate(self._history):
            for j, value in enumerate((entry.filename, entry.frame + 1, entry.time)):
                item = QtGui.QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                self.setItem(i, j, item)
            cutoff_table = CutoffHistoryTable.CutoffTable(entry.radii)
            self.setCellWidget(i, 3, cutoff_table)
            entry_action_widget = CutoffHistoryTable.EntryActionWidget()
            self.setCellWidget(i, 4, entry_action_widget)
            entry_action_widget.remove.connect(lambda history_index=i: self._remove_clicked(history_index))
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def remove_history_entry(self, row):
        return self.removeRow(row)

    def clear_history(self):
        self.setRowCount(0)
        self._indices_to_remove.add(range(len(self._history)))
        self._orig_index_to_row_index = len(self._orig_index_to_row_index) * [None]

    def removeRow(self, row):
        super(CutoffHistoryTable, self).removeRow(row)
        self._indices_to_remove.add(row)
        self._orig_index_to_row_index = (self._orig_index_to_row_index[:row] +
                                         [None] +
                                         [index - 1 if index is not None else None
                                          for index in self._orig_index_to_row_index[row+1:]])

    def _remove_clicked(self, history_index):
        self.removeRow(self._orig_index_to_row_index[history_index])

    @property
    def history(self):
        return [entry for i, entry in enumerate(self._history) if i in self._indices_to_remove]

    @property
    def history_entries_for_deletion(self):
        return [self._history[i] for i in sorted(self._indices_to_remove)]
