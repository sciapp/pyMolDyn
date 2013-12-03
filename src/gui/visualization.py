# -*- coding: utf-8 -*-

import sys
from math import pi, sin, cos, acos
import numpy as np
import gr3
import pybel
import volumes
import os.path
from calculation import *

class Visualization():

    def __init__(self, volume, filename, frame_nr):
        self.domain_meshes = []
        self.cavity_meshes = []
        
        self.mat = np.array(([1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]))
        self.d = max(volume.side_lengths)*2
        self.pos = np.array((0, 0, self.d))
        self.up = np.array((0, 1, 0))
        self.right = np.array((1, 0, 0))
        
        self.volume = volume
        generator = pybel.readfile("xyz", filename)
        try:
            for i in range(frame_nr):
                molecule = generator.next()
        except StopIteration:
            if frame_nr > n:
                print 'Error: This frame does not exist.'
                sys.exit(0)
        self.atoms = molecule.atoms
        self.num_atoms = len(self.atoms)
        self.atom_positions = [atom.coords for atom in self.atoms]
        for atom_index in range(self.num_atoms):
            self.atom_positions[atom_index] = self.volume.get_equivalent_point(self.atom_positions[atom_index])

        res_name = "results/"+''.join(os.path.basename(filename).split(".")[:-1])+str(frame_nr)+"_cc.hdf5"
        cr = CalculationResults(res_name)
        
        self.max_domain_index = cr.number_of_domains
        self.domain_vertices_list = [t[0] for t in cr.domain_triangles]
        self.domain_normals_list = [t[1] for t in cr.domain_triangles]
        self.max_cavity_index = cr.number_of_multicavities
        self.cavity_vertices_list = [t[0] for t in cr.multicavity_triangles]
        self.cavity_normals_list = [t[1] for t in cr.multicavity_triangles]
        self.max_center_cavity_index = cr.number_of_center_multicavities
        self.center_cavity_vertices_list = [t[0] for t in cr.center_multicavity_triangles]
        self.center_cavity_normals_list = [t[1] for t in cr.center_multicavity_triangles]
        
        self.init()

    def init(self):
        self.domain_meshes = []
        for domain_index in range(self.max_domain_index):
            domain_vertices = self.domain_vertices_list[domain_index]
            domain_normals = self.domain_normals_list[domain_index]
            num_domain_vertices = len(domain_vertices)*3
            mesh = gr3.createmesh(num_domain_vertices, domain_vertices, domain_normals, [(1,1,1)]*num_domain_vertices)
            self.domain_meshes.append(mesh)
            
        self.cavity_meshes = []
        for cavity_index in range(self.max_cavity_index):
            cavity_vertices = self.cavity_vertices_list[cavity_index]
            cavity_normals = self.cavity_normals_list[cavity_index]
            num_cavity_vertices = len(cavity_vertices)*3
            mesh = gr3.createmesh(num_cavity_vertices, cavity_vertices, cavity_normals, [(1,1,1)]*num_cavity_vertices)
            self.cavity_meshes.append(mesh)
            
        self.center_cavity_meshes = []
        for cavity_index in range(self.max_center_cavity_index):
            center_cavity_vertices = self.center_cavity_vertices_list[cavity_index]
            center_cavity_normals = self.center_cavity_normals_list[cavity_index]
            num_center_cavity_vertices = len(center_cavity_vertices)*3
            mesh = gr3.createmesh(num_center_cavity_vertices, center_cavity_vertices, center_cavity_normals, [(1,1,1)]*num_center_cavity_vertices)
            self.center_cavity_meshes.append(mesh)

        self.create_scene()
        
