# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from PyQt4 import QtCore, QtGui
from twin_view_widget import TwinViewWidget


class MainWindow(QtGui.QMainWindow):
    def __init__(self, non_translated_data, translated_data, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self._init_ui(non_translated_data, translated_data)

    def _init_ui(self, non_translated_data, translated_data):
        self._grid_vis = TwinViewWidget(self, non_translated_data, translated_data)
        self.setCentralWidget(self._grid_vis)
