#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import numpy as np
from PyQt4 import QtGui
from main_window import MainWindow


def main():
    app = QtGui.QApplication(sys.argv)
    data = np.load('../data/cavities.npz')
    mask = np.load('../data/mask.npz')['mask']
    mask[mask != 0] = 1
    non_translated_data, translated_data = data['non_translated_areas'], data['translated_areas']
    w = MainWindow(non_translated_data, translated_data, mask)
    w.resize(2000, 1000)
    w.setWindowTitle('Grid Visualization')
    screen_geometry = QtGui.QApplication.desktop().screenGeometry()
    x, y = (screen_geometry.width() - w.width()) / 2, (screen_geometry.height() - w.height()) / 2
    w.move(x, y)
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
