'''
This module allows the analysis of surface-based molecular cavities in various 
volumes. To do so, a volume and a list of atom positions and their cutoff radii
is required. The following example shows reading the first frame of a ``xyz`` 
file (using the ``pybel`` module), defining a hexagonal volume and moving all 
atoms into this volume.

.. code-block:: python
   :emphasize-lines: 7,10
   
   import pybel
   
   atoms = pybel.readfile("xyz", "hexagonal.xyz").next().atoms
   num_atoms = len(atoms)
   atom_positions = [atom.coords for atom in atoms]

   volume = volumes.HexagonalVolume(17.68943, 22.61158)
   for atom_index in range(num_atoms):
       atom_positions[atom_index] = volume.get_equivalent_point(atom_positions[atom_index])
   atoms = Atoms(atom_positions, [2.8]*num_atoms)
   
After this, a discretization of the volume is needed. This module supports
caching of these with the ``DiscretizationCache`` class.

.. code-block:: python
   
   discretization_cache = DiscretizationCache('cache.hdf5')
   discretization = discretization_cache.get_discretization(volume, 192)
   
Using this ``discretization`` and the ``Atoms`` object created above, the atom
positions and their cutoff radii are also discretized.

.. code-block:: python
   
   atom_discretization = AtomDiscretization(atoms, discretization)
   
With these objections created, all preparations are complete and the domain and
cavity calculation can be done:

.. code-block:: python
   
   domain_calculation = DomainCalculation(discretization, atom_discretization)
   cavity_calculation = CavityCalculation(domain_calculation)

Author: Florian Rhiem <f.rhiem@fz-juelich.de>
'''
from math import ceil, floor, sin, cos, pi
import itertools
import sys
import numpy as np
import numpy.linalg as la
import h5py
from gr3 import triangulate

dimension = 3
dimensions = range(dimension)

import volumes

class DiscretizationCache(object):
    '''
    Instances of this class use a hdf5-formatted file as a cache for volume
    discretizations.
    '''
    
    def __init__(self, filename):
        self.file = h5py.File(filename, 'a')
        if '/discretizations' not in self.file:
            self.file.create_group('/discretizations')
            
    def get_discretization(self, volume, d_max):
        '''
        Return a cached discretization are generate a new one, store it in the
        cache file and then return it.
        '''
        discretization_repr = repr(volume) + " d_max=%d" %d_max
        print discretization_repr
        if discretization_repr in self.file['/discretizations']:
            stored_discretization = self.file['/discretizations/'+discretization_repr]
            grid = np.array(stored_discretization)
            discretization = Discretization(volume, d_max, grid)
        else:
            discretization = Discretization(volume, d_max)
            grid = discretization.grid
            self.file['/discretizations/'+discretization_repr] = grid
            self.file.flush()
        return discretization
        
    def get_discretization_from_string(self, string):
        string_parts = string.split()
        volume_type = string_parts[0]
        volume_type = volume_type.title()+"Volume"
        volume_class = getattr(volumes, volume_type)
        argument_info = string_parts[1:-1]
        arguments = {}
        for argument in argument_info:
            name, value = argument.split('=')
            value = float(value)
            arguments[name] = value
        volume = volume_class(**arguments)
        d_max_info = string_parts[-1]
        if not d_max_info.startswith('d_max='):
            raise Exception('Any volume discretization information string must end with "d_max=<d_max>".')
        d_max = float(d_max_info[len('d_max='):])
        return self.get_discretization(volume, d_max)
        

