# -*- coding: utf-8 -*-

from math import floor
import itertools
import numpy as np
import h5py
from util.message import print_message, progress, finish
import algorithm

__all__ = ["DiscretizationCache",
           "AtomDiscretization"]

dimension = algorithm.dimension
dimensions = algorithm.dimensions


class DiscretizationCache(object):
    """
    Instances of this class use a hdf5-formatted file as a cache for volume
    discretizations.
    """

    def __init__(self, filename):
        self.file = h5py.File(filename, 'a')
        if '/discretizations' not in self.file:
            self.file.create_group('/discretizations')

    def get_discretization(self, volume, d_max):
        """
        Return a cached discretization are generate a new one, store it in the
        cache file and then return it.
        """
        discretization_repr = repr(volume) + " d_max=%d" % d_max
        print_message(discretization_repr)
        if discretization_repr in self.file['/discretizations']:
            stored_discretization = self.file['/discretizations/' + discretization_repr]
            grid = np.array(stored_discretization)
            discretization = Discretization(volume, d_max, grid)
        else:
            discretization = Discretization(volume, d_max)
            grid = discretization.grid
            self.file['/discretizations/' + discretization_repr] = grid
            self.file.flush()
        return discretization

    def get_discretization_from_string(self, string):
        string_parts = string.split()
        volume_type = string_parts[0]
        volume_type = volume_type.title() + "Volume"
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
    """
    Instances of this class represent a discrete version of a volume.

    The discretization is done in the following steps:
     1. For a given maximum resolution of the resulting discrete representation
        (d_max), the length of the discretization cells (s_step) is calculated.
     2. The actual resolutions of the resulting discrete representation (d) are
        calculated and the side lengths of corresponding bounding cuboid
        (s_tilde) are calculated. (After this point, the transformation
        functions discrete_to_continuous(p) and continuous_to_discrete(p) can
        be used.)
     3. The volume's translation vectors are discretized (translation_vectors)
        and combinations of these are calculated
        (combined_translation_vectors).
     4. An integer grid is created and for each discrete point, it stores
        either 0 if the point is inside the volume or 1 if it is outside the
        volume.
     5. In the grid, for each point which is inside the volume (value = 0) all
        points created by addition of a combined translation vector are defined
        to be outside of the volume (value = 1), except for the point itself.
        After this, there is no equivalent pair of points, which both are
        inside the volume.
     6. At this point there might still be some points in the grid though,
        which have no equivalent point inside of the volume (value = 0). For
        each of these points, all equivalent points are found and from these,
        the one closest to the center (continuous coordinates (0,0,0)) is
        defined to be inside the volume.
     7. For each point which is outside of the volume (value = 1). A negative
        value is set to indicate which combined translation vector leads to the
        equivalent point inside the volume.
    """

    def __init__(self, volume, d_max, grid=None):
        # step 1
        self.d_max = d_max
        self.volume = volume
        self.s = volume.side_lengths
        self.s_max = max(self.s)
        if self.d_max % 2 == 1:
            self.d_max -= 1
        self.s_step = self.s_max / (self.d_max - 4)
        print_message("s_step", self.s_step)

        # step 2
        self.d = [int(floor(self.s[i] / self.s_step) + 4) for i in dimensions]
        for i in dimensions:
            if self.d[i] % 2 == 1:
                self.d[i] += 1
        print_message("d", self.d)
        self.s_tilde = [(self.d[i] - 1) * self.s_step for i in dimensions]

        # step 3
        self.translation_vectors = [[int(floor(c / self.s_step + 0.5)) for c in v] for v in
                                    self.volume.translation_vectors]
        # TODO: remove unnecesary vectors in hexagonal volumes
        self.combined_translation_vectors = [
            [sum([v[0][j] * v[1] for v in zip(self.translation_vectors, i)]) for j in dimensions] for i in
            itertools.product((-1, 0, 1), repeat=dimension) if any(i)]

        if grid is not None:
            self.grid = grid
        else:
            # step 4
            self.grid = np.zeros(self.d, dtype=np.int8)
            # create array similar to itertools.product
            order = [i + 1 for i in range(dimension)] + [0]
            points = np.indices(self.d).transpose(*order).reshape((-1, dimension))
            # choose points that are not inside
            inside = self.volume.is_inside(self.discrete_to_continuous(points))
            points = points.compress(np.logical_not(inside), axis=0)
            # convert to tuple of indices
            indices = [points[:, i] for i in range(dimension)]
            self.grid[indices] = 1
            points = None
            inside = None
            indices = None
            if False:
                # step 5
                for p in itertools.product(*map(range, self.d)):
                    equivalent_points = [[p[i] + v[i] for i in dimensions] for v in self.combined_translation_vectors]
                    valid_equivalent_points = [tuple(point) for point in equivalent_points if
                                               all([0 <= point[i] <= self.d[i] - 1 for i in dimensions])]
                    if self.grid[p] == 0:
                        equivalent_points_inside = [point for point in valid_equivalent_points if self.grid[point] == 0]
                        for point in equivalent_points_inside:
                            self.grid[point] = 1
                # step 6 & 7
                for p in itertools.product(*map(range, self.d)):
                    equivalent_points = [([p[i] + v[i] for i in dimensions], vi) for vi, v in
                                         enumerate(self.combined_translation_vectors)]
                    valid_equivalent_points = [(tuple(point), vi) for point, vi in equivalent_points if
                                               all([0 <= point[i] <= self.d[i] - 1 for i in dimensions])]
                    if self.grid[p] == 1:
                        equivalent_points_inside = [(point, vi) for point, vi in valid_equivalent_points if
                                                    self.grid[point] == 0]
                        if not equivalent_points_inside:
                            nearest_to_center = p
                            nearest_to_center_index = -1  # -1 -> -(-1+1) == 0
                            min_d_center = sum([(p[i] - self.d[i] / 2) * (p[i] - self.d[i] / 2) for i in dimensions])
                            for p2, vi in valid_equivalent_points:
                                d_center = sum([(p2[i] - self.d[i] / 2) * (p2[i] - self.d[i] / 2) for i in dimensions])
                                if d_center < min_d_center:
                                    min_d_center = d_center
                                    nearest_to_center = p2
                                    nearest_to_center_index = vi
                            self.grid[nearest_to_center] = 0
                            self.grid[p] = -(nearest_to_center_index + 1)
                        else:
                            combined_translation_vector_index = equivalent_points_inside[0][1]
                            self.grid[p] = -(combined_translation_vector_index + 1)
        print_message("translation vectors", self.translation_vectors)

    def get_direct_neighbors(self, point):
        '''
        This method returns the direct neighbor points of a given point.
        '''
        neighbors_without_bound_checks = [[point[j] + i[j] for j in dimensions] for i in
                                          itertools.product((-1, 0, 1), repeat=dimension) if any(i)]
        direct_neighbors = [tuple(neighbor) for neighbor in neighbors_without_bound_checks if
                            all([0 <= neighbor[j] <= self.d[j] - 1 for j in dimensions])]
        return direct_neighbors

    def get_neighbors_in_volume(self, point):
        """
        This method returns the neighbor points of a given point, which are
        inside the volume.
        """
        direct_neighbors = self.get_direct_neighbors(point)
        neighbors_in_volume = map(self.get_equivalent_point_in_volume, direct_neighbors)
        return neighbors_in_volume

    def get_equivalent_point_in_volume(self, point):
        """
        For a point given in discrete coordinates, this method returns the
        point which is inside of the volume and is equivalent to the given
        point.
        """
        if self.grid[point] == 0:
            return point
        else:
            combined_translation_vector_index = -self.grid[point] - 1
            combined_translation_vector = self.combined_translation_vectors[combined_translation_vector_index]
            return tuple([point[i] + combined_translation_vector[i] for i in dimensions])

    def get_translation_vector(self, point):
        combined_translation_vector_index = -self.grid[point] - 1
        combined_translation_vector = self.combined_translation_vectors[combined_translation_vector_index]
        return combined_translation_vector

    def continuous_to_discrete(self, point):
        """
        Transforms a point from continuous to discrete coordinates.
        """
        if isinstance(point, np.ndarray) and len(point.shape) > 1:
            s_tilde_bc = np.tile(self.s_tilde, (point.shape[0], 1))
            return np.array(np.floor((point + s_tilde_bc / 2) / self.s_step + 0.5), dtype=np.int)
        else:
            return tuple([int(floor((point[i] + self.s_tilde[i] / 2) / self.s_step + 0.5)) for i in dimensions])

    def discrete_to_continuous(self, point):
        """
        Transforms a point from discrete to continuous coordinates.
        """
        if isinstance(point, np.ndarray) and len(point.shape) > 1:
            s_tilde_bc = np.tile(self.s_tilde, (point.shape[0], 1))
            return point * self.s_step - s_tilde_bc / 2
        else:
            return tuple([point[k] * self.s_step - self.s_tilde[k] / 2 for k in dimensions])

    def __repr__(self):
        return repr(self.volume) + " d_max=%d" % self.d_max


class AtomDiscretization:
    """
    Instances of this class represent a list of atoms in a discrete volume.
    """

    def __init__(self, atoms, discretization):
        self.discretization = discretization
        self.atoms = atoms
        self.sorted_discrete_radii = []
        self.discrete_radii = []
        self.discrete_positions = []
        for radius_index, position in zip(self.atoms.radii_as_indices, self.atoms.sorted_positions):
            radius = self.atoms.sorted_radii[radius_index]
            discrete_position = self.discretization.continuous_to_discrete(position)
            self.discrete_positions.append(discrete_position)
        for radius in self.atoms.sorted_radii:
            discrete_radius = int(floor(radius / self.discretization.s_step + 0.5))
            self.sorted_discrete_radii.append(discrete_radius)
        print_message("maximum radius:", self.sorted_discrete_radii[0])
