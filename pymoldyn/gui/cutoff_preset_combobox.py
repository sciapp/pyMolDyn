from PySide6 import QtCore

from ..config.cutoff_presets import cutoff_presets
from .util.labeled_combobox import LabeledComboBox


class CutoffPresetComboBox(LabeledComboBox):
    preset_selected = QtCore.Signal(object)

    def __init__(self, parent=None):
        super().__init__(label="Preset", parent=parent)
        self._presets = cutoff_presets.presets
        CutoffPresetComboBox._init_ui(self)  # Emulate static binding

    def _init_ui(self):
        for preset in self._presets:
            self.insertItem(len(self._presets), preset.name)
        self.activated.connect(self._on_entry_activated)
        if len(cutoff_presets.presets) == 0:
            self.setVisible(False)

    def discard_preset_choice(self):
        self.setCurrentIndex(0)

    def _on_entry_activated(self, index):
        self.preset_selected.emit(self._presets[index - 1])

    @property
    def selected_preset(self):
        selected_index = self.currentIndex()
        return self._presets[selected_index - 1]
