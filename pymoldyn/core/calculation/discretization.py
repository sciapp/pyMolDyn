import collections
import itertools
from math import floor

import h5py
import numpy as np

from ...util.message import print_message
from .. import volumes
from . import algorithm
from .extension import mark_translation_vectors

try:
    import numexpr as ne

    NUMEXPR = True
except ImportError:
    NUMEXPR = False


__all__ = ["DiscretizationCache", "AtomDiscretization"]

dimension = algorithm.dimension
dimensions = algorithm.dimensions


class DiscretizationCache(object):
    """
    Instances of this class use a hdf5-formatted file as a cache for volume
    discretizations.
    """

    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def lock(self):
        try:
            self.file = h5py.File(self.filename, "a")
            if "/discretizations" not in self.file:
                self.file.create_group("/discretizations")
        except IOError:
            self.file = None
        return self

    def unlock(self):
        if self.file is not None:
            self.file.close()
            self.file = None

    def __enter__(self):
        return self.lock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()

    def get_discretization(self, volume, d_max):
        """
        Return a cached discretization are generate a new one, store it in the
        cache file and then return it.
        """
        discretization_repr = repr(volume) + " d_max=%d" % d_max
        print_message(
            "{volume}, discretization resolution: {resolution:d}".format(volume=repr(volume), resolution=d_max)
        )
        if self.file is not None and discretization_repr in self.file["/discretizations"]:
            stored_discretization = self.file["/discretizations/" + discretization_repr]
            grid = np.array(stored_discretization)
            discretization = Discretization(volume, d_max, grid)
        else:
            discretization = Discretization(volume, d_max)
            grid = discretization.grid
            if self.file is not None:
                self.file["/discretizations/" + discretization_repr] = grid
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
            name, value = argument.split("=")
            value = float(value)
            arguments[name] = value
        volume = volume_class(**arguments)
        d_max_info = string_parts[-1]
        if not d_max_info.startswith("d_max="):
            raise Exception('Any volume discretization information string must end with "d_max=<d_max>".')
        d_max = float(d_max_info[len("d_max=") :])
        return self.get_discretization(volume, d_max)


