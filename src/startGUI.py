#!/usr/bin/env python
# -*- coding: utf-8 -*-

# use pythonic PyQt api (version 2)
import sip
API_NAMES = ("QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant")
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

import util.colored_exceptions
from gui import main_window
from core import volumes
from core.control import Control
from PyQt4 import QtGui
from PyQt4 import QtCore
import signal
import sys
import os
import core.calculation


def main():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
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


    filenames = sys.argv[1:]
    for filename in filenames:
        if filename:
            window.file_dock.file_tab.disable_files_in_menu_and_open(filename)
            window.update_submenu_recent_files()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
