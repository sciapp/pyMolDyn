from PySide import QtGui, QtCore

class ProgressDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.finished = False

        self.initUI()

    def initUI(self):
        hbox = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel('starting calculation', self)
        self.progressbar = QtGui.QProgressBar(self)
        self.cancel_btn = QtGui.QPushButton('Cancel', self)
        self.cancel_btn.clicked.connect(self.cancel)
        self.setMinimumSize(300,150)

        vbox = QtGui.QHBoxLayout()

        vbox.addStretch()
        vbox.addWidget(self.cancel_btn)
        vbox.addStretch()

        hbox.addWidget(self.label)
        hbox.addWidget(self.progressbar)
        hbox.addLayout(vbox)

        self.setLayout(hbox)

    def calculation_finished(self):
        self.finished = True
        #self.close_dialog()

    def progress(self, value):
        self.progressbar.setValue(value)

    def close_dialog(self):
        if self.finished:
            self.done(QtGui.QDialog.Accepted)
        else:
            self.done(QtGui.QDialog.Rejected)
        pass

    def print_step(self, *text):
        tmp = str(text[0])
        for t in text[1:]:
            tmp += ' {}'.format(t)
        self.label.setText(tmp)

    def cancel(self):
        print 'canceled calculation'
        self.close_dialog()