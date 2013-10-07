import sys
import math
import numpy as np
import gr3
from OpenGL.GLUT import *
import pybel
import volumes

volume = volumes.HexagonalVolume(17.68943, 22.61158)

molecule = pybel.readfile("xyz", "xyz/hexagonal.xyz").next()
atoms = molecule.atoms
num_atoms = len(atoms)
atom_positions = [atom.coords for atom in atoms]
for atom_index in range(num_atoms):
    atom_positions[atom_index] = volume.get_equivalent_point(atom_positions[atom_index])


from calculation import *

cr = CalculationResults("test3.hdf5")
max_domain_index = cr.number_of_domains
domain_vertices_list = [t[0] for t in cr.domain_triangles]
domain_normals_list = [t[1] for t in cr.domain_triangles]
max_cavity_index = cr.number_of_multicavities
cavity_vertices_list = [t[0] for t in cr.multicavity_triangles]
cavity_normals_list = [t[1] for t in cr.multicavity_triangles]
max_center_cavity_index = cr.number_of_center_multicavities
center_cavity_vertices_list = [t[0] for t in cr.center_multicavity_triangles]
center_cavity_normals_list = [t[1] for t in cr.center_multicavity_triangles]

rot = 0
domain_meshes = []
cavity_meshes = []
def init():
    global domain_meshes
    global cavity_meshes
    global center_cavity_meshes
    global rot
    
    domain_meshes = []
    for domain_index in range(max_domain_index):
        domain_vertices = domain_vertices_list[domain_index]
        domain_normals = domain_normals_list[domain_index]
        num_domain_vertices = len(domain_vertices)*3
        mesh = gr3.createmesh(num_domain_vertices, domain_vertices, domain_normals, [(1,1,1)]*num_domain_vertices)
        domain_meshes.append(mesh)
        
    cavity_meshes = []
    for cavity_index in range(max_cavity_index):
        cavity_vertices = cavity_vertices_list[cavity_index]
        cavity_normals = cavity_normals_list[cavity_index]
        num_cavity_vertices = len(cavity_vertices)*3
        mesh = gr3.createmesh(num_cavity_vertices, cavity_vertices, cavity_normals, [(1,1,1)]*num_cavity_vertices)
        cavity_meshes.append(mesh)
        
    center_cavity_meshes = []
    for cavity_index in range(max_center_cavity_index):
        center_cavity_vertices = center_cavity_vertices_list[cavity_index]
        center_cavity_normals = center_cavity_normals_list[cavity_index]
        num_center_cavity_vertices = len(center_cavity_vertices)*3
        mesh = gr3.createmesh(num_center_cavity_vertices, center_cavity_vertices, center_cavity_normals, [(1,1,1)]*num_center_cavity_vertices)
        center_cavity_meshes.append(mesh)
        
    create_scene()
    
    d = max(volume.side_lengths)*2
    gr3.cameralookat(d*math.sin(rot),0,d*math.cos(rot), 0,0,0, 0,1,0)
    gr3.export("test.html",800,800)

def create_scene(show_cavities=True, center_based_cavities=False):
    global domain_meshes
    global cavity_meshes
    global center_cavity_meshes
    
    gr3.clear()
    if not show_cavities:
        for domain_index in range(max_domain_index):
            gr3.drawmesh(domain_meshes[domain_index], 1, (0,0,0), (0,0,1), (0,1,0), (0,1,0.5), (1,1,1))
    else:
        if not center_based_cavities:
            for cavity_index in range(max_cavity_index):
                gr3.drawmesh(cavity_meshes[cavity_index], 1, (0,0,0), (0,0,1), (0,1,0), (0.2,0.4,1), (1,1,1))
        else:
            for cavity_index in range(max_center_cavity_index):
                gr3.drawmesh(center_cavity_meshes[cavity_index], 1, (0,0,0), (0,0,1), (0,1,0), (0.9,0.4,0.2), (1,1,1))

    edges = volume.edges
    num_edges = len(edges)
    edge_positions = [edge[0] for edge in edges]
    edge_directions = [[edge[1][i]-edge[0][i] for i in range(3)] for edge in edges]
    edge_lengths = [sum([c*c for c in edge])**0.5 for edge in edge_directions]
    edge_radius = min(edge_lengths)/200
    gr3.drawcylindermesh(num_edges, edge_positions, edge_directions, [(1,1,1)]*num_edges, [edge_radius]*num_edges, edge_lengths)
    corners = list(set([tuple(edge[0]) for edge in edges] + [tuple(edge[1]) for edge in edges]))
    num_corners = len(corners)
    gr3.drawspheremesh(num_corners, corners, [(1,1,1)]*num_edges, [edge_radius]*num_edges)
    gr3.drawspheremesh(len(atom_positions), atom_positions, [(1,1,1)]*len(atom_positions), [edge_radius*4]*len(atom_positions))
    

def display():
    global rot
    d = max(volume.side_lengths)*2
    gr3.cameralookat(d*math.sin(rot),0,d*math.cos(rot), 0,0,0, 0,1,0)
    gr3.drawimage(0, 1200, 0, 1200, 1200, 1200, gr3.GR3_Drawable.GR3_DRAWABLE_OPENGL)
    glutSwapBuffers()

def special(key, x, y):
    global rot
    if key == GLUT_KEY_LEFT:
        rot += math.pi/180*10
    if key == GLUT_KEY_RIGHT:
        rot -= math.pi/180*10
    glutPostRedisplay()

def keyboard(key, x, y):
    if ord(key) == 27:
        sys.exit()
    if key == 'd':
        create_scene(False)
    if key == 'c':
        create_scene(True)
    if key == 'f':
        create_scene(True, True)
    glutPostRedisplay()

glutInit()
glutInitWindowSize(1200,1200)
glutCreateWindow(repr(volume))
init()
glutDisplayFunc(display)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special)
glutMainLoop()
