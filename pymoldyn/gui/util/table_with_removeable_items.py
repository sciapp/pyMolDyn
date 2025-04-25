from PySide6 import QtCore, QtWidgets

from .table_fit import TableFit


class TableWithRemoveableEntries(QtWidgets.QTableWidget):
    class EntryActionWidget(QtWidgets.QWidget):

        remove = QtCore.Signal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self._init_ui()

        def _init_ui(self):
            self.bt_remove = QtWidgets.QPushButton(
                self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton), ""
            )
            self.bt_remove.setFixedSize(30, 30)
            self.bt_remove.setFlat(True)
            self.bt_remove.clicked.connect(lambda event: self.remove.emit())
            self.la_main = QtWidgets.QHBoxLayout()
            self.la_main.addWidget(self.bt_remove)
            self.la_main.setContentsMargins(15, 0, 15, 0)
            self.setLayout(self.la_main)

    def __init__(self, header_labels, entry_count):
        super().__init__(entry_count, len(header_labels) + 1)
        self._table_fit = TableFit(self, size_hint_only=True, scrollbar_extra_space=(-1, 2))
        self._header_labels = header_labels
        self._row_index_to_entry_index = range(entry_count)
        self._entry_index_to_row_index = range(entry_count)
        self._indices_to_remove = set()
        TableWithRemoveableEntries._init_ui(self)  # Emulate static binding

    def _init_ui(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.setMaximumHeight(300)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalHeaderLabels(self._header_labels + ("",))
        self.setVerticalHeaderLabels(map(str, range(self.entry_count())))
        self.setShowGrid(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        for i, entry in enumerate(self.entries()):
            for j, item in enumerate(entry):
                if isinstance(item, QtWidgets.QTableWidgetItem):
                    self.setItem(i, j, item)
                else:
                    # item is an arbitrary widget that should be set as cell widget
                    self.setCellWidget(i, j, item)
            entry_action_widget = TableWithRemoveableEntries.EntryActionWidget()
            self.setCellWidget(i, len(entry), entry_action_widget)
            entry_action_widget.remove.connect(lambda entry_index=i: self._remove_clicked(entry_index))
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def remove_entry(self, row):
        return self.removeRow(row)

    def clear_entries(self):
        self.setRowCount(0)
        self._indices_to_remove.update(range(self.entry_count()))
        self._row_index_to_entry_index = []
        self._entry_index_to_row_index = len(self._entry_index_to_row_index) * [None]

    def removeRow(self, row):
        super(TableWithRemoveableEntries, self).removeRow(row)
        self._indices_to_remove.add(self._row_index_to_entry_index[row])
        del self._row_index_to_entry_index[row]
        self._entry_index_to_row_index = (
            self._entry_index_to_row_index[:row]
            + [None]
            + [index - 1 if index is not None else None for index in self._entry_index_to_row_index[row + 1 :]]
        )

    def _remove_clicked(self, entry_index):
        self.removeRow(self._entry_index_to_row_index[entry_index])

    def entry_count(
        self,
    ):  # Overriding properties in in a QObject class seems not to work...
        raise NotImplementedError

    def entries(self):
        """Returns a list of entries. A entry is a tuple of QTableWidgetItems (representing a table row).
        Instead of QTableWidgetItems, arbitrary widgets can be used which are set as cell widgets.
        """
        raise NotImplementedError