#        d = max(self.volume.side_lengths)*2
#        gr3.cameralookat(d*math.sin(self.yrot),0,d*math.cos(self.yrot), 0,0,0, 0,1,0)
        self.set_camera()
        gr3.export("test.html",800,800)

    def create_scene(self, show_cavities=True, center_based_cavities=False):
        global domain_meshes
        global cavity_meshes
        global center_cavity_meshes
        
        gr3.clear()
        if not show_cavities:
            for domain_index in range(self.max_domain_index):
                gr3.drawmesh(self.domain_meshes[domain_index], 1, (0,0,0), (0,0,1), (0,1,0), (0,1,0.5), (1,1,1))
        else:
            if not center_based_cavities:
                for cavity_index in range(self.max_cavity_index):
                    gr3.drawmesh(self.cavity_meshes[cavity_index], 1, (0,0,0), (0,0,1), (0,1,0), (0.2,0.4,1), (1,1,1))
            else:
                for cavity_index in range(self.max_center_cavity_index):
                    gr3.drawmesh(self.center_cavity_meshes[cavity_index], 1, (0,0,0), (0,0,1), (0,1,0), (0.9,0.4,0.2), (1,1,1))

        edges = self.volume.edges
        num_edges = len(edges)
        edge_positions = [edge[0] for edge in edges]
        edge_directions = [[edge[1][i]-edge[0][i] for i in range(3)] for edge in edges]
        edge_lengths = [sum([c*c for c in edge])**0.5 for edge in edge_directions]
        edge_radius = min(edge_lengths)/200
        gr3.drawcylindermesh(num_edges, edge_positions, edge_directions, [(1,1,1)]*num_edges, [edge_radius]*num_edges, edge_lengths)
        corners = list(set([tuple(edge[0]) for edge in edges] + [tuple(edge[1]) for edge in edges]))
        num_corners = len(corners)
        gr3.drawspheremesh(num_corners, corners, [(1,1,1)]*num_edges, [edge_radius]*num_edges)
        gr3.drawspheremesh(len(self.atom_positions), self.atom_positions, [(1,1,1)]*len(self.atom_positions), [edge_radius*4]*len(self.atom_positions))
        
    def process_key(self, key):
        if key == 'right':
            self.xrot += pi/180*10
        elif key == 'left':
            self.xrot -= pi/180*10
        elif key == 'd':
            self.create_scene(False)
        elif key == 'c':
            self.create_scene(True) 
        elif key == 'f':
            self.create_scene(True,True)

    def zoom(self, delta):
        zoom_v = 1./20
        if self.pos[2] + zoom_v*delta > 0:
            self.pos[2] += zoom_v*delta

    def get_rotation_matrix(self, n, alpha):
        a = alpha
        print 'norm',np.linalg.norm(n)
        rot_mat = np.array(([n[0]**2*(1-cos(a)) + cos(a),               n[0]*n[1]*(1-cos(a)) - n[2]*sin(a),     n[0]*n[2]*(1-cos(a)) + n[1]*sin(a)],
                            [n[0]*n[1]*(1-cos(a)) - n[2]*sin(a),        n[1]**2*(1-cos(a)) + cos(a),            n[1]*n[2]*(1-cos(a)) - n[0]*sin(a)],
                            [n[2]*n[0]*(1-cos(a)) - n[1]*sin(a),        n[2]*n[1]*(1-cos(a)) + n[0]*sin(a),     n[2]**2*(1-cos(a)) + cos(a)]))
#        print 'n1',np.linalg.norm(rot_mat[:,0])
#        print 'n2',np.linalg.norm(rot_mat[:,1])
#        print 'n3',np.linalg.norm(rot_mat[:,2])
#        print 'HAHA',np.linalg.norm(rot_mat)
        return rot_mat

    def rotate_mouse(self, dx, dy):
        rot_v = 1./100
        dx *= rot_v
        dy *= rot_v
        diff_vec = (dx*self.rightt + (-1*dy)*self.upt)
        if all(diff_vec == np.zeros(3)):
            return
#        print self.right, 'norm', np.linalg.norm(self.right)
        rot_axis = np.cross(diff_vec, self.pt)
        rot_axis = rot_axis/np.linalg.norm(rot_axis)

        m = self.get_rotation_matrix(rot_axis, 0.05)
        self.mat = m.dot(self.mat)
        self.mat[:,0] /= np.linalg.norm(self.mat[:,0])
        self.mat[:,1] /= np.linalg.norm(self.mat[:,1])
        self.mat[:,2] /= np.linalg.norm(self.mat[:,2])

    def get_rotation_angle(self, v1, v2):
        if all(v1 == np.zeros(2)) or all(v2 == np.zeros(2)):
            return 0
        return acos((v1.dot(v2))/(np.linalg.norm(v1)*np.linalg.norm(v2)))

    def set_camera(self):
        print 'n1',np.linalg.norm(self.mat[:,0])
        print 'n2',np.linalg.norm(self.mat[:,1])
        print 'n3',np.linalg.norm(self.mat[:,2])
        self.pt = np.dot(self.mat, self.pos)
        #self.upt = np.dot(self.mat, self.up)
        #self.rightt = np.dot(self.mat, self.right)
        self.rightt = self.mat[:,0]
        self.upt = self.mat[:,1]
        print np.dot(self.upt,self.rightt)
        self.pt = self.mat[:,2]*self.d

        gr3.cameralookat(self.pt[0], self.pt[1], self.pt[2], 0, 0, 0, self.upt[0], self.upt[1], self.upt[2])

    def paint(self, display_size):
        self.set_camera()
        gr3.drawimage(0, display_size, 0, display_size, display_size, display_size, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)
