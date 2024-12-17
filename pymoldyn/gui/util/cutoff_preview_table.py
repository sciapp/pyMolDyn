# -*- coding: utf-8 -*-


from __future__ import absolute_import


import collections
from PySide6 import QtCore, QtWidgets
from .table_fit_mixin import TableFitMixin


class CutoffPreviewTable(QtWidgets.QTableWidget, TableFitMixin):
    def __init__(self, radii):
        QtWidgets.QTableWidget.__init__(self, 1, len(radii))
        TableFitMixin.__init__(self, scrollbar_extra_space=(0, 0))
        self._radii = collections.OrderedDict(sorted(radii.items()))    # Sorted by element name
        self._init_ui()

    def _init_ui(self):
        self.setHorizontalHeaderLabels(self._radii.keys())
        self.setVerticalHeaderLabels(('  ', ))
        self.setShowGrid(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        for i, cutoff_radius in enumerate(self._radii.itervalues()):
            item = QtWidgets.QTableWidgetItem(str(cutoff_radius))
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.setItem(0, i, item)
