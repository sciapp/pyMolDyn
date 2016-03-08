# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math
import numpy as np


class MouseTrackball(object):
    def __init__(self, midpoint, radius):
        self.midpoint = tuple(map(float, midpoint))
        self.radius = float(radius)
        self.previous_pos = None

    def start_trackball(self, start_pos):
        self.previous_pos = start_pos

    def update_trackball(self, current_pos):
        def z_func(x, y):
            r_quad = (x-self.midpoint[0])**2 + (y-self.midpoint[1])**2
            if r_quad <= self.radius**2 / 2.0:
                return math.sqrt(self.radius**2 - r_quad)
            else:
                return self.radius**2 / (2*math.sqrt(r_quad))

        if np.all(current_pos == self.previous_pos):
            return None

        x1, y1 = self.previous_pos
        z1 = z_func(x1, y1)
        x2, y2 = current_pos
        z2 = z_func(x2, y2)

        v1 = np.array([x1, y1, z1])
        v1 /= np.linalg.norm(v1)
        v2 = np.array([x2, y2, z2])
        v2 /= np.linalg.norm(v2)
        n = np.cross(v1, v2)
        n /= np.linalg.norm(n)
        angle = math.acos(np.dot(v1, v2))

        self.previous_pos = current_pos

        rotation_matrix = create_rotation_matrix_homogenous(angle, n[0], n[1], n[2])

        return rotation_matrix


def create_translation_matrix_homogenous(x, y, z):
    matrix = np.zeros((4, 4), dtype=np.float32)
    for i in range(4):
        matrix[i, i] = 1
    matrix[:3, 3] = (x, y, z)
    return matrix


def create_rotation_matrix_homogenous(angle, x, y, z):
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[:3, :3] = create_rotation_matrix(angle, x, y, z)
    matrix[3, 3] = 1
    return matrix


def create_rotation_matrix(angle, x, y, z):
    x, y, z = np.array((x, y, z))/np.linalg.norm((x, y, z))
    matrix = np.zeros((3, 3), dtype=np.float32)
    cos = math.cos(angle)
    sin = math.sin(angle)
    matrix[0, 0] = x*x*(1-cos)+cos
    matrix[1, 0] = x*y*(1-cos)+sin*z
    matrix[0, 1] = x*y*(1-cos)-sin*z
    matrix[2, 0] = x*z*(1-cos)-sin*y
    matrix[0, 2] = x*z*(1-cos)+sin*y
    matrix[1, 1] = y*y*(1-cos)+cos
    matrix[1, 2] = y*z*(1-cos)-sin*x
    matrix[2, 1] = y*z*(1-cos)+sin*x
    matrix[2, 2] = z*z*(1-cos)+cos
    return matrix
