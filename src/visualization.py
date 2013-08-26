import sys
import math
import itertools
import numpy as np

domain_triangles = np.load("domain_triangles_hexagonal_192_19.npy")
cavity_triangles = np.load("cavity_triangles_hexagonal_192_19.npy")
import pybel

for molecule in pybel.readfile("xyz", "xyz/hexagonal.xyz"):
    atoms = molecule.atoms
    num_atoms = len(atoms)
    atom_positions = [atom.coords for atom in atoms]
    break


import calculation
#volume = calculation.TriclinicVolume(30.639, 30.639, 22.612, math.pi/2, math.pi/2, math.pi/3)
volume = calculation.HexagonalVolume(17.68943, 22.61158)
for atom_index in range(num_atoms):
    atom_positions[atom_index] = volume.get_equivalent_point(atom_positions[atom_index])

if isinstance(volume, calculation.TriclinicVolume):
    edges = [((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5)), ((-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5)), ((-0.5, -0.5, -0.5), (0.5, -0.5, -0.5)), ((-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5)), ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5)), ((-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5)), ((-0.5, 0.5, -0.5), (0.5, 0.5, -0.5)), ((-0.5, 0.5, 0.5), (0.5, 0.5, 0.5)), ((0.5, -0.5, -0.5), (0.5, -0.5, 0.5)), ((0.5, -0.5, -0.5), (0.5, 0.5, -0.5)), ((0.5, -0.5, 0.5), (0.5, 0.5, 0.5)), ((0.5, 0.5, -0.5), (0.5, 0.5, 0.5))]
    new_edges = []
    for edge in edges:
        point1, point2 = edge
        point1 = volume.Minv*np.matrix(point1).T
        point1 = point1.T.tolist()[0]
        point2 = volume.Minv*np.matrix(point2).T
        point2 = point2.T.tolist()[0]
        new_edges.append((point1, point2))
    edges = new_edges
else:
    edges = []
    for i in range(6):
        p1 = (math.sin(math.pi/3*i)*volume.a, math.cos(math.pi/3*i)*volume.a, -0.5*volume.c)
        p2 = (math.sin(math.pi/3*(i+1))*volume.a, math.cos(math.pi/3*(i+1))*volume.a, -0.5*volume.c)
        edges.append((p1,p2))
        p3 = (math.sin(math.pi/3*i)*volume.a, math.cos(math.pi/3*i)*volume.a, 0.5*volume.c)
        p4 = (math.sin(math.pi/3*(i+1))*volume.a, math.cos(math.pi/3*(i+1))*volume.a, 0.5*volume.c)
        edges.append((p3,p4))
        p5 = (math.sin(math.pi/3*i)*volume.a, math.cos(math.pi/3*i)*volume.a, -0.5*volume.c)
        p6 = (math.sin(math.pi/3*i)*volume.a, math.cos(math.pi/3*i)*volume.a, 0.5*volume.c)
        edges.append((p5,p6))

#box_size = 27.079855

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


def get_normals(triangle_list):
    normals = {}    # Die verschiedenen Punkte werden als Key verwendet, sodass mit den Punkten direkt die zugehoerige Normale abgefragt werden kann.
    
    for i in triangle_list:
        v1 = (i[1][0] - i[0][0], i[1][1] - i[0][1], i[1][2] - i[0][2])
        v2 = (i[2][0] - i[0][0], i[2][1] - i[0][1], i[2][2] - i[0][2]) 
        n = (v1[1]*v2[2] - v1[2]*v2[1], v1[2]*v2[0] - v1[0]*v2[2], v1[0]*v2[1] - v1[1]*v2[0])
        n_laenge = math.sqrt(n[0]**2 + n[1]**2 + n[2]**2)
        if n_laenge != 0 :
            n = (n[0]/n_laenge, n[1]/n_laenge, n[2]/n_laenge)
        for j in i:
            j = tuple(j)
            if not normals.has_key(j):
                normals[j] = n
            else:
                normals[j] = (normals[j][0] + n[0], normals[j][1] + n[1], normals[j][2] + n[2])
                
    for i in normals.iterkeys():
        n = normals[i]
        n_laenge = math.sqrt(n[0]**2 + n[1]**2 + n[2]**2)
        if n_laenge != 0 :
            n = (n[0]/n_laenge, n[1]/n_laenge, n[2]/n_laenge)
        normals[i] = n
        
    return normals

def init():
    global display_list
    global display_list2
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45,1,0.1,400)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslate(0,0,-100)
    glEnable(GL_NORMALIZE)
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glClearColor(0.2,0.2,0.2,1)
    display_list = glGenLists(1)
    glNewList(display_list, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for triangles in cavity_triangles:
        normals = get_normals(triangles)
        for triangle in triangles:
            #if all([volume.is_inside(vertex) for vertex in triangle]):
            for vertex in triangle:
                glNormal(*normals[tuple(vertex)])
                glVertex(*vertex)
                
    glEnd()
    glEndList()
    display_list2 = glGenLists(1)
    glNewList(display_list2, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for triangles in domain_triangles:
        normals = get_normals(triangles)
        for triangle in triangles:
            for vertex in triangle:
                glNormal(*normals[tuple(vertex)])
                glVertex(*vertex)
                
    glEnd()
    glEndList()
    

def display():
    global display_list
    global display_list2
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor(1,1,1)
    if show:
        glCallList(display_list)
    else:
        glCallList(display_list2)
    glDisable(GL_LIGHTING)
    glBegin(GL_POINTS)
    for atom_position in atom_positions:
        glVertex3f(*atom_position)
    glEnd()
    glBegin(GL_LINES)
    for edge in edges:
        point1, point2 = edge
        glVertex3f(*point1)
        glVertex3f(*point2)
    glEnd()
    glEnable(GL_LIGHTING)
    glutSwapBuffers()

show = True
def keyboard(key, x, y):
    if ord(key) == 27:
        sys.exit()
    if key == 'd':
        global show
        show = not show

def special(key, x, y):
    if key == GLUT_KEY_LEFT:
        glRotate(5,0,1,0)
    elif key == GLUT_KEY_RIGHT:
        glRotate(-5,0,1,0)

glutInit()
glutInitWindowSize(1000,1000)
glutCreateWindow("Test")
init()
glutDisplayFunc(display)
glutIdleFunc(glutPostRedisplay)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special)
glutMainLoop()
