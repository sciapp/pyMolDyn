from PySide import QtGui
from gui.tabs.statistics.tree_list import TreeList
from gui.tabs.statistics.html_view import HTMLWindow

class StatisticsTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'statistics'-tab
    """

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "statistics", parent)
        self.setWidget(QtGui.QWidget())

        self.layout             = QtGui.QHBoxLayout()
        self.statistics_tab     = StatisticsTab(self.widget())

        self.layout.addWidget(self.statistics_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

    def update_results(self, results):
        self.statistics_tab.update_results(results)


class StatisticsTab(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.control = None
        hbox = QtGui.QHBoxLayout()

        self.html_view = HTMLWindow()
        self.tree_list = TreeList(self.html_view)
        self.html_view.tree_list = self.tree_list
        self.tree_list.setMinimumWidth(150)
        hbox.addWidget(self.tree_list)
        hbox.addWidget(self.html_view)
        self.adjustSize()
        self.setLayout(hbox)
        self.show()

    def update_results(self, results):
        self.html_view.update_results(results)
        self.tree_list.update_results(results)
