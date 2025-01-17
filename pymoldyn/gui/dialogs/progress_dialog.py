from PySide6 import QtCore, QtWidgets


class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.finished = False

        self.initUI()

    def initUI(self):
        hbox = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel("starting calculation", self)
        self.progressbar = QtWidgets.QProgressBar(self)
        # self.cancel_btn = QtWidgets.QPushButton('Cancel', self)
        # self.cancel_btn.clicked.connect(self.cancel)
        self.setMinimumSize(300, 100)

        vbox = QtWidgets.QHBoxLayout()

        vbox.addStretch()
        # vbox.addWidget(self.cancel_btn)
        vbox.addStretch()

        hbox.addWidget(self.label)
        hbox.addWidget(self.progressbar)
        hbox.addLayout(vbox)

        self.setLayout(hbox)

    def calculation_finished(self):
        self.finished = True
        QtCore.QMetaObject.invokeMethod(self, "close_dialog", QtCore.Qt.QueuedConnection)

    def progress(self, value):
        QtCore.QMetaObject.invokeMethod(
            self.progressbar,
            "setValue",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(int, value),
        )

    @QtCore.Slot()
    def close_dialog(self):
        if self.finished:
            self.done(QtWidgets.QDialog.Accepted)
        else:
            self.done(QtWidgets.QDialog.Rejected)
        pass

    def print_step(self, *text):
        tmp = str(text[0])
        for t in text[1:]:
            tmp += " {}".format(t)
        self.label.setText(tmp)

    def cancel(self):
        print("canceled calculation")
        self.close_dialog()
