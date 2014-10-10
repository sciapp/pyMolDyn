# -*- coding: utf-8 -*-

from math import sin, cos
import gr3
from core.calculation import calculated, CalculationResults
from config.configuration import config
import pybel
import numpy as np
import os
import sys
from gui.util.gl_util import create_perspective_projection_matrix, create_look_at_matrix, create_rotation_matrix_homogenous, create_translation_matrix_homogenous


class Visualization():

    def __init__(self, volume, filename, frame_nr, resolution, use_center_points):
        self.domain_meshes = []
        self.cavity_meshes = []
        self.center_cavity_meshes = []

        self.mat = np.eye(4)
        self.d = max(volume.side_lengths) * 2
        self.pos = np.array((0, 0, self.d))
        self.up = np.array((0, 1, 0))
        self.right = np.array((1, 0, 0))

        self.near = 0.1
        self.far = 3 * self.d
        self.fov = 45.0
        
        self.volume = volume
        generator = pybel.readfile("xyz", filename)
        try:
            for i in range(frame_nr):
                molecule = generator.next()
        except StopIteration:
            print 'Error: This frame does not exist.'
            sys.exit(0)
        self.atoms = molecule.atoms
        self.num_atoms = len(self.atoms)
        self.atom_positions = [atom.coords for atom in self.atoms]
        for atom_index in range(self.num_atoms):
            self.atom_positions[atom_index] = self.volume.get_equivalent_point(self.atom_positions[atom_index])

        self.calculated = calculated(filename, frame_nr, resolution, False)
        self.center_based_calculated = calculated(filename, frame_nr, resolution, True)

        if self.calculated:
            res_name = '{}{}.hdf5'.format(config.Path.result_dir, ''.join(os.path.basename(filename).split(".")[:-1]))
            cr = CalculationResults(res_name, frame_nr, resolution)
            self.max_domain_index = cr.number_of_domains
            self.domain_vertices_list = [t[0] for t in cr.domain_triangles]
            self.domain_normals_list = [t[1] for t in cr.domain_triangles]
            self.max_cavity_index = cr.number_of_multicavities
            self.cavity_vertices_list = [t[0] for t in cr.multicavity_triangles]
            self.cavity_normals_list = [t[1] for t in cr.multicavity_triangles]

        if use_center_points: 
            if self.center_based_calculated:
                self.max_center_cavity_index = cr.number_of_center_multicavities
                self.center_cavity_vertices_list = [t[0] for t in cr.center_multicavity_triangles]
                self.center_cavity_normals_list = [t[1] for t in cr.center_multicavity_triangles]
            else:
                use_center_points = False
        self.init(use_center_points)

    def init(self, use_center_points):
        if self.calculated:
            self.domain_meshes = []
            for domain_index in range(self.max_domain_index):
                domain_vertices = self.domain_vertices_list[domain_index]
                domain_normals = self.domain_normals_list[domain_index]
                num_domain_vertices = len(domain_vertices) * 3
                mesh = gr3.createmesh(num_domain_vertices, domain_vertices, domain_normals, [config.Colors.domain]*num_domain_vertices)
                self.domain_meshes.append(mesh)

            self.cavity_meshes = []
            for cavity_index in range(self.max_cavity_index):
                cavity_vertices = self.cavity_vertices_list[cavity_index]
                cavity_normals = self.cavity_normals_list[cavity_index]
                num_cavity_vertices = len(cavity_vertices) * 3
                mesh = gr3.createmesh(num_cavity_vertices, cavity_vertices, cavity_normals, [config.Colors.cavity]*num_cavity_vertices)
                self.cavity_meshes.append(mesh)

        if use_center_points:
            self.center_cavity_meshes = []
            for cavity_index in range(self.max_center_cavity_index):
    #        for cavity_index in range(self.max_center_cavity_index-1):  fixes Index Error 256K dataset
                center_cavity_vertices = self.center_cavity_vertices_list[cavity_index]
                center_cavity_normals = self.center_cavity_normals_list[cavity_index]
                num_center_cavity_vertices = len(center_cavity_vertices) * 3
                mesh = gr3.createmesh(num_center_cavity_vertices, center_cavity_vertices, center_cavity_normals, [config.Colors.alt_cavity]*num_center_cavity_vertices)
                self.center_cavity_meshes.append(mesh)

        self.create_scene()

        self.set_camera(100, 100)
        # gr3.export("test.html",800,800)

    def create_scene(self, show_cavities=True, center_based_cavities=False):
        if center_based_cavities and not self.center_based_calculated:
            return
        gr3.setbackgroundcolor(config.Colors.background[0], config.Colors.background[1], config.Colors.background[2], 1.0)
        gr3.clear()
        if self.calculated:
            if not show_cavities:
                for domain_index in range(self.max_domain_index):
                    gr3.drawmesh(self.domain_meshes[domain_index], 1, (0,0,0), (0,0,1), (0,1,0), config.Colors.domain, (1,1,1))
            else:
                if center_based_cavities and self.center_based_calculated:
                    for cavity_index in range(self.max_center_cavity_index):
                        gr3.drawmesh(self.center_cavity_meshes[cavity_index], 1, (0,0,0), (0,0,1), (0,1,0), config.Colors.alt_cavity, (1,1,1))
                else:
                    for cavity_index in range(self.max_cavity_index):
                        gr3.drawmesh(self.cavity_meshes[cavity_index], 1, (0,0,0), (0,0,1), (0,1,0), config.Colors.cavity, (1,1,1))

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
        gr3.drawspheremesh(len(self.atom_positions), self.atom_positions, [config.Colors.atoms]*len(self.atom_positions), [edge_radius*4]*len(self.atom_positions))

    def zoom(self, delta):
        """
            camera_zoom
        """
        zoom_v = 1./20
        zoom_cap = self.d + zoom_v*delta < max(self.volume.side_lengths)*4
        if self.d + zoom_v * delta > 0 and zoom_cap:
            self.d += zoom_v * delta

    def rotate_mouse(self, dx, dy):
        """
            calculates rotation to a given dx and dy on the screen
        """
        rot_v = 1./13000
        diff_vec = (dx*self.rightt + (-1*dy)*self.upt)
        if all(diff_vec == np.zeros(3)):
            return
        rot_axis = np.cross(diff_vec, self.pt)
        rot_axis /= np.linalg.norm(rot_axis)

        # rotation matrix with min rotation angle
        m = create_rotation_matrix_homogenous(max(self.d,20)*rot_v*(dx**2+dy**2)**0.5, rot_axis[0], rot_axis[1], rot_axis[2])
        self.mat = m.dot(self.mat)

    def set_camera(self, width, height):
        """
            updates the shown scene after perspective has changed
        """
        self.rightt = self.mat[:3, 0]
        self.upt = self.mat[:3, 1]
        self.pt = self.mat[:3, 2] * self.d
        self.t = self.mat[:3, 3]

        self.proj_mat = create_perspective_projection_matrix(np.radians(self.fov), 1. * width / height, self.near, self.far)
        gr3.setcameraprojectionparameters(self.fov, self.near, self.far)
        self.lookat_mat = create_look_at_matrix(self.pt+self.t, self.t, self.upt)
        gr3.cameralookat(self.pt[0]+self.t[2], self.pt[1]+self.t[1], self.pt[2]+self.t[2], self.t[0], self.t[1], self.t[2], self.upt[0], self.upt[1], self.upt[2])

    def paint(self, width, height):
        """
            refreshes the OpenGL scene
        """
        self.set_camera(width, height)
        gr3.drawimage(0, width, 0, height, width, height, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)

