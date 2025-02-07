import collections

from PySide6 import QtCore, QtWidgets

from .table_fit import TableFit


class CutoffPreviewTable(QtWidgets.QTableWidget):
    def __init__(self, radii):
        super().__init__(1, len(radii))
        self._table_fit = TableFit(self, scrollbar_extra_space=(0, 0))
        self._radii = collections.OrderedDict(sorted(radii.items()))  # Sorted by element name
        self._init_ui()

    def _init_ui(self):
        self.setHorizontalHeaderLabels(self._radii.keys())
        self.setVerticalHeaderLabels(("  ",))
        self.setShowGrid(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        for i, cutoff_radius in enumerate(self._radii.values()):
            item = QtWidgets.QTableWidgetItem(str(cutoff_radius))
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.setItem(0, i, item)
