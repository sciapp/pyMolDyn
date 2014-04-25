# -*- coding: utf-8 -*-

import util.colored_exceptions
from gui import main_window, visualization
from PySide import QtCore, QtGui
import sys
import volumes

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = main_window.MainWindow()
    app.setOrganizationName("Forschungszentrum Jülich GmbH")
    app.setOrganizationDomain("fz-juelich.de")
    app.setApplicationName("pyMolDyn 2")
    
    #box_size = 27.079855
    #volume = volumes.CubicVolume(box_size)
    volume = volumes.HexagonalVolume(17.68943, 22.61158)
    #window.show_dataset(volume, 'xyz/structure_c.xyz',1, 64, True)
    window.show_dataset(volume, 'xyz/hexagonal.xyz',1, 64, True)
    sys.exit(app.exec_())
