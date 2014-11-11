# -*- coding: utf-8 -*-

from math import sin, cos, sqrt, pi
import gr3
from config.configuration import config
import core.calculation as calculation
import numpy as np
import os
from ctypes import c_int
from util.gl_util import create_perspective_projection_matrix, create_look_at_matrix, create_rotation_matrix_homogenous, create_translation_matrix_homogenous


class Visualization(object):
    def __init__(self):
        self.max_side_lengths = 1.0
        self.mat = np.eye(4)
        self.d = self.max_side_lengths * 2
        self.pos = np.array((0, 0, self.d))
        self.up = np.array((0, 1, 0))
        self.right = np.array((1, 0, 0))

        self.near = 0.1
        self.far = 3 * self.d
        self.fov = 45.0

        self.results = None
        self.settings = VisualizationSettings()

    def setresults(self, results):
        self.results = results
        max_side_lengths = max(results.atoms.volume.side_lengths)
        self.d = self.d / self.max_side_lengths * max_side_lengths 
        self.max_side_lengths = max_side_lengths
        self.far = 6 * max_side_lengths
        self.create_scene()
        self.set_camera(100, 100)

    def create_scene(self):
        show_domains = self.settings.show_domains
        show_surface_cavities = self.settings.show_cavities
        show_center_cavities = self.settings.show_alt_cavities
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

        if self.results is None:
            return

        edges = self.results.atoms.volume.edges
        num_edges = len(edges)
        edge_positions = [edge[0] for edge in edges]
        edge_directions = [[edge[1][i]-edge[0][i] for i in range(3)] for edge in edges]
        edge_lengths = [sum([c*c for c in edge])**0.5 for edge in edge_directions]
        edge_radius = min(edge_lengths)/200
        if self.settings.show_bounding_box:
            gr3.drawcylindermesh(num_edges, edge_positions, edge_directions, [config.Colors.bounding_box]*num_edges, [edge_radius]*num_edges, edge_lengths)
            corners = list(set([tuple(edge[0]) for edge in edges] + [tuple(edge[1]) for edge in edges]))
            num_corners = len(corners)
            gr3.drawspheremesh(num_corners, corners, [(1,1,1)]*num_edges, [edge_radius]*num_edges)

        if self.settings.show_atoms and not self.results.atoms is None:
            gr3.drawspheremesh(self.results.atoms.number,
                    self.results.atoms.positions,
                    [config.Colors.atoms] * self.results.atoms.number,
                    [edge_radius * 4] * self.results.atoms.number)

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
        zoom_cap = self.d + zoom_v*delta < (self.max_side_lengths)*4
        if self.d + zoom_v * delta > 0 and zoom_cap:
            self.d += zoom_v * delta

    def translate_mouse(self, dx, dy):
        trans_v = 1./1000
        diff_vec = (dx * self.mat[:3, 0] + (-1 * dy) * self.mat[:3,1])
        self.mat[:3, 3] += -1 * max(self.d,20) * trans_v * diff_vec

    def rotate_mouse(self, dx, dy):
        """
            calculates rotation to a given dx and dy on the screen
        """
        rightt = self.mat[:3, 0]
        upt = self.mat[:3, 1]
        pt = self.mat[:3, 2] * self.d
        rot_v = 1./13000
        diff_vec = (dx*rightt + (-1*dy)*upt)
        if all(diff_vec == np.zeros(3)):
            return
        rot_axis = np.cross(diff_vec, pt)
        rot_axis /= np.linalg.norm(rot_axis)
        # rotation matrix with min rotation angle
        m = create_rotation_matrix_homogenous(max(self.d,20)*rot_v*(dx**2+dy**2)**0.5, rot_axis[0], rot_axis[1], rot_axis[2])
        self.mat = m.dot(self.mat)

    def set_camera(self, width, height):
        """
            updates the shown scene after perspective has changed
        """
        rightt = self.mat[:3, 0]
        upt = self.mat[:3, 1]
        pt = self.mat[:3, 2] * self.d
        t = self.mat[:3, 3]

        self.proj_mat = create_perspective_projection_matrix(np.radians(self.fov), 1. * width / height, self.near, self.far)
        gr3.setcameraprojectionparameters(self.fov, self.near, self.far)
        self.lookat_mat = create_look_at_matrix(pt + t, t, upt)
        gr3.cameralookat(pt[0] + t[0], pt[1] + t[1], pt[2] + t[2], t[0], t[1], t[2], upt[0], upt[1], upt[2])

    def paint(self, width, height):
        """
            refreshes the OpenGL scene
        """
        self.set_camera(width, height)
        gr3.drawimage(0, width, 0, height, width, height, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)


class VisualizationSettings(object):
    def __init__(self, domains=False, cavities=True, alt_cavities=False, atoms=True, bounding_box=True):
        self.show_cavities = cavities
        self.show_domains = domains
        self.show_alt_cavities = alt_cavities
        self.show_atoms = atoms
        self.show_bounding_box = bounding_box
