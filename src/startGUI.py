# -*- coding: utf-8 -*-

import util.colored_exceptions
from gui import main_window
from visualization import visualization, volumes
import calculation
from PySide import QtCore, QtGui
import sys

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = main_window.MainWindow()
    app.setOrganizationName("Forschungszentrum Jülich GmbH")
    app.setOrganizationDomain("fz-juelich.de")
    app.setApplicationName("pyMolDyn 2")

    box_size = 27.079855
    volume = volumes.CubicVolume(box_size)
    #volume = volumes.HexagonalVolume(17.68943, 22.61158)
    window.show_dataset(volume, '../xyz/structure_c.xyz', 1, 32, False)
    #window.show_dataset(volume, '../xyz/hexagonal.xyz', 1, 32, False)
    sys.exit(app.exec_())
