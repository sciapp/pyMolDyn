# -*- coding: utf-8 -*-
'''
To support various materials, different Bravais lattice systems need to be used
in pyMolDyn2, so that the shapes and periodic boundary conditions of different
crystalline structures are taken into account. These lattice systems are used as simulation volume and this module provides a
class for each of the 7 lattice systems. All of these are centered at 
(0,0,0).

As monoclinic, orthorombic, tetragonal, rhombohedral and cubic systems are
special cases of a triclinic system, the corresponding classes inherit from 
TriclinicVolume.

For more information about the Bravais lattice systems, see:
http://en.wikipedia.org/wiki/Bravais_lattice

Author: Florian Rhiem <f.rhiem@fz-juelich.de>
'''

from math import ceil, sin, cos, pi
cot = lambda alpha: cos(alpha) / sin(alpha)
import itertools
import numpy as np
import numpy.linalg as la
from math import acos

class HexagonalVolume(object):
    '''
    A hexagonal volume centered in the origin with a side length of ``a`` (for
    the 6 individual outer sides) and a height of ``c``.
    '''
    def __init__(self, a, c):
        self.a = float(a)
        self.c = float(c)
        f = 2*self.a*sin(pi/3)
        
        #: The lattice system translation vectors (`right`, `right-up`, `forward`)
        self.translation_vectors = [(cos(pi*i/3)*f, sin(pi*i/3)*f, 0) for i in range(2)] + [(0, 0, self.c)]
      
        #: The side lengths of an axis-aligned bounding box
        self.side_lengths = [2*self.a*sin(pi/3), 2*self.a, self.c]
        
        #: The cell volume, calculated as 6 times the area of an equilateral 
        #: triangle with side length a (3**0.5/4*a*a) times the height c.
        self.volume = 6*(3**0.5/4*self.a*self.a)*self.c
        
        #: A list of edges as point pairs
        self.edges = []
        for i in range(6):
            # edge on the lower hexagon
            p1 = (sin(pi/3*i)*self.a, cos(pi/3*i)*self.a, -0.5*self.c)
            p2 = (sin(pi/3*(i+1))*self.a, cos(pi/3*(i+1))*self.a, -0.5*self.c)
            self.edges.append((p1,p2))
            # edge on the upper hexagon
            p3 = (sin(pi/3*i)*self.a, cos(pi/3*i)*self.a, 0.5*self.c)
            p4 = (sin(pi/3*(i+1))*self.a, cos(pi/3*(i+1))*self.a, 0.5*self.c)
            self.edges.append((p3,p4))
            # edge connecting the two hexagons
            p5 = (sin(pi/3*i)*self.a, cos(pi/3*i)*self.a, -0.5*self.c)
            p6 = (sin(pi/3*i)*self.a, cos(pi/3*i)*self.a, 0.5*self.c)
            self.edges.append((p5,p6))

    def is_inside(self, point):
        '''
        True if ``point`` is inside of the volume, False otherwise.
        '''
        x,y,z = point
        ax = abs(x)
        ay = abs(y)
        az = abs(z)
        if az > self.c/2:
            return False
        if ax > sin(pi/3)*self.a:
            return False
        if ay > self.a:
            return False
        if ay > self.a/2 and ay > self.a - ax*cot(pi/3):
            return False
        return True
        
    def get_equivalent_point(self, point):
        '''
        For a given point, this method returns an equivalent point inside the volume.
        '''
        equivalent_point = np.array(point)
        translation_vectors = np.array(self.translation_vectors)
        translation_vectors = np.append(translation_vectors, [translation_vectors[1]-translation_vectors[0]])
        translation_vectors.shape = (4, 3)
        translation_vector_lengths = np.array([la.norm(v) for v in translation_vectors])
        for i, translation_vector_length in enumerate(translation_vector_lengths):
            translation_vectors[i] /= translation_vector_length
        projection_matrix = np.matrix(translation_vectors)
        
        may_be_outside = True
        while may_be_outside:
            projected_point = (projection_matrix * np.matrix(equivalent_point).T)
            scaled_projected_point = np.array(projected_point.flat) / translation_vector_lengths
            max_index = np.argmax(np.abs(scaled_projected_point))
            if abs(scaled_projected_point[max_index]) > 0.5:
                may_be_outside = True
                equivalent_point -= ceil(scaled_projected_point[max_index]-0.5)*translation_vector_lengths[max_index]*translation_vectors[max_index]
            else:
                may_be_outside = False
        return tuple(equivalent_point)
        
    def __repr__(self):
        return "HEXAGONAL a=%f c=%f" % (self.a, self.c)

