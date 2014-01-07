# -*- coding: utf-8 -*-

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
    
    volume = volumes.HexagonalVolume(17.68943, 22.61158)
    window.show_dataset(volume, 'xyz/hexagonal.xyz',1)
    sys.exit(app.exec_())
