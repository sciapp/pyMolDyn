# -*- coding: utf-8 -*-

import util.colored_exceptions
from gui import main_window
from core import volumes
from core.control import Control
from PySide import QtGui
from PySide import QtCore
import signal
import sys
import os
import core.calculation


def main():
    app = QtGui.QApplication(sys.argv)
    control = Control()
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

    control = window.control
    # settings = core.calculation.CalculationSettings({filename: [0]},
    #                                                 32,
    #                                                 domains=False,
    #                                                 surface_cavities=False,
    #                                                 center_cavities=False)
    # control.calculate(settings)
    # control.update()
    # window.updatestatus()

    # Let the Python interpreter run every 50ms...
    timer = QtCore.QTimer()
    timer.start(50)
    timer.timeout.connect(lambda: None)
    # ... to allow it to quit the application on SIGINT (Ctrl-C)
    signal.signal(signal.SIGINT, lambda *args: app.quit())

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
