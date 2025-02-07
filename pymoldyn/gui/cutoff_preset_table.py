from PySide6 import QtCore, QtWidgets

from .util.cutoff_preview_table import CutoffPreviewTable
from .util.table_with_removeable_items import TableWithRemoveableEntries


class CutoffPresetTable(TableWithRemoveableEntries):
    HEADER_LABELS = ("Preset Name", "Cutoff")

    def __init__(self, presets):
        self._presets = list(presets)
        super().__init__(self.HEADER_LABELS, len(presets))
        self._orig_index_to_row_index = range(len(self._presets))
        self._indices_to_remove = set()
        self._init_ui()

    def _init_ui(self):
        pass

    @property
    def presets(self):
        return [entry for i, entry in enumerate(self._presets) if i in self._indices_to_remove]

    @property
    def preset_entries_for_deletion(self):
        return [self._presets[i] for i in sorted(self._indices_to_remove)]

    def entry_count(self):
        return len(self._presets)

    def entries(self):
        entries = []
        for i, presets_entry in enumerate(self._presets):
            current_row = []
            for j, value in enumerate((presets_entry.name,)):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                current_row.append(item)
            if isinstance(presets_entry.radii, float):
                cutoff_fixed_value = presets_entry.radii
                item = QtWidgets.QTableWidgetItem(str(cutoff_fixed_value))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                current_row.append(item)
            else:
                cutoff_table = CutoffPreviewTable(presets_entry.radii)
                current_row.append(cutoff_table)
            entries.append(tuple(current_row))
        return entries
