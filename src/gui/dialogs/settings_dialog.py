from PySide import QtCore, QtGui
import sys
from config.configuration import config, Configuration


class SettingsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.colors = {
            'Background': 'BACKGROUND',
            'Bounding Box': 'BOUNDING_BOX',
            'Cavity': 'CAVITY',
            'Domain': 'DOMAIN',
            'Alt. Cavity': 'ALT_CAVITY'
        }

        self.button_dict = {}
        vbox = QtGui.QVBoxLayout()
        for btn_str, clr_str in self.colors.iteritems():

            pix = QtGui.QPixmap(50, 50)
            cfg_clr = getattr(config, 'Colors')
            tmp = [int(f * 255) for f in getattr(cfg_clr, clr_str)]
            pix.fill(QtGui.QColor(*tmp))

            b = QtGui.QPushButton(btn_str, self)
            self.button_dict[btn_str] = b
            self.connect(b, QtCore.SIGNAL("clicked()"), lambda who=btn_str: self.show_color_dialog(who))
            b.setIcon(QtGui.QIcon(pix))

            vbox.addWidget(b)

        # Ok and Cancel Buttons
        ok      = QtGui.QPushButton('Ok', self)
        ok.clicked.connect(self.ok)
        cancel  = QtGui.QPushButton('Cancel', self)
        cancel.clicked.connect(self.cancel)

        hbox    = QtGui.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(ok)
        hbox.addStretch()
        hbox.addWidget(cancel)
        hbox.addStretch()
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.exec_()

    def ok(self):
        config = self._tmp
        print self._tmp.Colors.BACKGROUND, config.Colors.BACKGROUND
        config.save()
        self.accept()

    def cancel(self):
        self.reject()

    def show_color_dialog(self, s):
        self._tmp = Configuration()
        self._tmp.read()
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            pix = QtGui.QPixmap(50, 50)
            pix.fill(color)
            self.button_dict[s].setIcon(QtGui.QIcon(pix))
        for i, clr_val in enumerate(list(color.toTuple()[:3])):
            tmp_cfg_clr = getattr(self._tmp, 'Colors')
            getattr(tmp_cfg_clr, self.colors[s])[i] = clr_val / 255.


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    config.read()
    dia = SettingsDialog()
    sys.exit(app.exec_())
