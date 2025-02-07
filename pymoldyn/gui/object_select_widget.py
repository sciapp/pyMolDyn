import re

from PySide6 import QtCore, QtGui, QtWidgets


class ObjectSelectWidget(QtWidgets.QWidget):
    state_changed = QtCore.Signal(bool)
    selection_indices_changed = QtCore.Signal(object)

    def __init__(self, text, parent, add_index_selector=True, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._has_index_selector = add_index_selector

        # Widgets
        self._activation_checkbox = QtWidgets.QCheckBox(text, self)
        if self._has_index_selector:
            self._selection_checkbox = QtWidgets.QCheckBox("only selected indices", self)
            self._index_selection = IndexSelectLineEdit(self)

        # Layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnMinimumWidth(0, 8)
        layout.addWidget(self._activation_checkbox, 0, 0, 1, 3)
        if self._has_index_selector:
            layout.addWidget(self._selection_checkbox, 1, 1)
            layout.addWidget(self._index_selection, 1, 2)
        self.setLayout(layout)

        # Signals
        self._activation_checkbox.stateChanged.connect(self._state_changed)
        if self._has_index_selector:
            self._selection_checkbox.stateChanged.connect(self._selection_toggled)
            self._index_selection.indices_changed.connect(self._selection_indices_changed)

        # State setup
        self._state_changed(check_state=False)

    @property
    def indices(self):
        if self._has_index_selector and self._selection_checkbox.isChecked():
            return self._index_selection.indices
        else:
            return None

    @indices.setter
    def indices(self, indices):
        if self._has_index_selector:
            self._index_selection.indices = indices

    def add_indices(self, indices):
        if self._has_index_selector:
            self._index_selection.add_indices(indices)

    def isChecked(self):
        return self._activation_checkbox.isChecked()

    def setChecked(self, checkState):
        return self._activation_checkbox.setChecked(checkState)

    def selection_checkbox_is_checked(self):
        return self._selection_checkbox.isChecked()

    def selection_checkbox_set_checked(self, check_state):
        return self._selection_checkbox.setChecked(check_state)

    def _state_changed(self, check_state):
        if self._has_index_selector:
            self._selection_checkbox.setEnabled(check_state)
            self._index_selection.setEnabled(check_state)
        self.state_changed.emit(check_state)

    def _selection_toggled(self, check_state):
        if self._index_selection.indices is not None:
            self.selection_indices_changed.emit(self.indices)

    def _selection_indices_changed(self, indices):
        if self._selection_checkbox.isChecked():
            self.selection_indices_changed.emit(indices)


class IndexSelectLineEdit(QtWidgets.QLineEdit):
    indices_changed = QtCore.Signal(object)
    TIMER_INTERVAL = 1000

    class Validator(QtGui.QValidator):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def validate(self, input, pos):
            return (
                (QtGui.QValidator.Acceptable if re.match(r"^[0-9,\s-]*$", input) else QtGui.QValidator.Invalid),
                input,
                pos,
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indices = None
        self._next_indices = None
        self.setValidator(IndexSelectLineEdit.Validator())
        self.indices_emit_timer = QtCore.QTimer(self)
        self.indices_emit_timer.setInterval(self.TIMER_INTERVAL)
        self.indices_emit_timer.setSingleShot(True)
        self.indices_emit_timer.timeout.connect(self._time_out)
        self.textEdited.connect(self._text_edited)

    @property
    def indices(self):
        return self._indices

    @indices.setter
    def indices(self, indices):
        def indices2string(indices):
            def range2string(range):
                if range is None:
                    return ""
                elif len(range) == 1:
                    start = range[0]
                    end = start
                else:
                    start, end = range
                if start == end:
                    return str(start + 1)
                else:
                    return "{:d}-{:d}".format(start + 1, end + 1)

            indices = list(set(indices))
            indices.sort()
            ranges = []
            if len(indices) == 0:
                current_range = None
            else:
                current_range = [indices[0]]
                previous_index = indices[0]
                for current_index in indices[1:]:
                    if current_index > previous_index + 1:
                        current_range.append(previous_index)
                        ranges.append(current_range)
                        current_range = [current_index]
                    previous_index = current_index
                current_range.append(previous_index)
            ranges.append(current_range)
            indices_string = ", ".join(map(range2string, ranges))
            return indices_string

        self.setText(indices2string(indices))
        self._indices = tuple(indices)
        if self.isEnabled():
            self.indices_changed.emit(self._indices)

    def add_indices(self, indices):
        if self._indices is not None:
            self.indices = set(self._indices) | set(indices)
        else:
            self.indices = indices

    def _text_edited(self):
        if self.indices_emit_timer.isActive():
            self.indices_emit_timer.stop()
        indices_from_line_edit = self._get_indices_from_line_edit()
        if indices_from_line_edit is not None:
            if len(indices_from_line_edit) > 0:
                self._next_indices = indices_from_line_edit
            else:
                self._next_indices = None
            self.indices_emit_timer.start()

    def _time_out(self):
        if self._next_indices != self._indices:
            self._indices = self._next_indices
            self.indices_changed.emit(self._indices)

    def _get_indices_from_line_edit(self):
        input_text = self.text().replace(" ", "")
        is_input_valid = re.match(r"^(\d+(-\d+)?(,\d+(-\d+)?)*)?$", input_text)
        if is_input_valid:
            parts = input_text.split(",") if input_text != "" else []
            indices = []
            indices.extend((int(comp) - 1 for comp in parts if "-" not in comp))  # single indices
            for comp in parts:
                if "-" in comp:  # index ranges
                    start, end = map(int, comp.split("-"))
                    indices.extend(range(start - 1, end))
            indices = list(set(indices))  # Eliminate duplicate entries
            indices.sort()
            return tuple(indices)
        else:
            return None