class Discretization(object):
    '''
    Instances of this class represent a discrete version of a volume.
    
    The discretization is done in the following steps:
     1. For a given maximum resolution of the resulting discrete representation
        (d_max), the length of the discretization cells (s_step) is calculated.
     2. The actual resolutions of the resulting discrete representation (d) are
        calculated and the side lengths of corresponding bounding cuboid
        (s_tilde) are calculated. (After this point, the transformation 
        functions discrete_to_continuous(p) and continuous_to_discrete(p) can be
        used.)
     3. The volume's translation vectors are discretized (translation_vectors)
        and combinations of these are calculated (combined_translation_vectors).
     4. An integer grid is created and for each discrete point, it stores either
        0 if the point is inside the volume or 1 if it is outside the volume.
     5. In the grid, for each point which is inside the volume (value = 0) all 
        points created by addition of a combined translation vector are defined
        to be outside of the volume (value = 1), except for the point itself.
        After this, there is no equivalent pair of points, which both are inside
        the volume.
     6. At this point there might still be some points in the grid though, which
        have no equivalent point inside of the volume (value = 0). For each of 
        these points, all equivalent points are found and from these, the one 
        closest to the center (continuous coordinates (0,0,0)) is defined to be 
        inside the volume.
     7. For each point which is outside of the volume (value = 1). A negative 
        value is set to indicate which combined translation vector leads to the
        equivalent point inside the volume.
         
    '''
    def __init__(self, volume, d_max, grid=None):
        # step 1
        self.d_max = d_max
        self.volume = volume
        self.s = volume.side_lengths
        self.s_max = max(self.s)
        if self.d_max%2 == 1:
            self.d_max -= 1
        self.s_step = self.s_max/(self.d_max-4)
        print "s_step",self.s_step
        
        #step 2
        self.d = [int(floor(self.s[i]/self.s_step)+4) for i in dimensions]
        for i in dimensions:
            if self.d[i]%2 == 1:
                self.d[i] += 1
        print "d", self.d
        self.s_tilde = [(self.d[i]-1)*self.s_step for i in dimensions]
        
        # step 3
        self.translation_vectors = [[int(floor(c/self.s_step+0.5)) for c in v] for v in self.volume.translation_vectors]
        self.combined_translation_vectors = [[sum([v[0][j]*v[1] for v in zip(self.translation_vectors, i)]) for j in dimensions] for i in itertools.product((-1, 0, 1), repeat=dimension) if any(i)]
        
        if grid is not None:
            self.grid = grid
        else:
            #step 4
            self.grid = np.zeros(self.d, dtype=np.int8)
            for p in itertools.product(*map(range, self.d)):
                point = self.discrete_to_continuous(p)
                if self.volume.is_inside(point):
                    self.grid[p] = 0
                else:
                    self.grid[p] = 1
            
            # step 5
            for p in itertools.product(*map(range, self.d)):
                equivalent_points = [[p[i]+v[i] for i in dimensions] for v in self.combined_translation_vectors]
                valid_equivalent_points = [tuple(point) for point in equivalent_points if all([0 <= point[i] <= self.d[i]-1 for i in dimensions])]
                if self.grid[p] == 0:
                    equivalent_points_inside = [point for point in valid_equivalent_points if self.grid[point] == 0]
                    for point in equivalent_points_inside:
                        self.grid[point] = 1

            # step 6 & 7
            for p in itertools.product(*map(range, self.d)):
                equivalent_points = [([p[i]+v[i] for i in dimensions], vi) for vi, v in enumerate(self.combined_translation_vectors)]
                valid_equivalent_points = [(tuple(point), vi) for point, vi in equivalent_points if all([0 <= point[i] <= self.d[i]-1 for i in dimensions])]
                if self.grid[p] == 1:
                    equivalent_points_inside = [(point, vi) for point, vi in valid_equivalent_points if self.grid[point] == 0]
                    if not equivalent_points_inside:
                        nearest_to_center = p
                        nearest_to_center_index = -1 # -1 -> -(-1+1) == 0
                        min_d_center = sum([(p[i] - self.d[i]/2)*(p[i] - self.d[i]/2) for i in dimensions])
                        for p2,vi in valid_equivalent_points:
                            d_center = sum([(p2[i] - self.d[i]/2)*(p2[i] - self.d[i]/2) for i in dimensions])
                            if d_center < min_d_center:
                                min_d_center = d_center
                                nearest_to_center = p2
                                nearest_to_center_index = vi
                        self.grid[nearest_to_center] = 0
                        self.grid[p] = -(nearest_to_center_index+1)
                    else:
                        combined_translation_vector_index = equivalent_points_inside[0][1]
                        self.grid[p] = -(combined_translation_vector_index+1)
        print "translation vectors", self.translation_vectors

    def get_direct_neighbors(self, point):
        '''
        This method returns the direct neighbor points of a given point.
        '''
        neighbors_without_bound_checks = [[point[j]+i[j] for j in dimensions] for i in itertools.product((-1, 0, 1), repeat=dimension) if any(i)]
        direct_neighbors = [tuple(neighbor) for neighbor in neighbors_without_bound_checks if all([0 <= neighbor[j] <= self.d[j] - 1 for j in dimensions])]
        return direct_neighbors

    def get_neighbors_in_volume(self, point):
        '''
        This method returns the neighbor points of a given point, which are
        inside the volume.
        '''
        direct_neighbors = self.get_direct_neighbors(point)
        neighbors_in_volume = map(self.get_equivalent_point_in_volume, direct_neighbors)
        return neighbors_in_volume

    def get_equivalent_point_in_volume(self, point):
        '''
        For a point given in discrete coordinates, this method returns the point
        which is inside of the volume and is equivalent to the given point.
        '''
        if self.grid[point] == 0:
            return point
        else:
            combined_translation_vector_index = -self.grid[point]-1
            combined_translation_vector = self.combined_translation_vectors[combined_translation_vector_index]
            return tuple([point[i]+combined_translation_vector[i] for i in dimensions])

    def continuous_to_discrete(self,point):
        '''
        Transforms a point from continuous to discrete coordinates.
        '''
        return tuple([int(floor((point[i]+self.s_tilde[i]/2)/self.s_step+0.5)) for i in dimensions])

    def discrete_to_continuous(self,point):
        '''
        Transforms a point from discrete to continuous coordinates.
        '''
        return tuple([point[k]*self.s_step-self.s_tilde[k]/2 for k in dimensions])
        
    def __repr__(self):
        discretization_repr = repr(self.volume) + " d_max=%d" % self.d_max