class TriclinicVolume(object):
    '''
    A triclinic volume centered at the origin with the angles ``alpha``, 
    ``beta``, ``gamma`` and the side lengths ``a``, ``b`` and ``c``. It has the 
    shape of a parallelepiped.
    '''
    def __init__(self, *args):
        if len(args) == 6:
            a           = args[0]
            b           = args[1]
            c           = args[2]
            alpha       = args[3]
            beta        = args[4]
            gamma       = args[5]
            self.a      = a
            self.b      = b
            self.c      = c
            self.alpha  = alpha
            self.beta   = beta
            self.gamma  = gamma
            self.V = (1-cos(alpha)**2-cos(beta)**2-cos(gamma)**2+2*cos(alpha)*cos(beta)*cos(gamma))**0.5
            #: The cartesian-to-fractional transformation matrix
            self.M = np.matrix([[1/a, 1/a * (-cos(gamma)/sin(gamma)), 1/a * (cos(alpha)*cos(gamma)-cos(beta))/(self.V*sin(gamma))],
                                [  0, 1/b *             1/sin(gamma), 1/b * (cos(beta)*cos(gamma)-cos(alpha))/(self.V*sin(gamma))],
                                [  0,                              0, 1/c * sin(gamma)/self.V]])
            Minv = la.inv(self.M)
            #: The fracional-to-cartesian transformation matrix
            self.Minv = Minv
        else:
            v1 = np.array([float(f) for f in args[0:3]])
            v2 = np.array([float(f) for f in args[3:6]])
            v3 = np.array([float(f) for f in args[6:]])
            self.a = la.norm(v1)
            self.b = la.norm(v2)
            self.c = la.norm(v3)

            alpha = acos((v1.dot(v3))/(self.a * self.c))
            beta  = acos((v2.dot(v3))/(self.b * self.c))
            gamma = acos((v1.dot(v2))/(self.a * self.b))
            self.alpha  = alpha
            self.beta   = beta
            self.gamma  = gamma

            self.V      = (1-cos(alpha)**2-cos(beta)**2-cos(gamma)**2+2*cos(alpha)*cos(beta)*cos(gamma))**0.5
            self.Minv   = np.matrix(np.array([v1,v2,v3]).T)
            self.M      = np.matrix(la.inv(self.Minv))

        #: The lattice system translation vectors (`right`, `up`, `forward`)
        self.translation_vectors = [tuple(self.Minv.T[i].tolist()[0]) for i in range(3)]
        min_point = [float('inf')]*3
        max_point = [float('-inf')]*3
        for i, j, k in itertools.product((-0.5,0,0.5),repeat=3):
            point = self.Minv*np.matrix((i,j,k)).T
            point = point.T.tolist()[0]
            for l in range(3):
                min_point[l] = min(min_point[l], point[l])
                max_point[l] = max(max_point[l], point[l])
                
        #: The side lengths of an axis-aligned bounding box
        self.side_lengths = [d-c for c,d in zip(min_point, max_point)]
        
        #: The cell volume
        self.volume = self.V*self.a*self.b*self.c
        
        edges = [((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5)), ((-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5)), ((-0.5, -0.5, -0.5), (0.5, -0.5, -0.5)), ((-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5)), ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5)), ((-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5)), ((-0.5, 0.5, -0.5), (0.5, 0.5, -0.5)), ((-0.5, 0.5, 0.5), (0.5, 0.5, 0.5)), ((0.5, -0.5, -0.5), (0.5, -0.5, 0.5)), ((0.5, -0.5, -0.5), (0.5, 0.5, -0.5)), ((0.5, -0.5, 0.5), (0.5, 0.5, 0.5)), ((0.5, 0.5, -0.5), (0.5, 0.5, 0.5))]
        new_edges = []
        for edge in edges:
            point1, point2 = edge
            point1 = self.Minv*np.matrix(point1).T
            point1 = point1.T.tolist()[0]
            point2 = self.Minv*np.matrix(point2).T
            point2 = point2.T.tolist()[0]
            new_edges.append((point1, point2))
        #: A list of edges as point pairs
        self.edges = new_edges
        
    def is_inside(self, point):
        '''
        Returns True if point is inside of the volume, False otherwise.
        '''
        fractional_point = self.M*np.matrix(point).T
        return all((-0.5 < float(c) < 0.5 for c in fractional_point))
                
    def get_equivalent_point(self, point):
        '''
        For a given point, this method returns an equivalent point inside the volume.
        '''
        fractional_point = self.M*np.matrix(point).T
        fractional_point = fractional_point.T.tolist()[0]
        for i in range(3):
            fractional_point[i] -= ceil(fractional_point[i]-0.5)
        new_point = self.Minv*np.matrix(fractional_point).T
        new_point = tuple(new_point.T.tolist()[0])
        return new_point
        
    def __repr__(self):
        return "TRICLINIC a=%f b=%f c=%f alpha=%f beta=%f gamma=%f" % (self.a, self.b, self.c, self.alpha, self.beta, self.gamma)

