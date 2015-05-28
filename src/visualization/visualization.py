# -*- coding: utf-8 -*-
"""
Visualize Atoms and Cavities with GR3
"""

from math import sin, cos, sqrt, pi
import gr3
from config.configuration import config
import core.calculation as calculation
import numpy as np
import numpy.linalg as la
import os
from ctypes import c_int
from util.gl_util import create_perspective_projection_matrix, create_look_at_matrix, create_rotation_matrix_homogenous, create_translation_matrix_homogenous

class Visualization(object):
    """
    Visualize Atoms and Cavities with GR3
    """
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

        self.width = 0
        self.height = 0

        self.results = None
        self.settings = VisualizationSettings()

    def setresults(self, results):
        """
        Set the results that will be displayed

        **Parameters:**
            `results` :
                :class:`core.data.Results` object to visualize
        """
        self.results = results
        max_side_lengths = max(results.atoms.volume.side_lengths)
        self.d = self.d / self.max_side_lengths * max_side_lengths
        self.max_side_lengths = max_side_lengths
        self.far = 6 * max_side_lengths
        self.create_scene()
        if self.width != 0 and self.height != 0:
            self.paint(self.width, self.height)

    def create_scene(self):
        """
        Create GR3 meshes. ``self.results`` contains the mesh data
        and in ``self.settings`` is specified which meshes shound be rendered.
        """

        c = config.Colors.background
        gr3.setbackgroundcolor(c[0], c[1], c[2], 1.0)
        gr3.clear()

        if self.results is None:
            return

        show_domains = self.settings.show_domains
        show_surface_cavities = self.settings.show_cavities
        show_center_cavities = self.settings.show_alt_cavities
        if show_center_cavities and self.results.center_cavities is not None:
            show_domains = False
            show_surface_cavities = False
        elif show_surface_cavities and self.results.surface_cavities is not None:
            show_domains = False

        edges = self.results.atoms.volume.edges
        num_edges = len(edges)
        edge_positions = [edge[0] for edge in edges]
        edge_directions = [[edge[1][i]-edge[0][i] for i in range(3)] for edge in edges]
        edge_lengths = [sum([c*c for c in edge])**0.5 for edge in edge_directions]
        edge_radius = min(edge_lengths)/200
        if self.settings.show_bounding_box:
            gr3.drawcylindermesh(num_edges, edge_positions, edge_directions,
                                 [config.Colors.bounding_box]*num_edges,
                                 [edge_radius]*num_edges, edge_lengths)
            corners = list(set([tuple(edge[0]) for edge in edges] + [tuple(edge[1]) for edge in edges]))
            num_corners = len(corners)
            gr3.drawspheremesh(num_corners, corners,
                               [config.Colors.bounding_box]*num_corners,
                               [edge_radius]*num_corners)

        if self.settings.show_atoms and self.results.atoms is not None:
            gr3.drawspheremesh(self.results.atoms.number,
                               self.results.atoms.positions,
                               self.results.atoms.colors,
                               [edge_radius * 4] * self.results.atoms.number)

            if self.settings.show_bonds:
                bonds = self.results.atoms.bonds
                for start_index, target_indices in enumerate(bonds):
                    if len(target_indices) == 0:
                        continue
                    start_position = self.results.atoms.positions[start_index]
                    target_positions = self.results.atoms.positions[target_indices]
                    directions = target_positions - start_position
                    bond_lengths = la.norm(directions, axis=1)
                    directions /= bond_lengths.reshape(len(directions), 1)
                    gr3.drawcylindermesh(len(target_indices),
                                         target_positions,
                                         -directions,
                                         [config.Colors.bonds] * self.results.atoms.number,
                                         np.ones(bond_lengths.shape)*edge_radius,
                                         bond_lengths)

        if self.results is None:
            return
        if show_domains and self.results.domains is not None:
            self.draw_cavities(self.results.domains, config.Colors.domain)
        if show_surface_cavities and self.results.surface_cavities is not None:
            self.draw_cavities(self.results.surface_cavities,
                               config.Colors.cavity)
        if show_center_cavities and self.results.center_cavities is not None:
            self.draw_cavities(self.results.center_cavities,
                               config.Colors.alt_cavity)

    def draw_cavities(self, cavities, color):
        for triangles in cavities.triangles:
            mesh = gr3.createmesh(triangles.shape[1] * 3,
                                  triangles[0, :, :, :],
                                  triangles[1, :, :, :],
                                  [color] * (triangles.shape[1] * 3))
            gr3.drawmesh(mesh, 1, (0, 0, 0), (0, 0, 1), (0, 1, 0),
                         (1, 1, 1), (1, 1, 1))
            gr3.deletemesh(c_int(mesh.value))

    def zoom(self, delta):
        """
        Adjust the zoom level.

        **Parameters:**
            `delta` :
                the increment of the distance from the camera to the center
        """
        zoom_v = 1./20
        zoom_cap = self.d + zoom_v*delta < (self.max_side_lengths)*4
        if self.d + zoom_v * delta > 0 and zoom_cap:
            self.d += zoom_v * delta

    def translate_mouse(self, dx, dy):
        """
        Translate the model.
        """
        trans_v = 1./1000
        trans_factor = trans_v * max(self.d, 20)
        m = create_translation_matrix_homogenous(-dx * trans_factor,
                                                  dy * trans_factor, 0)
        self.mat = self.mat.dot(m)

    def set_focus_on(self, x, y, z):
        self.mat[:3, 3] = (x, y, z)

    def rotate_mouse(self, dx, dy):
        """
        Rotate the model according to a mouse movement (dx, dy) on the screen.
        """
        rot_v = 1./13000
        if dx == 0 and dy == 0:
            return
        rot_axis = np.array((-dy, -dx, 0.0))
        rot_factor = max(self.d, 20) * rot_v * la.norm(rot_axis)
        # rotation matrix with min rotation angle
        m = create_rotation_matrix_homogenous(rot_factor, rot_axis[0], rot_axis[1], rot_axis[2])
        self.mat = self.mat.dot(m)

    def reset_view(self):
        self.mat = np.eye(4)

    def set_camera(self, width, height):
        """
        Update the shown scene after the perspective has changed.
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
        Refresh the OpenGL scene.
        """
        self.width = width
        self.height = height
        self.set_camera(width, height)
        gr3.drawimage(0, width, 0, height, width, height, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)

    def save_screenshot(self, file_name, width=3840, height=2160):
        """
        Save a screenshot in the given resolution.
        """
        gr3.export(file_name, width, height)

    def get_object_at_position(self, x, y, z):
        if self.results is None:
            return None
        if self.results.atoms is not None:
            positions = self.results.atoms.positions
            distances = la.norm(positions - (x, y, z), axis=1)
            nearest_atom_index = np.argmin(distances)

            # calculate atom radius
            edges = self.results.atoms.volume.edges
            edge_directions = [[edge[1][i]-edge[0][i] for i in range(3)] for edge in edges]
            edge_lengths = [sum([c*c for c in edge])**0.5 for edge in edge_directions]
            edge_radius = min(edge_lengths)/200
            atom_radius = 4*edge_radius

            if 0.95 < distances[nearest_atom_index]/atom_radius < 1.05:
                return ('atom', nearest_atom_index)


class VisualizationSettings(object):
    """
    Container for settings that control which part of the data is visualized.
    Attributes:

        `show_domains`

        `show_cavities`

        `show_alt_cavities`

        `show_atoms`

        `show_bounding_box`

    """
    def __init__(self, domains=False, cavities=True, alt_cavities=False,
                 atoms=True, bonds=True, bounding_box=True):
        self.show_domains = domains
        self.show_cavities = cavities
        self.show_alt_cavities = alt_cavities
        self.show_atoms = atoms
        self.show_bonds = bonds
        self.show_bounding_box = bounding_box
