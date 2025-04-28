"""
Visualize Atoms and Cavities with GR3
"""

from ctypes import c_int

import gr3
import numpy as np
import numpy.linalg as la

from ..config.configuration import config
from ..util.gl_util import (
    create_look_at_matrix,
    create_perspective_projection_matrix,
    create_rotation_matrix_homogenous,
    create_translation_matrix_homogenous,
)


class Visualization(object):
    """
    Visualize Atoms and Cavities with GR3
    """

    def __init__(self, repaint_callback=None):
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
        self.usecurrentframebuffer = False
        if repaint_callback is not None:
            self._repaint_callback = repaint_callback
        else:
            self._repaint_callback = lambda: self.paint(self.width, self.height)
        #  self.assigned_opengl_context = None
        self._export_args = None

        self.results = None
        self.settings = VisualizationSettings()
        self.objectids = [None]

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
            self.repaint_callback()
        self.settings.visible_domain_indices = None
        self.settings.visible_surface_cavity_indices = None
        self.settings.visible_center_cavity_indices = None

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
        show_surface_cavities = self.settings.show_surface_cavities
        show_center_cavities = self.settings.show_center_cavities
        if show_center_cavities and self.results.center_cavities is not None:
            show_surface_cavities = False
        elif show_surface_cavities and self.results.surface_cavities is not None:
            show_domains = False

        self.objectids = [None]
        edges = self.results.atoms.volume.edges
        num_edges = len(edges)
        edge_positions = [edge[0] for edge in edges]
        edge_directions = [[edge[1][i] - edge[0][i] for i in range(3)] for edge in edges]
        edge_lengths = [sum([c * c for c in edge]) ** 0.5 for edge in edge_directions]
        edge_radius = min(edge_lengths) / 200
        if self.settings.show_bounding_box:
            gr3.drawcylindermesh(
                num_edges,
                edge_positions,
                edge_directions,
                [config.Colors.bounding_box] * num_edges,
                [edge_radius] * num_edges,
                edge_lengths,
            )
            corners = list(set([tuple(edge[0]) for edge in edges] + [tuple(edge[1]) for edge in edges]))
            num_corners = len(corners)
            gr3.drawspheremesh(
                num_corners,
                corners,
                [config.Colors.bounding_box] * num_corners,
                [edge_radius] * num_corners,
            )

        if self.settings.show_atoms and self.results.atoms is not None:
            visible_atom_indices = self.settings.visible_atom_indices
            if visible_atom_indices is not None:
                visible_atom_indices = [comp for comp in visible_atom_indices if 0 <= comp < self.results.atoms.number]
            else:
                visible_atom_indices = range(self.results.atoms.number)
            if len(visible_atom_indices) == 0:
                visible_atom_indices = None
            if visible_atom_indices is not None:
                visible_atom_indices = np.array(visible_atom_indices)
                gr3.drawspheremesh(
                    len(visible_atom_indices),
                    self.results.atoms.positions[visible_atom_indices],
                    self.results.atoms.colors[visible_atom_indices],
                    np.ones(len(visible_atom_indices)) * config.OpenGL.atom_radius,
                )
                if self.settings.show_bonds:
                    bonds = self.results.atoms.bonds
                    for start_index, target_indices in enumerate(bonds):
                        if start_index not in visible_atom_indices:
                            continue
                        target_indices = np.array([i for i in target_indices if i in visible_atom_indices])
                        if len(target_indices) == 0:
                            continue
                        start_position = self.results.atoms.positions[start_index]
                        target_positions = self.results.atoms.positions[target_indices]
                        directions = target_positions - start_position
                        bond_lengths = la.norm(directions, axis=1)
                        directions /= bond_lengths.reshape(len(directions), 1)
                        gr3.drawcylindermesh(
                            len(target_indices),
                            target_positions,
                            -directions,
                            [config.Colors.bonds] * self.results.atoms.number,
                            np.ones(bond_lengths.shape) * config.OpenGL.bond_radius,
                            bond_lengths,
                        )

        if self.results is None:
            return
        if show_domains and self.results.domains is not None:
            self.draw_cavities(
                self.results.domains,
                config.Colors.domain,
                "domain",
                self.settings.visible_domain_indices,
            )
        if show_surface_cavities and self.results.surface_cavities is not None:
            self.draw_cavities(
                self.results.surface_cavities,
                config.Colors.surface_cavity,
                "surface cavity",
                self.settings.visible_surface_cavity_indices,
            )
        if show_center_cavities and self.results.center_cavities is not None:
            self.draw_cavities(
                self.results.center_cavities,
                config.Colors.center_cavity,
                "center cavity",
                self.settings.visible_center_cavity_indices,
            )

    def draw_cavities(self, cavities, color, cavity_type, indices=None):
        if indices is None:
            indices = range(self.results.domains.number)
        for index in set(indices):
            if 0 <= index < len(cavities.triangles):
                triangles = cavities.triangles[index]
                gr3._gr3.gr3_setobjectid(gr3.c_int(len(self.objectids)))
                self.objectids.append((cavity_type, index))
                mesh = gr3.createmesh(
                    triangles.shape[1] * 3,
                    triangles[0, :, :, :],
                    triangles[1, :, :, :],
                    [color] * (triangles.shape[1] * 3),
                )
                gr3.drawmesh(mesh, 1, (0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 1, 1), (1, 1, 1))
                gr3.deletemesh(c_int(mesh.value))
        gr3._gr3.gr3_setobjectid(gr3.c_int(0))

    def zoom(self, delta):
        """
        Adjust the zoom level.

        **Parameters:**
            `delta` :
                the increment of the distance from the camera to the center
        """
        zoom_v = 1.0 / 20
        zoom_cap = self.d + zoom_v * delta < (self.max_side_lengths) * 4
        if self.d + zoom_v * delta > 0 and zoom_cap:
            self.d += zoom_v * delta

    def translate_mouse(self, dx, dy):
        """
        Translate the model.
        """
        trans_v = 1.0 / 1000
        trans_factor = trans_v * max(self.d, 20)
        m = create_translation_matrix_homogenous(-dx * trans_factor, dy * trans_factor, 0)
        self.mat = self.mat.dot(m)

    def set_focus_on(self, x, y, z):
        self.mat[:3, 3] = (x, y, z)

    def rotate_mouse(self, dx, dy):
        """
        Rotate the model according to a mouse movement (dx, dy) on the screen.
        """
        rot_v = 1.0 / 13000
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
        # rightt = self.mat[:3, 0]
        upt = self.mat[:3, 1]
        pt = self.mat[:3, 2] * self.d
        t = self.mat[:3, 3]

        self.proj_mat = create_perspective_projection_matrix(
            np.radians(self.fov), 1.0 * width / height, self.near, self.far
        )
        gr3.setcameraprojectionparameters(self.fov, self.near, self.far)
        self.lookat_mat = create_look_at_matrix(pt + t, t, upt)
        gr3.cameralookat(
            pt[0] + t[0],
            pt[1] + t[1],
            pt[2] + t[2],
            t[0],
            t[1],
            t[2],
            upt[0],
            upt[1],
            upt[2],
        )

    def assign_opengl_context(self, context):
        self.assigned_opengl_context = context

    def paint(self, width, height, usecurrentframebuffer=None, device_pixel_ratio=1):
        """
        Refresh the OpenGL scene.
        """
        self.width = width
        self.height = height
        self.set_camera(width, height)
        if usecurrentframebuffer is not None:
            self.usecurrentframebuffer = usecurrentframebuffer
        if self.usecurrentframebuffer:
            gr3.usecurrentframebuffer()
        if self._export_args is not None:
            gr3.export(*self._export_args)
            self._export_args = None
        else:
            gr3.drawimage(
                0,
                width * device_pixel_ratio,
                0,
                height * device_pixel_ratio,
                width,
                height,
                gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL,
            )

    def save_screenshot(self, file_name, width=3840, height=2160, first=True, last=True):
        """
        Save a screenshot in the given resolution.
        ``first`` and ``last`` can be used to indicate if the first or last screenshot is taken when
        multiple images are saved in a loop for example.
        """
        self._export_args = (file_name, width, height)
        self.repaint_callback()

    def get_object_at_2dposition(self, x, y):
        oid = gr3.c_int(0)
        gr3._gr3.gr3_selectid(
            gr3.c_int(x),
            gr3.c_int(y),
            gr3.c_int(self.width),
            gr3.c_int(self.height),
            gr3.byref(oid),
        )
        return self.objectids[oid.value]

    def get_object_at_3dposition(self, x, y, z):
        if self.results is None:
            return None
        if self.results.atoms is not None:
            positions = self.results.atoms.positions
            distances = la.norm(positions - (x, y, z), axis=1)
            nearest_atom_index = np.argmin(distances)

            # calculate atom radius
            edges = self.results.atoms.volume.edges
            edge_directions = [[edge[1][i] - edge[0][i] for i in range(3)] for edge in edges]
            edge_lengths = [sum([c * c for c in edge]) ** 0.5 for edge in edge_directions]
            edge_radius = min(edge_lengths) / 200
            atom_radius = 4 * edge_radius

            if 0.95 < distances[nearest_atom_index] / atom_radius < 1.05:
                return ("atom", nearest_atom_index)

    @property
    def repaint_callback(self):
        return self._repaint_callback

    @repaint_callback.setter
    def repaint_callback(self, repaint_callback):
        self._repaint_callback = repaint_callback


class VisualizationSettings(object):
    """
    Container for settings that control which part of the data is visualized.
    Attributes:

        `show_domains`

        `show_surface_cavities`

        `show_center_cavities`

        `show_atoms`

        `show_bounding_box`

    """

    def __init__(
        self,
        domains=False,
        show_surface_cavities=True,
        show_center_cavities=False,
        atoms=True,
        bonds=True,
        bounding_box=True,
        visible_atom_indices=None,
        visible_domain_indices=None,
        visible_surface_cavity_indices=None,
        visible_center_cavity_indices=None,
    ):
        self.show_domains = domains
        self.visible_domain_indices = visible_domain_indices
        self.show_surface_cavities = show_surface_cavities
        self.visible_surface_cavity_indices = visible_surface_cavity_indices
        self.show_center_cavities = show_center_cavities
        self.visible_center_cavity_indices = visible_center_cavity_indices
        self.show_atoms = atoms
        self.visible_atom_indices = visible_atom_indices
        self.show_bonds = bonds
        self.show_bounding_box = bounding_box
