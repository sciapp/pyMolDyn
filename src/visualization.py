import sys
import math
import numpy as np
from OpenGL.GLUT import *
import gr3
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
discretization_cache = DiscretizationCache('cache.hdf5')
discretization = discretization_cache.get_discretization(volume, 192)
    
max_domain_index = 0
domain_vertices_list = []
domain_normals_list = []

while True:
    try:
        domain_vertices, domain_normals = np.load("domain_triangles_hexagonal_192_22_domain%d.npy" % max_domain_index)
        domain_vertices_list.append(domain_vertices)
        domain_normals_list.append(domain_normals)
        max_domain_index += 1
    except IOError:
        break
max_cavity_index = 0
cavity_vertices_list = []
cavity_normals_list = []
while True:
    try:
        cavity_vertices, cavity_normals = np.load("cavity_triangles_hexagonal_192_22_cavity%d.npy" % max_cavity_index)
        cavity_vertices_list.append(cavity_vertices)
        cavity_normals_list.append(cavity_normals)
        print max_cavity_index, cavity_vertices.shape
        max_cavity_index += 1
    except IOError:
        break

        
def init():
    domain_meshes = []
    for domain_index in range(max_domain_index):
        domain_vertices = domain_vertices_list[domain_index]
        domain_normals = domain_normals_list[domain_index]
        num_domain_vertices = len(domain_vertices)*3
        mesh = gr3.createmesh(num_domain_vertices, domain_vertices, domain_normals, [(1,1,1)]*num_domain_vertices)
        domain_meshes.append(mesh)
        gr3.drawmesh(mesh, 1, (0,0,0), (0,0,1), (0,1,0), (0,1,0.5), (1,1,1))
        
    cavity_meshes = []
    for cavity_index in range(max_cavity_index):
        cavity_vertices = cavity_vertices_list[cavity_index]
        cavity_normals = cavity_normals_list[cavity_index]
        num_cavity_vertices = len(cavity_vertices)*3
        mesh = gr3.createmesh(num_cavity_vertices, cavity_vertices, cavity_normals, [(1,1,1)]*num_cavity_vertices)
        cavity_meshes.append(mesh)
        gr3.drawmesh(mesh, 1, (0,0,0), (0,0,1), (0,1,0), (0.2,0.4,1), (1,1,1))

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
    

rot = 0
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

def keyboard(key, x, y):
    if ord(key) == 27:
        sys.exit()

glutInit()
glutInitWindowSize(1200,1200)
glutCreateWindow(repr(volume))
init()
glutDisplayFunc(display)
glutIdleFunc(glutPostRedisplay)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special)
glutMainLoop()