class Atoms:
    '''
    Instances of this class represent a list of atoms and their properties:
    - position
    - cavity cutoff radius
    
    To allow iteration in the order of their radii (from largest to smallest),
    the attributes self.sorted_radii and self.sorted_positions can be used.
    '''
    def __init__(self, atom_positions, atom_radii):
        self.positions = atom_positions
        self.radii = atom_radii
        self.sorted_radii = sorted(list(set(self.radii)), reverse=True)
        self.radii_as_indices = []
        self.sorted_positions = []
        for index, radius in enumerate(self.sorted_radii):
            for atom_index,atom_radius in enumerate(self.radii):
                if radius == atom_radius:
                    self.radii_as_indices.append(index)
                    self.sorted_positions.append(self.positions[atom_index])

class AtomDiscretization:
    '''
    Instances of this class represent a list of atoms in a discrete volume.
    '''
    def __init__(self, atoms, discretization):
        self.discretization = discretization
        self.atoms = atoms
        self.sorted_discrete_radii = []
        self.discrete_radii = []
        self.discrete_positions = []
        for radius_index, position in zip(self.atoms.radii_as_indices,self.atoms.sorted_positions):
            radius = self.atoms.sorted_radii[radius_index]
            discrete_position = self.discretization.continuous_to_discrete(position)
            self.discrete_positions.append(discrete_position)
        for radius in self.atoms.sorted_radii:
            discrete_radius = int(floor(radius/self.discretization.s_step+0.5))
            self.sorted_discrete_radii.append(discrete_radius)
        print "maximum radius:", self.sorted_discrete_radii[0]


