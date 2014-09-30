from PySide import QtGui


class StatisticsTabDock(QtGui.QDockWidget):
    """
        DockWidget for the 'statistics'-tab
    """

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, "statistics", parent)
        self.setWidget(QtGui.QWidget())

        self.layout             = QtGui.QHBoxLayout()
        self.image_video_tab    = StatisticsTab(self.widget())

        self.layout.addWidget(self.image_video_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

class StatisticsTab(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)