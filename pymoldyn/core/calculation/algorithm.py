"""
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

With these objects created, all preparations are complete and the domain and
cavity calculation can be done:

.. code-block:: python

    domain_calculation = DomainCalculation(discretization, atom_discretization)
    cavity_calculation = CavityCalculation(domain_calculation)

Additionally, calculation of center-based cavities is possible by passing an
additional parameter to the CavityCalculation:

.. code-block:: python

    cavity_calculation = CavityCalculation(
        domain_calculation,
        use_surface_points=False,
    )

The FakeDomainCalculation class provides a drop-in replacement for the
domain_calculation object in case the results of a previous calculation need to
be used (this is possible as only those attributes which are stored are
actually used during center-based cavity calculation, which is not the case for
surface-based cavity calculations, which at least require the surface point
lists).

The CalculationResults class provides a container for the results and allows
storage to and retrieval from HDF5 files. These files have several groups which
contain the relevant information.

Author: Florian Rhiem <f.rhiem@fz-juelich.de>
"""

import sys
from math import pi as PI

import numpy as np

from ...computation.split_and_merge.algorithm import ObjectType
from ...computation.split_and_merge.pipeline import start_split_and_merge_pipeline
from ...util import message
from ...util.logger import Logger
from ...util.message import print_message
from ..calculation.gyrationtensor import calculate_gyration_tensor_parameters
from .extension import atomstogrid, cavity_intersections, cavity_triangles, mark_cavities

dimension = 3
dimensions = range(dimension)

logger = Logger("core.calculation.algorithm")
logger.setstream("default", sys.stdout, Logger.WARNING)


class DomainCalculation:
    """
    Cavity domain calulation is performed by the following steps:

    1.  A grid is created with the resolution defined in the volume
        discretization and filled with zeros.

    2.  For each atom, all points in the grid closer to this atom than the
        discrete cavity cutoff radius are set to a point indicating the atom
        index (atom_index+1).

    3.  At this point, every point in the grid which is inside of the volume
        and still has a value of zero is part of a cavity domain. To find these
        domains, an optimized split and merge algorithm is applied to the whole
        grid. It returns the center and surface points of each cavity domain
        (points with a neighbor outside of the cavity domain) stored in lists.
        Points inside of a domain are marked with a negative value indicating
        which domain they are part of.
    """

    def __init__(self, discretization, atom_discretization):
        # step 1
        self.discretization = discretization
        self.atom_discretization = atom_discretization
        self.grid = np.zeros(self.discretization.d, dtype=np.int64)

        message.progress(13)

        # step 2
        atomstogrid(
            self.grid,
            self.atom_discretization.discrete_positions,
            self.atom_discretization.atoms.radii_as_indices,
            self.atom_discretization.sorted_discrete_radii,
            [(0, 0, 0)] + self.discretization.combined_translation_vectors,
            self.discretization.grid,
        )
        message.progress(16)
        # step 3
        result = start_split_and_merge_pipeline(
            self.grid,
            self.discretization.grid,
            self.atom_discretization.discrete_positions,
            self.discretization.combined_translation_vectors,
            self.discretization.get_translation_vector,
            ObjectType.DOMAIN,
        )
        (
            self.centers,
            translated_areas,
            non_translated_areas,
            self.surface_point_list,
            self.cyclic_area_indices,
        ) = result
        print_message("Number of domains:", len(self.centers))
        message.progress(20)

        self.domain_volumes = []
        self.critical_domains = []  # count of very small domains -> domains that can disappear on cutoff radius changes
        for domain_index in range(len(self.centers)):
            current_cell_sum = (self.grid == -(domain_index + 1)).sum()
            if current_cell_sum == 1:
                self.critical_domains.append(domain_index)
            domain_volume = current_cell_sum * (self.discretization.s_step**3)
            self.domain_volumes.append(domain_volume)

        self.characteristic_radii = [(0.75 * volume / PI) ** (1.0 / 3.0) for volume in self.domain_volumes]

        if translated_areas:
            gyration_tensor_parameters = tuple(calculate_gyration_tensor_parameters(area) for area in translated_areas)
            (
                self.mass_centers,
                self.squared_gyration_radii,
                self.asphericities,
                self.acylindricities,
                self.anisotropies,
            ) = zip(*gyration_tensor_parameters)
            self.mass_centers = [
                self.discretization.discrete_to_continuous(point, result_inside_volume=True)
                for point in self.mass_centers
            ]
            self.squared_gyration_radii = [
                self.discretization.discrete_to_continuous(value, unit_exponent=2)
                for value in self.squared_gyration_radii
            ]
        else:
            (
                self.mass_centers,
                self.squared_gyration_radii,
                self.asphericities,
                self.acylindricities,
                self.anisotropies,
            ) = 5 * ([],)

        self.triangles()

    def triangles(self):
        if hasattr(self, "domain_triangles"):
            return self.domain_triangles
        number_of_domains = len(self.centers)
        print_message("Number of domains:", number_of_domains)
        triangles = []
        surface_areas = []
        step = (self.discretization.s_step,) * 3
        offset = self.discretization.discrete_to_continuous((0, 0, 0))
        for domain_index in range(number_of_domains):
            print_message("Calculating triangles for domain", domain_index)
            message.progress(int(20 + (20 / number_of_domains) * domain_index))
            vertices, normals, surface_area = cavity_triangles(
                self.grid, [domain_index], 1, step, offset, self.discretization.grid
            )
            triangles.append((vertices, normals))
            surface_areas.append(surface_area)

        self.domain_triangles = triangles
        self.domain_surface_areas = surface_areas
        return triangles