class DomainCalculation:
    '''
    Cavity domain calulation is performed by the following steps:
     1. A grid is created with the resolution defined in the volume
        discretization and filled with zeros.
     2. For each atom, all points in the grid closer to this atom than the 
        discrete cavity cutoff radius are set to a point indicating the atom
        index (atom_index+1). This is done with a 'sphere grid', which can be 
        reused for atoms with the same discrete radius.
     3. At this point, every point in the grid which is inside of the volume and
        still has a value of zero is part of a cavity domain. To find these 
        domains, the method walk_domain is used and for each domain, centers and
        surface points (points with a neighbor outside of the cavity domain) are
        stored in lists. Points inside of a domain are marked with a negative
        value indicating which domain they are part of.
    '''
    def __init__(self, discretization, atom_discretization):
        # step 1
        self.discretization = discretization
        self.atom_discretization = atom_discretization
        self.grid = np.zeros(self.discretization.d,dtype=np.int64)

        # step 2
        last_radius_index = -1 # (for reuse of sphere grids)
        atom_information = itertools.izip(range(len(self.atom_discretization.discrete_positions)), self.atom_discretization.atoms.radii_as_indices, self.atom_discretization.discrete_positions)
        for atom_index, radius_index, real_discrete_position in atom_information:
            discrete_radius = self.atom_discretization.sorted_discrete_radii[radius_index]
            if radius_index != last_radius_index:
                last_radius_index = radius_index
                sphere_grid = np.zeros([discrete_radius*2+1 for i in dimensions], dtype=np.bool)
                for point in itertools.product(range(discrete_radius*2+1), repeat=dimension):
                    squared_distance_to_grid_center = sum([(point[i]-discrete_radius)*(point[i]-discrete_radius) for i in dimensions])
                    sphere_grid[point] = (squared_distance_to_grid_center <= discrete_radius*discrete_radius)
            for v in self.discretization.combined_translation_vectors+[(0, 0, 0)]:
                discrete_position = [real_discrete_position[i]+v[i] for i in dimensions]
                for point in itertools.product(range(discrete_radius*2+1), repeat=dimension):
                    if sphere_grid[point]:
                        p = [point[i]-discrete_radius+discrete_position[i] for i in dimensions]
                        if all([0 <= p[i] <= self.discretization.d[i]-1 for i in dimensions]):
                            grid_value = self.discretization.grid[tuple(p)]
                            if grid_value == 0:
                                self.grid[tuple(p)] = atom_index+1
        # step 3
        domain_index = 0
        self.centers = []
        self.surface_point_list = []
        for p in itertools.product(*map(range,self.discretization.d)):
            if self.grid[p] == 0 and self.discretization.grid[p] == 0:
                center, surface_points = self.walk_domain(p, domain_index)
                self.centers.append(center)
                self.surface_point_list.append(surface_points)
                domain_index += 1
        print "number of domains:", domain_index
        self.domain_volumes = []
        for domain_index in range(len(self.centers)):
            domain_volume = (self.grid == -(domain_index+1)).sum()*(self.discretization.s_step**3)
            self.domain_volumes.append(domain_volume)
        self.triangles()

    def walk_domain(self, p, domain_index):
        '''
        This function 'walks' through a cavity domain with a given index,
        starting at the point p.
        All neighbors of a point (which is inside of the domain) which are also
        inside of a domain are marked as part of this domain and used for
        further 'walking'.
        '''
        points_to_walk = [p]
        max_squared_distance = 0
        surface_points = []
        while points_to_walk:
            p = points_to_walk.pop()
            if self.grid[p] == 0:
                min_squared_distance = sys.maxint
                for real_discrete_position in self.atom_discretization.discrete_positions:
                    for v in self.discretization.combined_translation_vectors+[(0,0,0)]:
                        discrete_position = [real_discrete_position[i]+v[i] for i in dimensions]
                        squared_distance = sum([(discrete_position[i]-p[i])*(discrete_position[i]-p[i]) for i in dimensions])
                        min_squared_distance = min(squared_distance,min_squared_distance)
                if min_squared_distance > max_squared_distance:
                    max_squared_distance = min_squared_distance
                    center = p
                self.grid[p] = -domain_index-1
                if any([self.discretization.grid[n] < 0 or self.grid[n] > 0 for n in self.discretization.get_direct_neighbors(p)]):
                    surface_points.append(p)
                for neighbor in self.discretization.get_neighbors_in_volume(p):
                    points_to_walk.append(neighbor)
        return center, surface_points

    def triangles(self):
        if hasattr(self, "domain_triangles"):
            return self.domain_triangles
        number_of_domains = len(self.centers)
        print number_of_domains
        domain_triangles = []
        domain_surface_areas = []
        step = (self.discretization.s_step,)*3
        offset = self.discretization.discrete_to_continuous((0, 0, 0))
        for domain_index in range(number_of_domains):
            print "Calculating triangles for domain", domain_index
            grid_value = -(domain_index+1)
            grid = (self.grid == grid_value)
            views = []
            for x, y, z in itertools.product(*map(xrange, (3, 3, 3))):
                view = grid[x:grid.shape[0]-2+x, y:grid.shape[1]-2+y, z:grid.shape[2]-2+z]
                views.append(view)
            grid = np.zeros(grid.shape, np.uint16)
            grid[:,:,:] = 0
            grid[1:-1, 1:-1, 1:-1] = sum(views)+100
            domain_triangles.append(triangulate(grid, step, offset, 100))
            domain_surface_area = 0
            for domain_triangle in domain_triangles[-1][0]:
                any_outside = False
                for vertex in domain_triangle:
                    discrete_vertex = discretization.continuous_to_discrete(vertex)
                    if discretization.grid[discrete_vertex] != 0:
                        any_outside = True
                        break
                if not any_outside:
                    v1, v2, v3 = domain_triangle
                    a = v2-v1
                    b = v3-v1
                    triangle_surface_area = la.norm(np.cross(a,b))*0.5
                    domain_surface_area += triangle_surface_area
            domain_surface_areas.append(domain_surface_area)
        self.domain_triangles = domain_triangles
        self.domain_surface_areas = domain_surface_areas
        return domain_triangles