class Discretization(object):
    """
    Instances of this class represent a discrete version of a volume.

    The discretization is done in the following steps:

    1.  For a given maximum resolution of the resulting discrete representation
        (d_max), the length of the discretization cells (s_step) is calculated.

    2.  The actual resolutions of the resulting discrete representation (d) are
        calculated and the side lengths of corresponding bounding cuboid
        (s_tilde) are calculated. (After this point, the transformation
        functions discrete_to_continuous(p) and continuous_to_discrete(p) can
        be used.)

    3.  The volume's translation vectors are discretized (translation_vectors)
        and combinations of these are calculated
        (combined_translation_vectors).

    4.  An integer grid is created and for each discrete point, it stores
        either 0 if the point is inside the volume or 1 if it is outside the
        volume.

    5.  In the grid, for each point which is inside the volume (value = 0) all
        points created by addition of a combined translation vector are defined
        to be outside of the volume (value = 1), except for the point itself.
        After this, there is no equivalent pair of points, which both are
        inside the volume.

    6.  At this point there might still be some points in the grid though,
        which have no equivalent point inside of the volume (value = 0). For
        each of these points, all equivalent points are found and from these,
        the one closest to the center (continuous coordinates (0,0,0)) is
        defined to be inside the volume.

    7.  For each point which is outside of the volume (value = 1). A negative
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
        print_message("Step length:", self.s_step)

        # step 2
        dimensions = range(len(self.s))
        self.d = [int(floor(self.s[i] / self.s_step) + 4) for i in dimensions]
        for i in dimensions:
            if self.d[i] % 2 == 1:
                self.d[i] += 1
        print_message(
            "Resolution per axis: (x: {x:d}, y: {y:d}, z: {z:d})".format(x=self.d[0], y=self.d[1], z=self.d[2])
        )
        self.s_tilde = [(self.d[i] - 1) * self.s_step for i in dimensions]

        # step 3
        self.translation_vectors = [
            [int(floor(c / self.s_step + 0.5)) for c in v] for v in self.volume.translation_vectors
        ]
        # TODO: remove unnecessary vectors in hexagonal volumes
        self.combined_translation_vectors = [
            [sum([v[0][j] * v[1] for v in zip(self.translation_vectors, i)]) for j in dimensions]
            for i in itertools.product((-1, 0, 1), repeat=len(dimensions))
            if any(i)
        ]

        if grid is not None:
            self.grid = grid
        else:
            # step 4
            self.grid = np.zeros(self.d, dtype=np.int8)
            # create array similar to itertools.product
            order = [i + 1 for i in range(len(dimensions))] + [0]
            points = np.indices(self.d).transpose(*order).reshape((-1, len(dimensions)))
            # choose points that are not inside
            inside = self.volume.is_inside(self.discrete_to_continuous(points))
            outside_points = points.compress(np.logical_not(inside), axis=0)
            del points
            # convert to a tuple of indices
            indices = tuple([outside_points[:, i] for i in range(len(dimensions))])
            self.grid[indices] = 1
            del outside_points
            del inside
            del indices
            # steps 5, 6, 7
            mark_translation_vectors(self.grid, self.combined_translation_vectors)
        translation_vector_output = ", ".join(["({0}, {1}, {2})".format(*vec) for vec in self.translation_vectors])
        print_message("Translation vectors:", translation_vector_output)

    def get_direct_neighbors(self, point):
        """
        This method returns the direct neighbor points of a given point.
        """
        neighbors_without_bound_checks = [
            [point[j] + i[j] for j in dimensions] for i in itertools.product((-1, 0, 1), repeat=dimension) if any(i)
        ]
        direct_neighbors = [
            tuple(neighbor)
            for neighbor in neighbors_without_bound_checks
            if all([0 <= neighbor[j] <= self.d[j] - 1 for j in dimensions])
        ]
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
        # If the point cannot be translated directly, shift it in the direction of the cell center by
        # applying one of the discrete translation vectors in each step until the point is inside the
        # discretization grid
        cell_center = None
        while not all(0 <= p < s for p, s in zip(point, self.grid.shape)):
            if cell_center is None:
                cell_center = np.array(self.grid.shape, dtype=np.int32) // 2
                translation_vectors = np.array(self.translation_vectors)
                normalized_translation_vectors = (translation_vectors.T / np.linalg.norm(translation_vectors, axis=1)).T
            vector_to_cell_center = cell_center - np.array(point, dtype=np.int32)
            vector_to_cell_center = vector_to_cell_center / np.linalg.norm(vector_to_cell_center)
            dot_products = np.dot(normalized_translation_vectors, vector_to_cell_center)
            rounded_dot_products = np.array(np.round(dot_products), dtype=np.int32)
            needed_translation_vector_index = np.argmax(np.abs(dot_products))
            needed_translation_vector = (
                rounded_dot_products[needed_translation_vector_index]
                * translation_vectors[needed_translation_vector_index]
            )
            next_point = tuple(p + t for p, t in zip(point, needed_translation_vector))
            if next_point == point:
                raise ArithmeticError("Could not determine an equivalent point inside the volume")
            point = next_point
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

    def continuous_to_discrete(self, arg, result_inside_volume=False, unit_exponent=1):
        """
        Transforms a single value or a point from continuous to discrete coordinates.
        If a point is given, ``result_inside_volume`` can be set to shift the result into the volume cell if
        necessary (equivalent point).
        In case of a single value input, 'unit_exponent' is used as exponent of the scaling factor.
        """

        def transform_point(point, result_inside_volume):
            if isinstance(point, np.ndarray) and len(point.shape) > 1:
                s_tilde_bc = np.tile(self.s_tilde, (point.shape[0], 1))
                print("s_tilde_bc", s_tilde_bc)
                result = np.array(
                    np.floor((point + s_tilde_bc / 2) / self.s_step + 0.5),
                    dtype=np.int32,
                )
                if result_inside_volume:
                    result = np.array(self.get_equivalent_point_in_volume(result))
            else:
                result = tuple(int(floor((point[i] + self.s_tilde[i] / 2) / self.s_step + 0.5)) for i in dimensions)
                if result_inside_volume:
                    result = self.get_equivalent_point_in_volume(result)
            return result

        def transform_value(value, unit_exponent):
            return int(floor(value / (self.s_step**unit_exponent) + 0.5))

        if isinstance(arg, collections.abc.Iterable):
            return transform_point(arg, result_inside_volume)
        else:
            return transform_value(arg, unit_exponent)

    def discrete_to_continuous(self, arg, result_inside_volume=False, unit_exponent=1):
        """
        Transforms a single value or a point from discrete to continuous coordinates.
        If a point is given, ``result_inside_volume`` can be set to shift the result into the volume cell if
        necessary (equivalent point).
        In case of a single value input, 'unit_exponent' is used as exponent of the scaling factor.
        """

        def transform_point(point):
            if isinstance(point, np.ndarray) and len(point.shape) > 1:
                if result_inside_volume:
                    if any(isinstance(c, float) for c in point):
                        rounded_point = np.array(np.around(point), dtype=np.int32)
                        rounded_diff = point - rounded_point
                        rounded_point = np.array(self.get_equivalent_point_in_volume(rounded_point))
                        point = rounded_point + rounded_diff
                    else:
                        point = np.array(self.get_equivalent_point_in_volume(point))
                if NUMEXPR:
                    s_tilde_bc = np.tile(self.s_tilde, (point.shape[0], 1))
                    s_step = self.s_step  # noqa: F841
                    return ne.evaluate("point * s_step - s_tilde_bc / 2")
                else:
                    s_tilde_bc = np.tile(self.s_tilde, (point.shape[0], 1))
                    return point * self.s_step - s_tilde_bc / 2
            else:
                if result_inside_volume:
                    if any(isinstance(c, float) for c in point):
                        rounded_point = tuple(int(round(c)) for c in point)
                        rounded_diff = tuple(c1 - c2 for c1, c2 in zip(point, rounded_point))
                        rounded_point = self.get_equivalent_point_in_volume(rounded_point)
                        point = tuple(c1 + c2 for c1, c2 in zip(rounded_point, rounded_diff))
                    else:
                        point = self.get_equivalent_point_in_volume(point)
                return tuple(point[k] * self.s_step - self.s_tilde[k] / 2 for k in dimensions)

        def transform_value(value, unit_exponent):
            return value * (self.s_step**unit_exponent)

        if isinstance(arg, collections.abc.Iterable):
            return transform_point(arg)
        else:
            return transform_value(arg, unit_exponent)

    def __repr__(self):
        return repr(self.volume) + " d_max=%d" % self.d_max


class AtomDiscretization:
    """
    Instances of this class represent a list of atoms in a discrete volume.
    """

    def __init__(self, atoms, discretization):
        self.atoms = atoms
        self.discretization = discretization
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
        print_message("Maximum radius:", self.sorted_discrete_radii[0])
