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
from computation.split_and_merge.util.graph import MergeGroup

cgr3.gr3_getviewmatrix.argtypes = [ctypes.POINTER(ctypes.c_float)]
cgr3.gr3_setviewmatrix.argtypes = [ctypes.POINTER(ctypes.c_float)]


class GridVisWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent, areas, merge_groups, mask, center, bounding_box_min, bounding_box_max,
                 camera_distance, *args, **kwargs):
        super(GridVisWidget, self).__init__(parent, *args, **kwargs)
        self._areas = areas
        self._merge_groups = merge_groups
        self._mask = mask
        inner_cell_positions = zip(*np.where(self._mask == 0))
        self._mask_node_positions = set((x, y, z) for x, y, z in inner_cell_positions
                                        if np.sum(self._mask[x-1:x+2, y-1:y+2, z-1:z+2]) > 9)
        node_positions = set((pos[0] + x, pos[1] + y, pos[2] + z)
                             for area in areas
                             for subarea in area
                             for pos, dim in subarea
                             for x, y, z in it.product(*(range(c) for c in dim)))
        self._mask_node_positions = tuple(self._mask_node_positions - node_positions)
        self._center = center
        self._cube_mesh = None
        self._show_box = False
        self._show_single_area = False
        self._show_subparts = False
        self._show_link = False
        self._show_translation = False
        self._show_merging_history = False
        self._current_area_index = 0
        self._current_merging_history = None
        self._current_merging_step_index = 0
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
        self._cube_mesh = create_cube()

    def resizeGL(self, width, height):
        pass

    def paintGL(self):
        gr3.clear()
        self._draw_scene()
        gr3.drawimage(0, self.width(), 0, self.height(), int(self.width()), int(self.height()),
                      gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)

    def _draw_scene(self):
        def draw_box():
            count_positions = len(self._mask_node_positions)
            mask_color = (0, 0, 1)
            gr3.drawmesh(self._cube_mesh, count_positions, self._mask_node_positions, count_positions*((0, 0, 1), ),
                         count_positions*((0, 1, 0), ), count_positions*(mask_color, ), count_positions*((1, 1, 1), ))

        def draw_link_vectors(area):
            center_points = tuple(np.mean(np.array([(pos[0] + x, pos[1] + y, pos[2] + z)
                                                    for pos, dim in subarea
                                                    for x, y, z in it.product(*(range(c) for c in dim))]), axis=0)
                                  for subarea in area)
            cone_positions = center_points[:-1]
            cone_vectors = tuple(c2 - c1 for c1, c2 in zip(center_points, center_points[1:]))
            cone_lengths = tuple(np.linalg.norm(c) for c in cone_vectors)
            cone_normalized_vectors = tuple(c / length for c, length in zip(cone_vectors, cone_lengths))
            count_positions = len(cone_positions)
            gr3.drawconemesh(count_positions, cone_positions, cone_normalized_vectors,
                             count_positions*((1, 0.7, 0.7), ), count_positions*((0.5, 0.5, 0.5), ), cone_lengths)

        def draw_translation_vectors(area, translation_vectors):
            center_points = tuple(np.mean(np.array([(pos[0] + x, pos[1] + y, pos[2] + z)
                                                    for pos, dim in subarea
                                                    for x, y, z in it.product(*(range(c) for c in dim))]), axis=0)
                                  for subarea in area)
            cone_positions, cone_vectors = zip(*[(c, t) for c, t in zip(center_points, translation_vectors)
                                                 if t != (0, 0, 0)])
            cone_lengths = tuple(np.linalg.norm(c) for c in cone_vectors)
            cone_normalized_vectors = tuple(c / length for c, length in zip(cone_vectors, cone_lengths))
            count_positions = len(cone_positions)
            gr3.drawconemesh(count_positions, cone_positions, cone_normalized_vectors,
                             count_positions*((0.7, 0.7, 1), ), count_positions*((0.5, 0.5, 0.5), ), cone_lengths)

        def draw_area(area, colors):
            colorize_subareas = not isinstance(colors, tuple)
            node_positions = [(pos[0] + x, pos[1] + y, pos[2] + z)
                              for subarea in area
                              for pos, dim in subarea
                              for x, y, z in it.product(*(range(c) for c in dim))]
            count_positions = len(node_positions)
            if colorize_subareas:
                count_positions_per_subarea = [sum(w * h * d for _, (w, h, d) in subarea) for subarea in area]
                colors = tuple(it.chain(*(count * (color, ) for count, color in
                                          zip(count_positions_per_subarea, colors))))
            else:
                colors = count_positions * (colors, )
            gr3.drawmesh(self._cube_mesh, count_positions, node_positions, count_positions*((0, 0, 1), ),
                         count_positions*((0, 1, 0), ), colors, count_positions*((1, 1, 1), ))

        def get_hsv_color_generator():
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

        def get_color_generator_for_merge_history(area):
            current_merging_step = self._current_merging_history[self._current_merging_step_index]
            subgroup_indices = tuple(subgroup_index for subgroup_index, subarea in enumerate(area)
                                     if self._merge_groups[subarea[0]]._instance_id in current_merging_step)
            for i in range(len(area)):
                color = (1, 0, 0) if i in subgroup_indices else (1, 1, 1)
                yield color

        color_generator = get_hsv_color_generator()
        if self._show_box:
            draw_box()
        if self._show_single_area:
            current_area = self._areas[self._current_area_index]
            if self._show_link and self._merge_groups is not None:
                draw_link_vectors(current_area)
            if self._show_translation and self._merge_groups is not None:
                current_translation_vectors = self._merge_groups[current_area[0][0]]._translation_vectors
                draw_translation_vectors(current_area, current_translation_vectors)
            if self._show_merging_history and self._merge_groups is not None:
                color_generator = get_color_generator_for_merge_history(current_area)
                draw_area(current_area, color_generator)
            elif self._show_subparts:
                draw_area(current_area, color_generator)
            else:
                for _ in range(self._current_area_index - 1):
                    color_generator.next()
                draw_area(current_area, color_generator.next())
        else:
            for area, color in zip(self._areas, color_generator):
                draw_area(area, color)

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
        self._show_box = True
        self.updateGL()

    def hide_box(self):
        self._show_box = False
        self.updateGL()

    def show_all_areas(self):
        self._show_single_area = False
        self.updateGL()

    def show_single_area(self):
        self._show_single_area = True
        self.updateGL()

    def show_next_area(self):
        if not self._show_merging_history:
            self._current_area_index += 1
            if self._current_area_index >= len(self._areas):
                self._current_area_index = 0
            new_index = self._current_area_index
        elif self._merge_groups is not None:
            self._current_merging_step_index += 1
            if self._current_merging_step_index >= len(self._current_merging_history):
                self._current_merging_step_index = 0
            new_index = self._current_merging_step_index
        else:
            new_index = self._current_area_index
        self.updateGL()
        return new_index

    def show_previous_area(self):
        if not self._show_merging_history:
            self._current_area_index -= 1
            if self._current_area_index < 0:
                self._current_area_index = len(self._areas) - 1
            new_index = self._current_area_index
        elif self._merge_groups is not None:
            self._current_merging_step_index -= 1
            if self._current_merging_step_index < 0:
                self._current_merging_step_index = len(self._current_merging_history) - 1
            new_index = self._current_merging_step_index
        else:
            new_index = self._current_area_index
        self.updateGL()
        return new_index

    def show_subparts(self):
        self._show_subparts = True
        self.updateGL()

    def hide_subparts(self):
        self._show_subparts = False
        self.updateGL()

    def show_link(self):
        self._show_link = True
        self.updateGL()

    def hide_link(self):
        self._show_link = False
        self.updateGL()

    def show_translation(self):
        self._show_translation = True
        self.updateGL()

    def hide_translation(self):
        self._show_translation = False
        self.updateGL()

    def show_merging_history(self):
        self._show_merging_history = True
        self._current_merging_step_index = 0
        self._current_merging_history = self._get_current_merging_history()
        self.updateGL()

    def hide_merging_history(self):
        self._show_merging_history = False
        self.updateGL()

    def _get_current_merging_history(self):
        if self._merge_groups is not None:
            merge_history = self._merge_groups.values()[0]._save_merge_history
            current_area = self._areas[self._current_area_index]
            relevant_merge_group_indices = tuple(self._merge_groups[subarea[0]]._instance_id
                                                 for subarea in current_area)
            relevant_history = tuple(merging_step for merging_step in merge_history
                                     if any(merge_group_index in merging_step
                                            for merge_group_index in relevant_merge_group_indices))
        else:
            relevant_history = None
        return relevant_history