class CavityCalculation:
    '''
    Cavity domain calulation is performed by the following steps:
     1. The discrete volume grid is divided into subgrid cells with a side length 
        based on the maximum discrete cavity cutoff radius. For each subgrid, a
        tuple of three lists is stored (in self.sg).
     2. The first list for each subgrid cell is filled with the atoms inside the
        cell (their 'real' positions, which might be outside of the volume).
     3. The second and third lists are filled with surface points and their 
        domain index. (These might also be moved with the translation vectors
        and might thereby also be outside of the volume.)
     4. A new grid is created (grid3) and each point in this grid is set to zero
        if it is outside of the volume or part inside of the cavity cutoff
        radius of an atom, or a negative value if it is part of a cavity domain
        (see the domain calculation step 2 for this).
     5. For each point which is inside the cavity cutoff radius of an
        atom, the nearest atom and the nearest domain surface point are found by
        using the neighbor subgrid cells. If a domain surface point is nearer
        than the nearest atom, than the point belongs to the cavity which this
        surface point belonged to and is marked with a negative value.
     6. At this point, two cavities constructed from two cavity domains might
        actually be one multicavity. In this step, these are found and a list of
        multicavities is created.
        
    About the subgrid cells:
    If a point inside a subgrid cell was marked as 'near an atom' during the
    domain calculation, then the position of this atom must be either in the
    same cell or in one of the cell's neighbors. This is guaranteed, because the
    atom must be at most its on cavity cutoff radius away, and the subgrid cell
    size is the maximum cavity cutoff radius.
    
    
    To calculate center-based cavities, use a grid filled with zeros instead of
    resuing some values from the domain calculation grid and then iterate over
    the domain centers instead of the domain surface points.
    '''
    def __init__(self, domain_calculation, use_surface_points=True):
        self.domain_calculation = domain_calculation
        if use_surface_points:
            self.grid = self.domain_calculation.grid
            num_surface_points = sum(map(len, self.domain_calculation.surface_point_list))
            print "number of surface points:", num_surface_points
        
        # step 1
        max_radius = self.domain_calculation.atom_discretization.sorted_discrete_radii[0]
        self.sg_cube_size = max_radius
        self.sgd = tuple([2+int(ceil(1.0*d/self.sg_cube_size))+2 for d in self.domain_calculation.discretization.d])
        self.sg = []
        for x in range(self.sgd[0]):
            self.sg.append([])
            for y in range(self.sgd[1]):
                self.sg[x].append([])
                for z in range(self.sgd[2]):
                    self.sg[x][y].append([[], [], []])
        # step 2
        for atom_index, atom_position in enumerate(self.domain_calculation.atom_discretization.discrete_positions):
            for v in self.domain_calculation.discretization.combined_translation_vectors+[(0, 0, 0)]:
                real_atom_position = [atom_position[i]+v[i] for i in dimensions]
                sgp = self.to_subgrid(real_atom_position)
                self.sg[sgp[0]][sgp[1]][sgp[2]][0].append(real_atom_position)
        # step 3
        if use_surface_points:
            domain_seed_point_lists = self.domain_calculation.surface_point_list
        else:
            domain_seed_point_lists = [[center] for center in self.domain_calculation.centers]
        for domain_index, domain_seed_points in enumerate(domain_seed_point_lists):
            for domain_seed_point in domain_seed_points:
                for v in self.domain_calculation.discretization.combined_translation_vectors+[(0, 0, 0)]:
                    real_domain_seed_point = [domain_seed_point[i]+v[i] for i in dimensions]
                    sgp = self.to_subgrid(real_domain_seed_point)
                    self.sg[sgp[0]][sgp[1]][sgp[2]][1].append(real_domain_seed_point)
                    self.sg[sgp[0]][sgp[1]][sgp[2]][2].append(domain_index)
        # step 4
        self.grid3 = np.zeros(self.domain_calculation.discretization.d,dtype=np.int64)
        for p in itertools.product(*map(range, self.domain_calculation.discretization.d)):
            if use_surface_points:
                grid_value = self.grid[p]
                if grid_value == 0: # outside the volume
                    self.grid3[p] = 0
                    possibly_in_cavity = False
                elif grid_value < 0: # cavity domain (stored as: -index-1), therefore guaranteed to be in a cavity
                    self.grid3[p] = grid_value
                    possibly_in_cavity = True
                elif grid_value > 0: # in radius of atom (stored as: index+1), therefore possibly in a cavity
                    self.grid3[p] = 0
                    possibly_in_cavity = True
            else:
                possibly_in_cavity = (self.domain_calculation.discretization.grid[p] == 0)
            if possibly_in_cavity:
                # step 5
                min_squared_atom_distance = sys.maxint
                sgp = self.to_subgrid(p)
                for i in itertools.product((0, 1, -1), repeat=dimension):
                    sgci = [sgp[j]+i[j] for j in dimensions]
                    for atom_position in self.sg[sgci[0]][sgci[1]][sgci[2]][0]:
                        squared_atom_distance = sum([(atom_position[j]-p[j])*(atom_position[j]-p[j]) for j in dimensions])
                        min_squared_atom_distance = min(min_squared_atom_distance,squared_atom_distance)
                for i in itertools.product((0, 1, -1), repeat=dimension):
                    next = False
                    sgci = [sgp[j]+i[j] for j in dimensions]
                    for domain_index, domain_seed_point in zip(self.sg[sgci[0]][sgci[1]][sgci[2]][2], self.sg[sgci[0]][sgci[1]][sgci[2]][1]):
                        squared_domain_seed_point_distance = sum([(domain_seed_point[j]-p[j])*(domain_seed_point[j]-p[j]) for j in dimensions])
                        if squared_domain_seed_point_distance < min_squared_atom_distance:
                            self.grid3[p] = -domain_index-1
                            next = True
                            break
                    if next:
                        break


        num_domains = len(self.domain_calculation.centers)
        grid_volume = (self.domain_calculation.discretization.grid == 0).sum()
        self.cavity_volumes = []
        for domain_index in range(num_domains):
            self.cavity_volumes.append(1.0*(self.grid3 == -(domain_index+1)).sum()*(self.domain_calculation.discretization.s_step**3))

        # step 6
        intersection_table = np.zeros((num_domains, num_domains), dtype=np.int8)
        directions = []
        for dx, dy, dz in itertools.product((0, 1), repeat=3):
            if any((dx > 0, dy > 0, dz > 0)):
                directions.append((dx, dy, dz))
        for p in itertools.product(*[range(x-1) for x in self.domain_calculation.discretization.d]):
            domain1 = -self.grid3[p]-1
            if domain1 != -1:
                for direction in directions:
                    p2 = tuple([p[i]+direction[i] for i in dimensions])
                    domain2 = -self.grid3[p2]-1
                    if domain2 != -1:
                        intersection_table[domain1][domain2] = 1
                        intersection_table[domain2][domain1] = 1
        multicavities = []
        for domain in range(num_domains):
            neighbors = set([domain])
            for neighbor in range(num_domains):
                if intersection_table[domain][neighbor] == 1:
                    neighbors.add(neighbor)
            for multicavity in multicavities[:]:
                if any([neighbor in multicavity for neighbor in neighbors]):
                    neighbors = neighbors | multicavity
                    multicavities.remove(multicavity)
            multicavities.append(neighbors)
        self.multicavities = multicavities
        self.multicavity_volumes = []
        for multicavity in multicavities:
            self.multicavity_volumes.append(sum(self.cavity_volumes[cavity_index] for cavity_index in multicavity))
        print "multicavity volumes:", self.multicavity_volumes
        
        print "multicavities:", multicavities
        
        self.triangles()

    def to_subgrid(self, position):
        sgp = [c/self.sg_cube_size + 2 for c in position]
        for i in dimensions:
            if sgp[i] < 0:
                sgp[i] = 0
            if sgp[i] >= self.sgd[i]:
                sgp[i] = self.sgd[i]-1
        return tuple(sgp)

    def squared_distance(self, a, b):
        '''
        Calculates the squared distance between two points while taking the
        translation vectors into account.
        '''
        sqd = sys.maxint
        for v in self.domain_calculation.discretization.combined_translation_vectors+[(0, 0, 0)]:
            sqd = min(sqd, sum([(a[i]-b[i]+v[i])*(a[i]-b[i]+v[i]) for i in dimensions]))
        return sqd

    def triangles(self):
        if hasattr(self, "cavity_triangles"):
            return self.cavity_triangles
        cavity_triangles = []
        step = (self.domain_calculation.discretization.s_step,)*3
        offset = self.domain_calculation.discretization.discrete_to_continuous((0, 0, 0))
        cavity_surface_areas = []
        for multicavity in self.multicavities:
            print multicavity
            grid = np.zeros(self.grid3.shape, dtype=np.bool)
            for cavity_index in multicavity:
                grid = np.logical_or(grid, self.grid3 == -(cavity_index+1))
            views = []
            for x, y, z in itertools.product(*map(xrange, (3, 3, 3))):
                view = grid[x:grid.shape[0]-2+x, y:grid.shape[1]-2+y, z:grid.shape[2]-2+z]
                views.append(view)
            grid = np.zeros(grid.shape, np.uint16)
            grid[:,:,:] = 0
            grid[1:-1, 1:-1, 1:-1] = sum(views)+100
            cavity_triangles.append(triangulate(grid, step, offset, 100+4))
            cavity_surface_area = 0
            for cavity_triangle in cavity_triangles[-1][0]:
                any_outside = False
                for vertex in cavity_triangle:
                    discrete_vertex = discretization.continuous_to_discrete(vertex)
                    if discretization.grid[discrete_vertex] != 0:
                        any_outside = True
                        break
                if not any_outside:
                    v1, v2, v3 = cavity_triangle
                    a = v2-v1
                    b = v3-v1
                    triangle_surface_area = la.norm(np.cross(a,b))*0.5
                    cavity_surface_area += triangle_surface_area
            cavity_surface_areas.append(cavity_surface_area)
        self.cavity_triangles = cavity_triangles
        self.cavity_surface_areas = cavity_surface_areas
        return cavity_triangles

