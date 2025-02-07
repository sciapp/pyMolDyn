from PySide6 import QtCore, QtWidgets


class TableFit:
    DEFAULT_SCROLLBAR_EXTRA_SPACE = (16, 16)

    def __init__(self, table_widget, size_hint_only=False, scrollbar_extra_space=None):
        self._table_widget = table_widget
        self._table_widget.sizeHint = self.sizeHint
        if scrollbar_extra_space is None:
            self._scrollbar_extra_space = TableFit.DEFAULT_SCROLLBAR_EXTRA_SPACE
        else:
            self._scrollbar_extra_space = []
            for given_value, default_value in zip(scrollbar_extra_space, TableFit.DEFAULT_SCROLLBAR_EXTRA_SPACE):
                value = given_value if given_value >= 0 else default_value
                self._scrollbar_extra_space.append(value)
            self._scrollbar_extra_space = tuple(self._scrollbar_extra_space)

        if not size_hint_only:
            self._table_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            self._table_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self._table_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def sizeHint(self):
        horizontal_header = self._table_widget.horizontalHeader()
        vertical_header = self._table_widget.verticalHeader()
        width = horizontal_header.length() + vertical_header.width() + self._scrollbar_extra_space[0]
        height = vertical_header.length() + horizontal_header.height() + self._scrollbar_extra_space[1]
        return QtCore.QSize(width, height)
