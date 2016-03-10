# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools as it
import numpy as np
from PyQt4 import QtCore, QtGui
from grid_vis_widget import GridVisWidget
from mouse_trackball import MouseTrackball
from mouse_trackball import create_translation_matrix_homogenous

CAMERA_DISTANCE = 100


class TwinViewWidget(QtGui.QWidget):
    def __init__(self, parent, non_translated_data, translated_data, *args, **kwargs):
        super(TwinViewWidget, self).__init__(parent, *args, **kwargs)
        self.non_translated_data, self.translated_data = self._filter_for_relevant_data(non_translated_data,
                                                                                        translated_data)
        center, bounding_box_min, bounding_box_max = self.get_bounding_box_and_center(non_translated_data)
        self.center = center
        self.bounding_box_min = bounding_box_min
        self.bounding_box_max = bounding_box_max
        self._trackball = MouseTrackball((0, 0, 0), 1)
        self._init_ui()

    @staticmethod
    def _filter_for_relevant_data(non_translated_data, translated_data):
        relevant_indices = tuple(i for i, (translated_area, non_translated_area)
                                 in enumerate(zip(translated_data, non_translated_data))
                                 if translated_area != non_translated_area)
        non_translated_data = [non_translated_data[i] for i in relevant_indices]
        translated_data = [translated_data[i] for i in relevant_indices]
        return non_translated_data, translated_data

    def _init_ui(self):
        self._main_layout = QtGui.QGridLayout()
        self._left_label = QtGui.QLabel('Non translated data:', self)
        self._left_label.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        self._main_layout.addWidget(self._left_label, 0, 0)
        self._right_label = QtGui.QLabel('Translated data:', self)
        self._right_label.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        self._main_layout.addWidget(self._right_label, 0, 1)
        self._left_view = GridVisWidget(self, self.non_translated_data, self.center, self.bounding_box_min,
                                        self.bounding_box_max, CAMERA_DISTANCE)
        self._left_view.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        self._main_layout.addWidget(self._left_view, 1, 0)
        self._right_view = GridVisWidget(self, self.translated_data, self.center, self.bounding_box_min,
                                         self.bounding_box_max, CAMERA_DISTANCE)
        self._right_view.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        self._main_layout.addWidget(self._right_view, 1, 1)
        self.setLayout(self._main_layout)

    @staticmethod
    def get_bounding_box_and_center(data):
        plain_nodes = tuple(node for area in data for subarea in area for node in subarea)
        node_positions = [(pos[0] + x, pos[1] + y, pos[2] + z) for pos, dim in plain_nodes
                          for x, y, z in it.product(*(range(c) for c in dim))]
        min_components = tuple(min(axis) for axis in zip(*node_positions))
        max_components = tuple(max(axis) for axis in zip(*node_positions))
        center = tuple((c1 + c2) // 2 for c1, c2 in zip(min_components, max_components))
        return center, min_components, max_components

    def on_mouse_press(self, event):
        x, y = (event.x(), event.y())
        self._trackball.start_trackball((2 / self.width() * x - 1, 1 - 2 / self.height() * y))

    def on_mouse_move(self, event):
        if event.buttons() != QtCore.Qt.NoButton:
            x, y = (event.x(), event.y())
            mx, my, mz = 0, 0, self.bounding_box_min[2] - CAMERA_DISTANCE - self.center[2]
            rotation_matrix = self._trackball.update_trackball((2 / self.width() * x - 1, 1 - 2 / self.height() * y))
            if rotation_matrix is not None:
                rotation_matrix = np.dot(create_translation_matrix_homogenous(mx, my, mz),
                                         np.dot(rotation_matrix, create_translation_matrix_homogenous(-mx, -my, -mz)))
                self._left_view.rotate(rotation_matrix)
                self._right_view.rotate(rotation_matrix)

    def on_key_press(self, event):
        key_to_method = {
            'b': 'show_box',
            'B': 'hide_box',
            'a': 'show_all_areas',
            'A': 'show_single_area',
            'n': 'show_next_area',
            'N': 'show_previous_area',
            'c': 'show_subparts',
            'C': 'hide_subparts'
        }

        key = unicode(event.text())
        if key in key_to_method:
            method_name = key_to_method[key]
            getattr(self, method_name)()

    def show_box(self):
        self.topLevelWidget().show_box = True
        self._left_view.show_box()
        self._right_view.show_box()

    def hide_box(self):
        self.topLevelWidget().show_box = False
        self._left_view.hide_box()
        self._right_view.hide_box()

    def show_all_areas(self):
        self.topLevelWidget().show_all_areas = True
        self._left_view.show_all_areas()
        self._right_view.show_all_areas()

    def show_single_area(self):
        self.topLevelWidget().show_all_areas = False
        self._left_view.show_single_area()
        self._right_view.show_single_area()

    def show_next_area(self):
        current_index = self._left_view.show_next_area()
        self._right_view.show_next_area()
        self.topLevelWidget().index = current_index

    def show_previous_area(self):
        current_index = self._left_view.show_previous_area()
        self._right_view.show_previous_area()
        self.topLevelWidget().index = current_index

    def show_subparts(self):
        self.topLevelWidget().show_subparts = True
        self._left_view.show_subparts()
        self._right_view.show_subparts()

    def hide_subparts(self):
        self.topLevelWidget().show_subparts = False
        self._left_view.hide_subparts()
        self._right_view.hide_subparts()