class CavityCalculation:
    """
    Cavity domain calulation is performed by the following steps:

    1.  The discrete volume grid is divided into subgrid cells with a side
        length based on the maximum discrete cavity cutoff radius. For each
        subgrid, a tuple of three lists is stored (in self.sg).

    2.  The first list for each subgrid cell is filled with the atoms inside
        the cell (their 'real' positions, which might be outside of the
        volume).

    3.  The second and third lists are filled with surface points and their
        domain index. (These might also be moved with the translation vectors
        and might thereby also be outside of the volume.)

    4.  A new grid is created (grid3) and each point in this grid is set to
        zero if it is outside of the volume or part inside of the cavity cutoff
        radius of an atom, or a negative value if it is part of a cavity domain
        (see the domain calculation step 2 for this).

    5.  For each point which is inside the cavity cutoff radius of an
        atom, the nearest atom and the nearest domain surface point are found
        by using the neighbor subgrid cells. If a domain surface point is
        nearer than the nearest atom, than the point belongs to the cavity
        which this surface point belonged to and is marked with a negative
        value.

    6.  At this point, two cavities constructed from two cavity domains might
        actually be one multicavity. In this step, these are found and a list
        of multicavities is created.

    About the subgrid cells:
    If a point inside a subgrid cell was marked as 'near an atom' during the
    domain calculation, then the position of this atom must be either in the
    same cell or in one of the cell's neighbors. This is guaranteed, because
    the atom must be at most its on cavity cutoff radius away, and the subgrid
    cell size is the maximum cavity cutoff radius.


    To calculate center-based cavities, use a grid filled with zeros instead of
    resuing some values from the domain calculation grid and then iterate over
    the domain centers instead of the domain surface points.
    """

    def __init__(
        self,
        domain_calculation,
        use_surface_points=True,
        gyration_tensor_parameters=False,
    ):
        self.domain_calculation = domain_calculation
        if use_surface_points:
            progress_bar_offset = 0
            self.grid = self.domain_calculation.grid
            num_surface_points = sum(map(len, self.domain_calculation.surface_point_list))
            print_message("Number of surface points:", num_surface_points)
        else:
            progress_bar_offset = 30
            self.grid = None

        self.sg_cube_size = self.domain_calculation.atom_discretization.sorted_discrete_radii[0]
        if use_surface_points:
            domain_seed_point_lists = self.domain_calculation.surface_point_list
        else:
            domain_seed_point_lists = [[center] for center in self.domain_calculation.centers]

        discretization = self.domain_calculation.discretization
        atom_discretization = self.domain_calculation.atom_discretization

        # steps 1 to 5
        self.grid3 = mark_cavities(
            self.grid,
            discretization.grid,
            discretization.d,
            self.sg_cube_size,
            atom_discretization.discrete_positions,
            [(0, 0, 0)] + discretization.combined_translation_vectors,
            domain_seed_point_lists,
            use_surface_points,
        )
        message.progress(43 + progress_bar_offset)

        if gyration_tensor_parameters:
            message.print_message("Calculating gyration tensor parameters")
            result = start_split_and_merge_pipeline(
                self.grid3,
                discretization.grid,
                atom_discretization.discrete_positions,
                discretization.combined_translation_vectors,
                discretization.get_translation_vector,
                ObjectType.CAVITY,
                progress=43 + progress_bar_offset,
            )
            translated_areas, non_translated_areas, cyclic_area_indices = result
        message.progress(50 + progress_bar_offset)

        num_domains = len(self.domain_calculation.centers)
        self.cavity_volumes = []
        print(num_domains)
        for domain_index in range(num_domains):
            self.cavity_volumes.append(1.0 * (self.grid3 == -(domain_index + 1)).sum() * (discretization.s_step**3))
            message.progress(int(50 + progress_bar_offset + (7 / num_domains) * domain_index))
        self.characteristic_radii = [(0.75 * volume / PI) ** (1.0 / 3.0) for volume in self.cavity_volumes]

        # step 6
        intersection_table = cavity_intersections(self.grid3, num_domains)
        multicavities = []
        cavity_to_neighbors = num_domains * [None]
        for domain in range(num_domains):
            message.progress(int(55 + progress_bar_offset + (13 / num_domains) * domain))
            current_neighbors = set([domain])
            for neighbor in range(num_domains):
                if intersection_table[domain][neighbor] == 1:
                    current_neighbors.add(neighbor)
            for multicavity in multicavities[:]:
                if any([neighbor in multicavity for neighbor in current_neighbors]):
                    current_neighbors = current_neighbors | multicavity
                    multicavities.remove(multicavity)
            multicavities.append(current_neighbors)
            for neighbor in current_neighbors:
                cavity_to_neighbors[neighbor] = current_neighbors
        self.multicavities = multicavities
        self.multicavity_volumes = []
        for multicavity in multicavities:
            self.multicavity_volumes.append(sum(self.cavity_volumes[cavity_index] for cavity_index in multicavity))
        print_message("Multicavity volumes:", self.multicavity_volumes)

        if gyration_tensor_parameters:
            if len(self.multicavities) == len(
                translated_areas
            ):  # TODO check weather split and merge and multicavity intersection give the same result for multicavities
                # `self.multicavities` entries are sorted by the largest contained neighbor index. Thus sort the indices
                # to access `non_translated_areas` and `translated_areas` to match the order of `self.multicavities`.
                def key_func(cavity_index):
                    cavity_area = non_translated_areas[cavity_index]
                    a_single_cavity_index = -self.grid3[cavity_area[0]] - 1
                    max_neighbor_index = max(cavity_to_neighbors[a_single_cavity_index])
                    return max_neighbor_index

                sorted_area_indices = sorted(range(len(self.multicavities)), key=key_func)
                sorted_translated_areas = [translated_areas[i] for i in sorted_area_indices]
                sorted_cyclic_area_indices = [
                    i for i, index in enumerate(sorted_area_indices) if index in cyclic_area_indices
                ]
                self.cyclic_area_indices = sorted_cyclic_area_indices

                gyration_tensor_parameters = tuple(
                    calculate_gyration_tensor_parameters(area) for area in sorted_translated_areas
                )
                (
                    self.mass_centers,
                    self.squared_gyration_radii,
                    self.asphericities,
                    self.acylindricities,
                    self.anisotropies,
                ) = zip(*gyration_tensor_parameters)
                self.mass_centers = [
                    discretization.discrete_to_continuous(point, result_inside_volume=True)
                    for point in self.mass_centers
                ]
                self.squared_gyration_radii = [
                    discretization.discrete_to_continuous(value, unit_exponent=2)
                    for value in self.squared_gyration_radii
                ]
            else:
                logger.warn("Gyration tensors could not be calculated try increasing the resolution.")
                message.log("Gyration tensors could not be calculated try increasing the resolution.")
                (
                    self.mass_centers,
                    self.squared_gyration_radii,
                    self.asphericities,
                    self.acylindricities,
                    self.anisotropies,
                ) = 5 * ([],)

        self.triangles()

    def squared_distance(self, a, b):
        """
        Calculates the squared distance between two points while taking the
        translation vectors into account.
        """
        sqd = sys.maxsize
        for v in self.domain_calculation.discretization.combined_translation_vectors + [(0, 0, 0)]:
            sqd = min(
                sqd,
                sum([(a[i] - b[i] + v[i]) * (a[i] - b[i] + v[i]) for i in dimensions]),
            )
        return sqd

    def triangles(self):
        if hasattr(self, "cavity_triangles"):
            return self.cavity_triangles
        step = (self.domain_calculation.discretization.s_step,) * 3
        offset = self.domain_calculation.discretization.discrete_to_continuous((0, 0, 0))
        triangles = []
        surface_areas = []
        for i, multicavity in enumerate(self.multicavities):
            print_message("Generating triangles for multicavity:", i + 1)
            vertices, normals, surface_area = cavity_triangles(
                self.grid3,
                multicavity,
                4,
                step,
                offset,
                self.domain_calculation.discretization.grid,
            )
            triangles.append((vertices, normals))
            surface_areas.append(surface_area)

        self.cavity_triangles = triangles
        self.cavity_surface_areas = surface_areas
        return cavity_triangles

    def __getattr__(self, attr):
        optional_attributes = (
            "mass_centers",
            "squared_gyration_radii",
            "asphericities",
            "acylindricities",
            "anisotropies",
            "characteristic_radii",
            "cyclic_area_indices",
        )
        if attr in optional_attributes:
            return None
        else:
            return super(CavityCalculation, self).__getattr__(attr)


class FakeDomainCalculation(object):
    """
    When calculating center-based cavities, a DomainCalculation object is
    required. This has to provide the domain central points, but not the surface
    points (as those are only needed for surface-based cavity calculation).
    Objects of this class can be used as a drop-in for 'real'
    DomainCalculations, e.g. when the required data is loaded from a file.
    """

    def __init__(self, discretization, atom_discretization, results):
        self.centers = results.domains.centers
        self.discretization = discretization
        self.atom_discretization = atom_discretization
