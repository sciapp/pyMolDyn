from Pyside import QtGui, QtCore

class ProgressDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.initUI()

    def initUI():
        hbox = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel('starting calculation', self)
        self.progressbar = QtGui.QProgressBar(self)
        self.cancel_btn = QtGui.QPushButton('Cancel', self)
        self.cancel_btn.clicked.connect(self.cancel)

        hbox.addWidget(self.label)
        hbox.addWidget(self.progressbar)
        hbox.addWidget(self.cancel_btn)

        self.setLayout(hbox)

    def progress(value):
        self.progressbar.setValue(value)
        
    def print_step(self, text):
        self.label.setText()

    def cancel(self):
        pass