class MonoclinicVolume(TriclinicVolume):
    '''
    A monoclinic volume, a special case of a triclinic volume with and ``alpha=gamma=pi/2``
    '''

    def __init__(self, *args):
        if len(args) == 4:
            a     = args[0]
            b     = args[1]
            c     = args[2]
            beta  = args[3]
            alpha = pi/2
            gamma = pi/2
            TriclinicVolume.__init__(self, a, b, c, alpha, beta, gamma)
        else:
            v1 = np.array([float(f) for f in args[0:3]])
            v2 = np.array([float(f) for f in args[3:6]])
            v3 = np.array([float(f) for f in args[6:]])
            TriclinicVolume.__init__(self, v1, v2, v3)

    def __repr__(self):
        return "MONOCLINIC a=%f b=%f c=%f beta=%f" % (self.a, self.b, self.c, self.beta)
        
class OrthorhombicVolume(TriclinicVolume):
    '''
    An orthorhombic volume, a special case of a triclinic volume with ``alpha=beta=gamma=pi/2``
    '''
    def __init__(self, *args):
        if len(args) == 3:
            a     = args[0]
            b     = args[1]
            c     = args[2]
            alpha = pi/2
            beta = pi/2
            gamma = pi/2
            TriclinicVolume.__init__(self, a, b, c, alpha, beta, gamma)
        else: # cell vectors
            v1 = np.array([float(f) for f in args[0:3]])
            v2 = np.array([float(f) for f in args[3:6]])
            v3 = np.array([float(f) for f in args[6:]])
            TriclinicVolume.__init__(self, v1, v2, v3)

    def __repr__(self):
        return "ORTHORHOMBIC a=%f b=%f c=%f" % (self.a, self.b, self.c)
        
class TetragonalVolume(TriclinicVolume):
    '''
    A tetragonal volume, a special case of a triclinic volume with ``a=b`` and ``alpha=beta=gamma=pi/2``
    '''
    def __init__(self, *args):
        if len(args) == 2:
            a = args[0]
            c = args[1]
            b = a
            alpha = pi/2
            beta = pi/2
            gamma = pi/2
            TriclinicVolume.__init__(self, a, b, c, alpha, beta, gamma)
        else: # cell vectors
            v1 = np.array([float(f) for f in args[0:3]])
            v2 = np.array([float(f) for f in args[3:6]])
            v3 = np.array([float(f) for f in args[6:]])
            TriclinicVolume.__init__(self, v1, v2, v3)

    def __repr__(self):
        return "TETRAGONAL a=%f c=%f" % (self.a, self.c)

class RhombohedralVolume(TriclinicVolume):
    '''
    A rhombohedral volume, a special case of a triclinic volume with ``a=b=c`` and ``alpha=beta=gamma``.
    '''
    def __init__(self, *args):
        if len(args) == 2:
            a     = args[0]
            alpha = args[1]
            b     = a
            c     = a
            beta  = alpha
            gamma = alpha
            TriclinicVolume.__init__(self, a, b, c, alpha, beta, gamma)
        else: # cell vectors
            v1 = np.array([float(f) for f in args[0:3]])
            v2 = np.array([float(f) for f in args[3:6]])
            v3 = np.array([float(f) for f in args[6:]])
            TriclinicVolume.__init__(self, v1, v2, v3)

    def __repr__(self):
        return "RHOMBOHEDRAL a=%f alpha=%f" % (self.a, self.alpha)
        
class CubicVolume(TriclinicVolume):
    '''
    A cubic volume, a special case of a triclinic volume with ``a=b=c`` and ``alpha=beta=gamma=pi/2``
    '''
    def __init__(self, *args):
        if len(args) == 1:
            a = args[0]
            b = a
            c = a
            alpha = pi/2
            beta = pi/2
            gamma = pi/2
            TriclinicVolume.__init__(self, a, b, c, alpha, beta, gamma)
        else: # cell vectors
            v1 = np.array([float(f) for f in args[0:3]])
            v2 = np.array([float(f) for f in args[3:6]])
            v3 = np.array([float(f) for f in args[6:]])
            TriclinicVolume.__init__(self, v1, v2, v3)
        
    def __repr__(self):
        return "CUBIC a=%f" % self.a

volumes = {
    'HEX' : (HexagonalVolume, 'ff'),
    'MON' : (MonoclinicVolume, 'ffff'),
    'TRI' : (TriclinicVolume, 'ffffff'),
    'ORT' : (OrthorhombicVolume, 'fff'),
    'TET' : (TetragonalVolume, 'ff'),
    'RHO' : (RhombohedralVolume,'ff'),
    'CUB' : (CubicVolume, 'f')
}

convert_functions = {
    'f' : float,
    'i' : int,
    's' : str
}

def get_volume_from_file(filename):
    with open(filename,'r') as f:
        f.readline()
        s = f.readline().split(' ')
        t = s[0].upper() # volume type
        cl = volumes[t][0] # volume class
        if len(s) == 10: # cell vectors given
            param = [float(f) for f in s[1:]]
        else:
            param_list = s[1:]
            param = [convert_functions[p](param_list[i]) for i,p in enumerate(volumes[t][1])] # parsing parameter
        return cl(*param)

if __name__ == '__main__':
    fn = '../xyz/structure_c.xyz'
    print get_volume_from_file(fn)
    fn = '../xyz/hexagonal.xyz'
    print get_volume_from_file(fn)
