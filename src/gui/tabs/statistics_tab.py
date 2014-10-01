from PySide import QtGui
from gui.tabs.statistics.tree_list import TreeList
from gui.tabs.statistics.html_view import HTMLWindow, load_html

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

class StatisticsTab(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        hbox = QtGui.QHBoxLayout()
        tree_list = TreeList()
        html = load_html()
        html_view = HTMLWindow(html)
        hbox.addWidget(tree_list)
        hbox.addWidget(html_view)
        self.setLayout(hbox)
        self.show()