class CalculationResults(object):
    def __init__(self, cavity_calculation_or_filename):
        if isinstance(cavity_calculation_or_filename, CavityCalculation):
            cavity_calculation = cavity_calculation_or_filename
            domain_calculation = cavity_calculation.domain_calculation
            discretization = domain_calculation.discretization
            atom_discretization = domain_calculation.atom_discretization
            atoms = atom_discretization.atoms
            
            # Atom Information
            self.number_of_atoms = len(atoms.positions)
            self.atom_positions = np.array(atoms.positions)
            self.atom_radii = np.array(atoms.radii)
            
            # Domain Results
            self.number_of_domains = len(domain_calculation.centers)
            self.domain_centers = np.array(domain_calculation.centers)
            self.domain_triangles = domain_calculation.domain_triangles
            self.domain_volumes = np.array(domain_calculation.domain_volumes)
            self.domain_surface_areas = np.array(domain_calculation.domain_surface_areas)
            
            # Cavity Results
            self.number_of_multicavities = len(cavity_calculation.multicavities)
            self.multicavities = cavity_calculation.multicavities # Multicavities as sets of cavity domain indices
            self.multicavity_triangles = cavity_calculation.cavity_triangles
            self.multicavity_volumes = np.array(cavity_calculation.multicavity_volumes)
            self.multicavity_surface_areas = np.array(cavity_calculation.cavity_surface_areas)
            self.number_of_center_multicavities = None
            self.center_multicavity_volumes = None
            self.center_multicavity_surface_areas = None
            self.center_multicavities = None
            self.center_multicavity_triangles = None
        else:
            filename = cavity_calculation_or_filename
            with h5py.File(filename, "r") as file:
                self.number_of_atoms = int(file["atom_information/number_of_atoms"].value)
                self.atom_positions = np.array(file["atom_information/atom_positions"])
                self.atom_radii = np.array(file["atom_information/atom_radii"])
                
                self.number_of_domains = int(file["domain_information/number_of_domains"].value)
                self.domain_centers = np.array(file["domain_information/domain_centers"])
                self.domain_volumes = np.array(file["domain_information/domain_volumes"])
                self.domain_surface_areas = np.array(file["domain_information/domain_surface_areas"])
                self.domain_triangles = []
                for domain_index in range(self.number_of_domains):
                    self.domain_triangles.append(np.array(file["domain_information/domain_triangles/%d" % domain_index]))
                
                self.number_of_multicavities = int(file["cavity_information/number_of_multicavities"].value)
                self.multicavity_volumes = np.array(file["cavity_information/multicavity_volumes"])
                self.multicavity_surface_areas = np.array(file["cavity_information/multicavity_surface_areas"])
                self.multicavities = []
                self.multicavity_triangles = []
                for multicavity_index in range(self.number_of_multicavities):
                    self.multicavities.append(set(np.array(file["cavity_information/multicavities/%d" % multicavity_index])))
                    self.multicavity_triangles.append(np.array(file["cavity_information/multicavity_triangles/%d" % multicavity_index]))
                if "center_cavity_information" in file:
                    self.number_of_center_multicavities = int(file["center_cavity_information/number_of_multicavities"].value)
                    self.center_multicavity_volumes = np.array(file["center_cavity_information/multicavity_volumes"])
                    self.center_multicavity_surface_areas = np.array(file["center_cavity_information/multicavity_surface_areas"])
                    self.center_multicavities = []
                    self.center_multicavity_triangles = []
                    for multicavity_index in range(self.number_of_multicavities):
                        self.center_multicavities.append(set(np.array(file["center_cavity_information/multicavities/%d" % multicavity_index])))
                        self.center_multicavity_triangles.append(np.array(file["center_cavity_information/multicavity_triangles/%d" % multicavity_index]))
                else:
                    self.number_of_center_multicavities = None
                    self.center_multicavity_volumes = None
                    self.center_multicavity_surface_areas = None
                    self.center_multicavities = None
                    self.center_multicavity_triangles = None
                    
        
    def export(self, filename):
        with h5py.File(filename, "w") as file:
            file["atom_information/number_of_atoms"] = self.number_of_atoms
            file["atom_information/atom_positions"] = self.atom_positions
            file["atom_information/atom_radii"] = self.atom_radii
            
            file["domain_information/number_of_domains"] = self.number_of_domains
            file["domain_information/domain_centers"] = self.domain_centers
            file["domain_information/domain_volumes"] = self.domain_volumes
            file["domain_information/domain_surface_areas"] = self.domain_surface_areas
            for domain_index in range(self.number_of_domains):
                file["domain_information/domain_triangles/%d" % domain_index] = self.domain_triangles[domain_index]
                
            file["cavity_information/number_of_multicavities"] = self.number_of_multicavities
            file["cavity_information/multicavity_volumes"] = self.multicavity_volumes
            file["cavity_information/multicavity_surface_areas"] = self.multicavity_surface_areas
            for multicavity_index in range(self.number_of_multicavities):
                file["cavity_information/multicavities/%d" % multicavity_index] = np.array(list(self.multicavities[multicavity_index]))
                file["cavity_information/multicavity_triangles/%d" % multicavity_index] = self.multicavity_triangles[multicavity_index]
                
            if self.number_of_center_multicavities is not None:
                file["center_cavity_information/number_of_multicavities"] = self.number_of_center_multicavities
                file["center_cavity_information/multicavity_volumes"] = self.center_multicavity_volumes
                file["center_cavity_information/multicavity_surface_areas"] = self.center_multicavity_surface_areas
                for multicavity_index in range(self.number_of_center_multicavities):
                    file["center_cavity_information/multicavities/%d" % multicavity_index] = np.array(list(self.center_multicavities[multicavity_index]))
                    file["center_cavity_information/multicavity_triangles/%d" % multicavity_index] = self.center_multicavity_triangles[multicavity_index]
                    
    def add_center_cavity_information(self, cavity_calculation):
        self.number_of_center_multicavities = len(cavity_calculation.multicavities)
        self.center_multicavities = cavity_calculation.multicavities
        self.center_multicavity_triangles = cavity_calculation.cavity_triangles
        self.center_multicavity_volumes = np.array(cavity_calculation.multicavity_volumes)
        self.center_multicavity_surface_areas = np.array(cavity_calculation.cavity_surface_areas)
    
