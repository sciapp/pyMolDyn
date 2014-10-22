# -*- coding: utf-8 -*-

from math import sin, cos, sqrt, pi
import gr3
from config.configuration import config
import core.calculation as calculation
import numpy as np
import os
from ctypes import c_int

class Visualization(object):
    def __init__(self, volume, filename, frame_nr, resolution, use_center_points):
        #TODO: here is the transition from old to new
        self.volume = volume
        self.results = calculation.calculate_cavities(filename, frame_nr, volume, resolution, use_center_points)

        #TODO: can it work, when volume is not given initially?
        self.distance = max(self.volume.side_lengths) * 2
        self.mat = np.matrix(np.identity(4))
        #self.mat[2, 3] = 1 # +1 ?

        self.create_scene(False, False) #TODO: neccessary?

    @property
    def atoms(self):
        #TODO: remove, when atoms is removed from results
        if not self.results is None:
            return self.results.atoms
        else:
            return None

    def create_scene(self, \
            show_cavities=True, \
            show_center_cavities=False):
        show_surface_cavities = show_cavities
        if show_surface_cavities:
            show_domains = False
        if show_center_cavities:
            show_domains = False
            show_surface_cavities = False
        if not show_surface_cavities and not show_center_cavities:
            show_domains = True

        c = config.Colors.background
        gr3.setbackgroundcolor(c[0], c[1], c[2], 1.0)
        gr3.clear()

        edges = self.volume.edges
        num_edges = len(edges)
        edge_positions = [edge[0] for edge in edges]
        edge_directions = [[edge[1][i]-edge[0][i] for i in range(3)] for edge in edges]
        edge_lengths = [sum([c*c for c in edge])**0.5 for edge in edge_directions]
        edge_radius = min(edge_lengths)/200
        gr3.drawcylindermesh(num_edges, edge_positions, edge_directions, [config.Colors.bounding_box]*num_edges, [edge_radius]*num_edges, edge_lengths)
        corners = list(set([tuple(edge[0]) for edge in edges] + [tuple(edge[1]) for edge in edges]))
        num_corners = len(corners)
        gr3.drawspheremesh(num_corners, corners, [(1,1,1)]*num_edges, [edge_radius]*num_edges)
        if not self.atoms is None:
            gr3.drawspheremesh(self.atoms.number,
                    self.atoms.positions,
                    [config.Colors.atoms] * self.atoms.number,
                    [edge_radius * 4] * self.atoms.number)

        if self.results is None:
            return
        if show_domains and not self.results.domains is None:
            self.draw_cavities(self.results.domains, config.Colors.domain)
        if show_surface_cavities \
                and not self.results.surface_cavities is None:
            self.draw_cavities(self.results.surface_cavities, \
                    config.Colors.cavity)
        if show_center_cavities \
                and not self.results.center_cavities is None:
            self.draw_cavities(self.results.center_cavities, \
                    config.Colors.alt_cavity)

    def draw_cavities(self, cavities, color):
        for triangles in cavities.triangles:
            mesh = gr3.createmesh(triangles.shape[1] * 3, \
                    triangles[0, :, :, :],
                    triangles[1, :, :, :],
                    [color] * (triangles.shape[1] * 3))
            gr3.drawmesh(mesh, 1, (0, 0, 0), (0, 0, 1), (0, 1, 0),
                    (1, 1, 1), (1, 1, 1))
            gr3.deletemesh(c_int(mesh.value))

    def zoom(self, delta):
        zoom_v = 1./20
        zoom_cap = self.distance + zoom_v*delta < max(self.volume.side_lengths) * 4
        if self.distance + zoom_v * delta > 0 and zoom_cap:
            self.distance += zoom_v * delta

    def rotate_mouse(self, dx, dy):
        dy = -dy # screen to world coordinates
        norm = sqrt(dx**2 + dy**2)
        if norm > 1e-7:
            # rotation axis orthogonal to movement
            v = np.matrix((dy, -dx, 0.0, 0.0), dtype=np.float).T
            # transform to model coordinates
            v = np.dot(self.mat, v)
            nv = sqrt(v[0]**2 + v[1]**2 + v[2]**2)
            # rotate
            rm = self.rotmatrix(norm * pi / 1000, v / nv)
            self.mat = np.dot(rm, self.mat)

    def rotmatrix(self, angle, v):
        v = np.array(v).ravel()
        c = cos(angle)
        ic = 1.0 - c
        s = sin(angle)
        return np.matrix((
            (v[0] * v[0] * ic + c, \
             v[0] * v[1] * ic - v[2] * s, \
             v[0] * v[2] * ic + v[1] * s, \
             0.0),
            (v[1] * v[0] * ic + v[2] * s, \
             v[1] * v[1] * ic + c, \
             v[1] * v[2] * ic - v[0] * s, \
             0.0),
            (v[2] * v[0] * ic - v[1] * s, \
             v[2] * v[1] * ic + v[0] * s, \
             v[2] * v[2] * ic + c, \
             0.0),
            (0.0, \
             0.0, \
             0.0, \
             1.0)
        ))

    def paint(self, width, height):
        up = np.array(self.mat[:, 1]).ravel()
        p = np.array(self.mat[:, 2]).ravel() * self.distance

        gr3.cameralookat(p[0], p[1], p[2], 0, 0, 0, up[0], up[1], up[2])
        gr3.drawimage(0, width, 0, height, width, height, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)

