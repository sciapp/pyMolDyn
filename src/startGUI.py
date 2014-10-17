# -*- coding: utf-8 -*-

import util.colored_exceptions
from gui import main_window
from core import volumes, control
from PySide import QtGui
import sys

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    control = control.Control()
    window = main_window.MainWindow(control)

    app.setOrganizationName("Forschungszentrum Jülich GmbH")
    app.setOrganizationDomain("fz-juelich.de")
    app.setApplicationName("pyMolDyn 2")

#    filename = '../xyz/generated2.xyz'
#    filename = '../xyz/generated.xyz'
#    filename = '../xyz/traject_200.xyz'
#    filename = '../xyz/GST_111_196_bulk.xyz'
    filename = '../xyz/structure_c.xyz'
#    filename = '../xyz/hexagonal.xyz'
    volume = volumes.get_volume_from_file(filename)
    window.show_dataset(volume, filename, 1, 32)

    sys.exit(app.exec_())
