from PySide6 import QtWidgets

from .gl_widget import GLWidget
from .histogram_widget import HistogramWidget
from .pdf_widget import PDFWidget


class GLStack(QtWidgets.QStackedWidget):
    def __init__(self, parent, main_window):
        QtWidgets.QStackedWidget.__init__(self, parent)
        self.parent = parent
        self.control = parent.control
        self.gl_widget = GLWidget(self, main_window)
        self.pdf_widget = PDFWidget(self)
        self.histogram_widget = HistogramWidget(self)

        self.addWidget(self.gl_widget)
        self.addWidget(self.pdf_widget)
        self.addWidget(self.histogram_widget)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.show()

    def activate(self, index):
        self.setCurrentIndex(index)
        self.widget(index).activate()

    def updatestatus(self):
        for index in range(self.count()):
            widget = self.widget(index)
            widget.updatestatus()