class FakeDomainCalculation(object):
    '''
    When calculating center-based cavities, a DomainCalculation object is
    required. This has to provide the domain central points, but not the surface
    points (as those are only needed for surface-based cavity calculation).
    Objects of this class can be used as a drop-in for 'real'
    DomainCalculations, e.g. when the required data is loaded from a file.
    '''
    def __init__(self, discretization, atom_discretization, results):
        self.centers = results.domain_centers
        self.discretization = discretization
        self.atom_discretization = atom_discretization
    
if __name__ == "__main__":
    import pybel

    molecule = pybel.readfile("xyz", "xyz/hexagonal.xyz").next()
    atoms = molecule.atoms
    num_atoms = len(atoms)
    atom_positions = [atom.coords for atom in atoms]

    volume = volumes.HexagonalVolume(17.68943, 22.61158)
    
    print num_atoms,"atoms"
    for atom_index in range(num_atoms):
        atom_positions[atom_index] = volume.get_equivalent_point(atom_positions[atom_index])
    atoms = Atoms(atom_positions, [2.8]*num_atoms)
    print "Volume discretization..."
    discretization_cache = DiscretizationCache('cache.hdf5')
    discretization = discretization_cache.get_discretization(volume, 192)
    print "Atom discretization..."
    atom_discretization = AtomDiscretization(atoms, discretization)
    '''
    print "Cavity domain calculation..."
    domain_calculation = DomainCalculation(discretization, atom_discretization)
    #triangles = domain_calculation.triangles()
    #for domain_index in range(len(triangles)):
    #    print "domain %3d: %fA^3 %fA^2" % (domain_index, domain_calculation.domain_volumes[domain_index], domain_calculation.domain_surface_areas[domain_index])
    #    np.save("domain_triangles_hexagonal_128_26_domain%d.npy"%domain_index, np.array(triangles[domain_index]))
    print "Cavity calculation..."
    cavity_calculation = CavityCalculation(domain_calculation)
    #print "Triangle calculation..."
    #triangles = cavity_calculation.triangles()
    #for cavity_index in range(len(triangles)):
    #    print "cavity %3d: %fA^3 %fA^2" % (cavity_index, cavity_calculation.multicavity_volumes[cavity_index], cavity_calculation.cavity_surface_areas[cavity_index])
    #    np.save("cavity_triangles_hexagonal_128_26_cavity%d.npy"%cavity_index, np.array(triangles[cavity_index]))
    results = CalculationResults(cavity_calculation)
    results.export("test2.hdf5")
    '''
    imported_results = CalculationResults("test2.hdf5")
    domain_calculation = FakeDomainCalculation(discretization, atom_discretization, imported_results)
    cavity_calculation = CavityCalculation(domain_calculation, False)
    imported_results.add_center_cavity_information(cavity_calculation)
    imported_results.export("test3.hdf5")
