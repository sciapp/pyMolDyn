from PySide import QtCore, QtGui
import sys
from config.configuration import config


class SettingsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.colors = {
            'Background': config.Colors.BACKGROUND,
            'Bounding Box': config.Colors.BOUNDING_BOX,
            'Cavity': config.Colors.CAVITY,
            'Domain': config.Colors.DOMAIN,
            'Alt. Cavity': config.Colors.ALT_CAVITY
        }

        self.button_dict = {}
        hbox = QtGui.QVBoxLayout()
        for btn_str, btn_clr in self.colors.iteritems():
            pix = QtGui.QPixmap(50, 50)
            tmp = [int(f * 255) for f in btn_clr]
            pix.fill(QtGui.QColor(*tmp))

            b = QtGui.QPushButton(btn_str, self)
            self.button_dict[btn_str] = b
            self.connect(b, QtCore.SIGNAL("clicked()"), lambda who=btn_str: self.show_color_dialog(who))
            b.setIcon(QtGui.QIcon(pix))

            hbox.addWidget(b)
        self.setLayout(hbox)
        self.exec_()

    def show_color_dialog(self, s):
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            pix = QtGui.QPixmap(50, 50)
            pix.fill(color)
            self.button_dict[s].setIcon(QtGui.QIcon(pix))
        for i, clr_val in enumerate(list(color.toTuple()[:3])):
            self.colors[s][i] = clr_val / 255.
        config.save()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    config.read()
    dia = SettingsDialog()
    sys.exit(app.exec_())
