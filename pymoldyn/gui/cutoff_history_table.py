from PySide6 import QtCore, QtWidgets

from .util.cutoff_preview_table import CutoffPreviewTable
from .util.table_with_removeable_items import TableWithRemoveableEntries


class CutoffHistoryTable(TableWithRemoveableEntries):
    HEADER_LABELS = ("Filename", "Frame", "Time", "Cutoff")

    def __init__(self, history):
        self._history = list(history)
        super().__init__(self.HEADER_LABELS, len(history))
        self._orig_index_to_row_index = range(len(self._history))
        self._indices_to_remove = set()
        self._init_ui()

    def _init_ui(self):
        pass

    @property
    def history(self):
        return [entry for i, entry in enumerate(self._history) if i not in self._indices_to_remove]

    @property
    def history_entries_for_deletion(self):
        return [self._history[i] for i in sorted(self._indices_to_remove)]

    def entry_count(self):
        return len(self._history)

    def entries(self):
        entries = []
        for i, history_entry in enumerate(self._history):
            current_row = []
            for j, value in enumerate((history_entry.filename, history_entry.frame + 1, history_entry.time)):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                current_row.append(item)
            cutoff_table = CutoffPreviewTable(history_entry.radii)
            current_row.append(cutoff_table)
            entries.append(tuple(current_row))
        return entries
