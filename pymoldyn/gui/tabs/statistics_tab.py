from PySide6 import QtWidgets

from .statistics.html_view import HTMLWindow
from .statistics.tree_list import TreeList


class StatisticsTabDock(QtWidgets.QDockWidget):
    """
    DockWidget for the 'statistics'-tab
    """

    def __init__(self, parent):
        QtWidgets.QDockWidget.__init__(self, "statistics", parent)
        self.setWidget(QtWidgets.QWidget())

        self.layout = QtWidgets.QHBoxLayout()
        self.statistics_tab = StatisticsTab(self.widget())

        self.layout.addWidget(self.statistics_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.setVisible(False)
        self.setMinimumWidth(350)

    def update_results(self, results):
        if results is not None:
            self.setVisible(True)
            self.statistics_tab.update_results(results)


class StatisticsTab(QtWidgets.QWidget):

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.control = None
        hbox = QtWidgets.QHBoxLayout()

        self.html_view = HTMLWindow()
        self.tree_list = TreeList(self.html_view)

        self.html_view.tree_list = self.tree_list
        self.tree_list.setMinimumWidth(150)
        hbox.addWidget(self.tree_list)
        hbox.addWidget(self.html_view)
        self.setLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.show()

    def update_results(self, results):
        self.html_view.update_results(results)
        self.tree_list.update_results(results)
