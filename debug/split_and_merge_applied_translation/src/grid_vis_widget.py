# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools as it
import colorsys
import ctypes
import gr3
import numpy as np
from gr3 import _gr3 as cgr3
from PyQt4 import QtCore, QtGui, QtOpenGL

cgr3.gr3_getviewmatrix.argtypes = [ctypes.POINTER(ctypes.c_float)]
cgr3.gr3_setviewmatrix.argtypes = [ctypes.POINTER(ctypes.c_float)]


class GridVisWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent, areas, center, bounding_box_min, bounding_box_max, camera_distance, *args, **kwargs):
        super(GridVisWidget, self).__init__(parent, *args, **kwargs)
        self._areas = areas
        self._center = center
        self._show_single_area = False
        self._current_area_index = 0
        self._bounding_box_min = bounding_box_min
        self._bounding_box_max = bounding_box_max
        self._camera_distance = camera_distance
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def initializeGL(self):
        def create_cube():
            cube_vertices = tuple(it.product((0, 1), repeat=3))
            triangle_vertex_indices = ((0, 6, 4), (0, 6, 2), (1, 7, 5), (1, 3, 7), (0, 5, 4), (0, 1, 5),
                                       (2, 7, 3), (2, 7, 6), (0, 2, 1), (1, 2, 3), (4, 7, 6), (4, 5, 7))
            triangle_vertices = tuple(cube_vertices[ind] for ind in it.chain(*triangle_vertex_indices))
            cube_surface_normals = ((0, 0, -1), (0, 0, 1), (0, -1, 0), (0, 1, 0), (-1, 0, 0), (1, 0, 0))
            triangle_normals = tuple(it.chain(*(6 * (normal, ) for normal in cube_surface_normals)))
            return gr3.createmesh(len(triangle_vertices), triangle_vertices, triangle_normals,
                                  len(triangle_vertices) * ((1, 1, 1), ))

        # self.setFormat(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers))
        gr3.init()
        gr3.setbackgroundcolor(0.25, 0.25, 0.25, 1)
        gr3.setcameraprojectionparameters(45, 1, 300)
        gr3.cameralookat(self._center[0], self._center[1], self._bounding_box_min[2] - self._camera_distance,
                         self._center[0], self._center[1], self._center[2],
                         0, 1, 0)
        gr3.setlightdirection(0, 0, 0)
        self.cube_mesh = create_cube()

    def resizeGL(self, width, height):
        pass

    def paintGL(self):
        gr3.clear()
        self._draw_scene()
        gr3.drawimage(0, self.width(), 0, self.height(), int(self.width()), int(self.height()),
                      gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)

    def _draw_scene(self):
        color_generator = self._get_color_generator()
        for i, (area, color) in enumerate(zip(self._areas, color_generator)):
            if not self._show_single_area or i == self._current_area_index:
                node_positions = [(pos[0] + x, pos[1] + y, pos[2] + z) for pos, dim in area
                                  for x, y, z in it.product(*(range(c) for c in dim))]
                count_positions = len(node_positions)
                gr3.drawmesh(self.cube_mesh, count_positions, node_positions, count_positions*((0, 0, 1), ),
                             count_positions*((0, 1, 0), ), count_positions*(color, ), count_positions*((1, 1, 1), ))

    def mousePressEvent(self, event):
        self.parent().on_mouse_press(event)

    def mouseMoveEvent(self, event):
        self.parent().on_mouse_move(event)

    def keyPressEvent(self, event):
        self.parent().on_key_press(event)

    def rotate(self, rotation_matrix):
        view_matrix = np.zeros((4, 4), dtype=np.float32, order='F')
        cgr3.gr3_getviewmatrix(view_matrix.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        view_matrix = np.dot(rotation_matrix, view_matrix)
        view_matrix = np.array(view_matrix, dtype=np.float32, order='F')
        cgr3.gr3_setviewmatrix(view_matrix.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        self.updateGL()

    def show_box(self):
        pass

    def hide_box(self):
        pass

    def show_all_areas(self):
        self._show_single_area = False
        self.updateGL()

    def show_single_area(self):
        self._show_single_area = True
        self.updateGL()

    def show_next_area(self):
        self._current_area_index += 1
        if self._current_area_index >= len(self._areas):
            self._current_area_index = 0
        self.updateGL()

    def show_previous_area(self):
        self._current_area_index -= 1
        if self._current_area_index < 0:
            self._current_area_index = len(self._areas) - 1
        self.updateGL()

    def show_diff(self):
        pass

    def disable_diff(self):
        pass

    @staticmethod
    def _get_color_generator():
        s, v = 0.8, 1.0

        def hsv_generator():
            color_range_queue = [(0.0, 0.5)]
            while len(color_range_queue) > 0:
                current_color_range = color_range_queue.pop(0)
                next_hue = sum(current_color_range) / 2.0
                yield next_hue
                yield next_hue + 0.5
                color_range_queue.append((0.0, next_hue))
                color_range_queue.append((next_hue, 0.5))

        for h in hsv_generator():
            yield colorsys.hsv_to_rgb(h, s, v)
