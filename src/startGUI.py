#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess


def start_batch():
        # The user actually wants to use startBatch.py instead of startGUI.py
        # This is implemented here as both Linux and OS X use completely
        # different ways to implement the pymoldyn executable, but both call
        # startGUI.py.
        script_directory = os.path.dirname(os.path.realpath(__file__))
        batch_script_path = os.path.join(script_directory, 'startBatch.py')
        args = [sys.executable, batch_script_path] + sys.argv[2:]
        sys.exit(subprocess.call(args))

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--batch':
    start_batch()


# use pythonic PyQt api (version 2)
import sip
API_NAMES = ("QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant")
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)

from gui import main_window
import core.file
from core import volumes
from core.control import Control
from PyQt4 import QtGui
from PyQt4 import QtCore
import signal
import core.calculation


def start_gui():
    core.file.SEARCH_PATH = os.getcwd()
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


def main():
    """A main function is required by shallow-appify"""
    start_gui()


if __name__ == '__main__':
    start_gui()
