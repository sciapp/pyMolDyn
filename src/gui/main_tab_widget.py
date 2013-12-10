from PySide import QtCore, QtGui
from gui.file_tab import FileTab
from gui.file_tab import DragList

class TabWidget(QtGui.QTabWidget):

    def __init__(self, parent):
        QtGui.QTabWidget.__init__(self, parent)
        self.init_gui()

    def init_gui(self):
        self.file_tab           = FileTab(self)
        self.view_tab           = QtGui.QWidget(self)
        self.image_video_tab    = QtGui.QWidget(self)

        self.view_button        = QtGui.QPushButton('view button', self.view_tab)
        self.image_video_button = QtGui.QPushButton('image_video button', self.image_video_tab)

        for widget, name in [(self.file_tab, 'file'), (self.view_tab, 'view'), (self.image_video_tab, 'image/video')]:
            self.addTab(widget, name)

