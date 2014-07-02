from PySide import QtGui, QtCore

class ProgressDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.initUI()

    def initUI(self):
        hbox = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel('starting calculation', self)
        self.progressbar = QtGui.QProgressBar(self)
        self.cancel_btn = QtGui.QPushButton('Cancel', self)
        self.cancel_btn.clicked.connect(self.cancel)

        hbox.addWidget(self.label)
        hbox.addWidget(self.progressbar)
        hbox.addWidget(self.cancel_btn)

        self.setLayout(hbox)

    def progress(self, value):
        self.progressbar.setValue(value)
        
    def print_step(self, *text):
        tmp = str(text[0])
        for t in text[1:]:
            tmp += ' {}'.format(t)
        self.label.setText(tmp)

    def cancel(self):
        print 'canceled calculation'
        pass

