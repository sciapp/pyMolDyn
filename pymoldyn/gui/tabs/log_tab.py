import datetime
import logging

from PySide6 import QtCore, QtGui, QtWidgets

STYLE_SHEET = """
.default {
    color: #909090;
    font-weight: bold;
}
.info {
    color: blue;
    font-weight: bold;
}
.warning {
    color: #DAA520;
    font-weight: bold;
}
.error {
    color: red;
    font-weight: bold;
}
"""


class LogTabDock(QtWidgets.QDockWidget):
    """
    DockWidget for the 'log'-tab
    """

    def __init__(self, parent):
        QtWidgets.QDockWidget.__init__(self, "logging", parent)
        self.setWidget(QtWidgets.QWidget())

        self.layout = QtWidgets.QHBoxLayout()
        self.log_tab = LogTab(self.widget(), parent)

        self.layout.addWidget(self.log_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)

    def append_log(self, message, level=logging.WARNING):
        QtCore.QMetaObject.invokeMethod(
            self.log_tab,
            "append_log",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, message),
            QtCore.Q_ARG(int, level),
        )


class LogTab(QtWidgets.QWidget):
    """
    tab 'log' in the main widget
    """

    def __init__(self, parent, main_window):
        QtWidgets.QWidget.__init__(self, parent)
        self.main_window = main_window
        self.init_gui()

    def init_gui(self):
        self.vbox = QtWidgets.QVBoxLayout()

        self.log_area = QtWidgets.QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.document().setDefaultStyleSheet(STYLE_SHEET)

        self.vbox.addWidget(self.log_area)
        self.setLayout(self.vbox)

    @QtCore.Slot(str, int)
    def append_log(self, message, level=logging.WARNING):
        level_to_style_class = {
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
        }

        current_date_as_string = datetime.datetime.now().strftime("%m/%d/%y, %H:%M")

        self.log_area.insertHtml(
            (
                '<div><span class="{style_class}">{message_type} <span class="default">({date})</span>:</span>'
                " <span>{message}</span></div><br />"
            ).format(
                style_class=level_to_style_class[level],
                message_type=level_to_style_class[level].upper(),
                date=current_date_as_string,
                message=message,
            )
        )

        current_cursor = self.log_area.textCursor()
        current_cursor.movePosition(QtGui.QTextCursor.End)
        self.log_area.setTextCursor(current_cursor)
