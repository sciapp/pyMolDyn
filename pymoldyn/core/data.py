"""
This module contains classes that are used to store data in pyMolDyn.
Most of them can be read and written to hdf5 files.
"""

import collections
import os
import sys
from datetime import datetime

import dateutil.parser
import h5py
import numpy as np

from ..config.configuration import config
from ..util.logger import Logger
from . import bonds, elements, volumes

logger = Logger("core.data")
logger.setstream("default", sys.stdout, Logger.WARNING)


__all__ = [
    "Atoms",
    "Domains",
    "Cavities",
    "Results",
    "FileInfo",
    "ResultInfo",
    "CalculatedFrames",
]


def writedataset(h5group, name, data, overwrite=True):
    """
    Write a dataset to a hdf5 file.
    The `overwrite` parameter controls the behaviour when the dataset
    already exists.
    """
    if name in h5group:
        if overwrite:
            del h5group[name]
        else:
            return False
    h5group[name] = data
    return True


class TimestampList(object):
    """
    A `list`-like structure with a fixed length to store :class:`datetime`
    objects.  For each frame it contains a calculation date or `None`.
    """

    def __init__(self, *args):
        """
        Creates an empty :class:`TimestampList` with a given length
        or copies values from a `list`.

        The constructor can be called in two ways:

        - ``TimestampList(num_frames)`` :
            create an empty :class:`TimestampList` with the length `num_frames`

        - ``TimestampList(list)`` :
            copy the values from the given list of strings
        """
        if isinstance(args[0], list):
            arr = args[0]
            self.timestamps = [None] * len(arr)
            for i, s in enumerate(arr):
                if len(s) > 0:
                    self.timestamps[i] = dateutil.parser.parse(s)
        else:
            num_frames = args[0]
            self.timestamps = [None] * num_frames

    @property
    def num_frames(self):
        return len(self.timestamps)

    def __getitem__(self, index):
        if 0 <= index < len(self.timestamps):
            return self.timestamps[index]
        else:
            return None

    def __setitem__(self, index, value):
        if not isinstance(value, datetime):
            raise ValueError("datetime required")
        self.timestamps[index] = value

    def __len__(self):
        return len(self.timestamps)

    def __iter__(self):
        return iter(self.timestamps)

    def hasdata(self):
        """
        Test if the list contains any data.

        **Returns:**
            If any item is not `None`
        """
        return any(map(lambda x: x is not None, self.timestamps))

    def tostrlist(self):
        """
        Converts the :class:`datetime` objects to strings.
        `None` values are converted to empty strings.

        **Returns:**
            A list of strings
        """
        return ["" if x is None else str(x) for x in self.timestamps]

    def prettystrings(self):
        """
        Converts the :class:`datetime` objects to human-readable strings.
        `None` values are converted to "X".

        **Returns:**
            A list of strings
        """

        def fmt(t):
            if t is None:
                return "X"
            else:
                return t.strftime("%d.%m.%Y %H:%M:%S")

        return map(fmt, self.timestamps)


class CalculatedFrames(object):
    """
    Contains information what results are calculated for what frame.
    The information about the three kinds of results are stored in
    these attributes of the type :class:`TimestampList`:

        `domains`

        `surface_cavities`

        `center_cavities`
    """

    def __init__(self, *args):
        """
        Creates an empty object or reads it from a hdf5 file.

        The constructor can be called in two ways:

        - ``CalculatedFrames(num_frames)`` :
            create an empty `CalculatedFrames` which can store information
            about `num_frames` frames

        - ``CalculatedFrames(hdf5group)`` :
            read the data from this hdf5 group
        """
        if isinstance(args[0], h5py.Group):
            h5group = args[0]
            dom_ts = list(h5group["domains"])
            sur_ts = list(h5group["surface_cavities"])
            cen_ts = list(h5group["center_cavities"])
            num_frames = len(dom_ts)
            self.domains = TimestampList(dom_ts)
            self.surface_cavities = TimestampList(sur_ts)
            self.center_cavities = TimestampList(cen_ts)
        else:
            num_frames = args[0]
            self.domains = TimestampList(num_frames)
            self.surface_cavities = TimestampList(num_frames)
            self.center_cavities = TimestampList(num_frames)

    @property
    def num_frames(self):
        return self.domains.num_frames

    def hasdata(self):
        """
        Test if member contains any data.

        **Returns:**

            If the `hasdata` method of any of the :class:`TimestampList`
            attributes returns `True`
        """
        return self.domains.hasdata() or self.surface_cavities.hasdata() or self.center_cavities.hasdata()

    def tohdf(self, h5group, overwrite=True):
        """
        Write the data to a hdf5 Group.

        **Parameters:**
            `h5group` :
                the hdf5 group in which the data will be written

            `overwrite` :

                specifies if existing data should be overwritten
        """
        if self.hasdata():
            writedataset(h5group, "domains", self.domains.tostrlist(), overwrite)
            writedataset(
                h5group,
                "surface_cavities",
                self.surface_cavities.tostrlist(),
                overwrite,
            )
            writedataset(h5group, "center_cavities", self.center_cavities.tostrlist(), overwrite)


class FileInfo(object):
    """
    Contains information about input files:

        `num_frames` :
            number of frames which are stored in the file

        `volumestr` :
            representative string of the volume the atoms are in

        `volume` :
            the corresponding `Volume` object itself

    """

    def __init__(self, num_frames=None, volumestr=None, volume_guessed=False):
        """
        **Parameters:**
            `num_frames` :
                number of frames which are stored in the file

            `volumestr` :
                representative string of the volume the atoms are in
        """
        self.num_frames = num_frames
        self.volumestr = volumestr
        self._volume = None
        self.volume_guessed = volume_guessed

    @property
    def volume(self):
        if self._volume is None and self.volumestr is not None:
            self._volume = volumes.Volume.fromstring(self.volumestr)
        return self._volume


class ResultInfo(FileInfo):
    """
    Information about a :class:`core.file.ResultFile`:

        `num_frames` :
            number of frames which are stored in the file

        `volumestr` :
            representative string of the volume the atoms are in

        `volume` :
            the corresponding `Volume` object itself

        `sourcefilepath` :
            path of the file which contains the original input data

        `calculatedframes` :
            dictionary which associates a resolution with a
            `CalculatedFrames` object
    """

    def __init__(self, *args):
        """
        The constructor can be called in two ways:

        - ``ResultInfo()`` :
            create an empty :class:`ResultInfo` object

        - ``ResultInfo(hdf5group)`` :
            read the data from this hdf5 group
        """
        super().__init__()
        self.sourcefilepath = None
        self.calculatedframes = dict()
        if len(args) > 0 and isinstance(args[0], h5py.Group):
            h5group = args[0]
            self.num_frames = int(h5group.attrs["num_frames"])
            self.volumestr = str(h5group.attrs["volume"])
            if "sourcefile" in h5group.attrs:
                self.sourcefilepath = str(h5group.attrs["sourcefile"])
            else:
                self.sourcefilepath = None
            for name, subgroup in h5group.items():
                if not name.startswith("resolution"):
                    continue
                resolution = int(name[10:])
                self.calculatedframes[resolution] = CalculatedFrames(subgroup)

    def __getitem__(self, resolution):
        """
        Get a :class:`CalculatedFrames` object for the specified resulotion.

        **Parameters:**
            `resolution`:
                the resolution for which the information will be queried

        **Returns:**
            A :class:`CalculatedFrames` object with information about
            existing calculations.
        """
        if resolution not in self.calculatedframes:
            self.calculatedframes[resolution] = CalculatedFrames(self.num_frames)
        return self.calculatedframes[resolution]

    def __contains__(self, resolution):
        """
        Check if any information about the given resolution is available.

        **Parameters:**
            `resolution`:
                the resolution for which the information will be queried

        **Returns:**
            If a :class:`CalculatedFrames` object for this resolution exists
        """
        return resolution in self.calculatedframes

    def resolutions(self):
        return self.calculatedframes.keys()

    def tohdf(self, h5group, overwrite=True):
        """
        Write the data to a hdf5 Group.

        **Parameters:**
            `h5group` :
                the hdf5 group in which the data will be written

            `overwrite` :
                specifies if existing data should be overwritten
        """
        h5group.attrs["num_frames"] = self.num_frames
        h5group.attrs["volume"] = self.volumestr
        if self.sourcefilepath is not None:
            h5group.attrs["sourcefile"] = self.sourcefilepath
        elif "sourcefile" in h5group.attrs:
            del h5group.attrs["sourcefile"]
        for resolution, info in self.calculatedframes.items():
            if info.hasdata():
                subgroup = h5group.require_group("resolution{}".format(resolution))
                info.tohdf(subgroup, overwrite)


class Atoms(object):
    """
    This class represents a list of atoms and their properties:

        - `number`

        - `positions`

        - `volume` :
            the volume that contains the atoms

        - `radii` :
            cavity cutoff radius

        - `sorted_positions` :
            `positions` sorted from largest to smallest radius

        - `sorted_radii` :
            unique `radii` sorted from largest to smallest

        - `radii_as_indices` :
            indices to associate an atom in `sorted_positions` with an element
            of `sorted_radii`
    """

    def __init__(self, *args):
        """
        The constructor can be called in three ways:

        - ``Atoms(positions, radii, elements, volume)`` :
            create the object using the given data

        - ``Atoms(molecule, volume)`` :
            read the data from this :class:`pybel.Molecule` object

        - ``Atoms(hdf5group)`` :
            read the data from this hdf5 group
        """
        if isinstance(args[0], h5py.Group):
            h5group = args[0]
            positions = h5group["positions"]
            radii = h5group["radii"]
            if "elements" in h5group:
                elements = h5group["elements"]
            else:
                logger.warn("Dataset 'elements' not found. Using 'atom' as default value")
                elements = np.empty(len(radii), dtype="|S4")
                elements[:] = "atom"
            if "volume" in h5group.attrs:
                volume = h5group.attrs["volume"]
            else:
                volume = h5group.parent.attrs["volume"]
            volume = volumes.Volume.fromstring(str(volume))
        else:
            # in these two cases atom positions may be outside of the volume
            positions = args[0]
            radii = args[1]
            elements = args[2]
            volume = args[3]

            if isinstance(volume, str):
                volume = volumes.Volume.fromstring(volume)
            if volume is not None:
                positions = map(lambda pos: volume.get_equivalent_point(pos), positions)
        self.volume = volume
        self.positions = np.asarray(list(positions), dtype=np.float64)
        self.number = self.positions.shape[0]
        self.elements = np.asarray(elements, dtype="|S4")
        self.radii = radii

        self._covalence_radii = None
        self._covalence_radii_by_element = None
        self._bonds = None
        self._colors = None

    @property
    def covalence_radii(self):
        if self._covalence_radii is None:
            covalence_radii = np.zeros(self.number, np.float32)
            for i, element in enumerate(self.elements):
                element_number = elements.numbers[element.upper().decode("utf-8")]
                covalence_radii[i] = elements.radii[element_number]
            self._covalence_radii = covalence_radii
        return self._covalence_radii

    @property
    def covalence_radii_by_element(self):
        covalence_radii = self.covalence_radii
        if self._covalence_radii_by_element is None:
            self._covalence_radii_by_element = dict(
                (element, covalence_radius) for element, covalence_radius in zip(self.elements, covalence_radii)
            )
        return self._covalence_radii_by_element

    @property
    def bonds(self):
        if self._bonds is None:
            self._bonds = bonds.get_bonds_with_radii(self, 1.15)
            self._bonds = bonds.get_bonds_symetric_indicies(self._bonds)
        return self._bonds

    @property
    def colors(self):
        if self._colors is None:
            colors = np.zeros((self.number, 3), np.float32)
            for i, element in enumerate(self.elements):
                element_number = elements.numbers[element.decode("utf-8").upper()]
                colors[i] = elements.colors[element_number]
            self._colors = colors / 255
        return self._colors

    @property
    def radii(self):
        return self._radii

    @radii.setter
    def radii(self, values):
        if values is None:
            self._radii = np.ones((self.number), dtype=np.float64) * config.Computation.std_cutoff_radius
        elif isinstance(values, collections.abc.Mapping):
            radii = [values[elem] for elem in self.elements]
            self._radii = np.asarray(radii, dtype=np.float64)
        elif isinstance(values, collections.abc.Iterable):
            self._radii = np.asarray(values, dtype=np.float64)
        else:
            self._radii = np.ones((self.number), dtype=np.float64) * values
        indices = np.argsort(-self._radii, kind="mergesort")
        self.sorted_positions = self.positions[indices]
        unique_radii, indices = np.unique(-self._radii, return_inverse=True)
        self.sorted_radii = -unique_radii
        self.radii_as_indices = np.sort(indices)

    def tohdf(self, h5group, overwrite=True):
        """
        Write the data to a hdf5 Group.

        **Parameters:**
            `h5group` :
                the hdf5 group in which the data will be written

            `overwrite` :
                specifies if existing data should be overwritten
        """
        h5group.parent.attrs["volume"] = str(self.volume)
        writedataset(h5group, "positions", self.positions, overwrite)
        writedataset(h5group, "radii", self.radii, overwrite)
        if np.any(self.elements == "atom"):
            logger.warn("Atom.elements contains default values. Not writing dataset.")
        else:
            writedataset(h5group, "elements", self.elements, overwrite)

    def totxt(self, fmt):
        bond_file_name = fmt.format(property="bonds")
        bond_angle_file_name = fmt.format(property="bond_angles")
        bond_chain_angle_file_name = fmt.format(property="bond_dihedral_angles")

        bond_angles, bond_chain_angles = bonds.calculate_bond_angles(self, self.bonds)
        with open(bond_file_name, "w") as outfile:
            for source_index, target_indices in enumerate(self.bonds):
                for target_index in target_indices:
                    outfile.write("{} {}\n".format(source_index + 1, target_index + 1))
        with open(bond_angle_file_name, "w") as outfile:
            for bond1, bond2 in bond_angles.keys():
                if bond1[0] > bond2[1]:
                    outfile.write(
                        "{} {} {} {}\n".format(
                            bond1[0] + 1,
                            bond1[1] + 1,
                            bond2[1] + 1,
                            bond_angles[bond1, bond2],
                        )
                    )
        with open(bond_chain_angle_file_name, "w") as outfile:
            for bond_chain, angle in bond_chain_angles.items():
                outfile.write("{} {} {} {}".format(*[index + 1 for index in bond_chain]))
                outfile.write(" {}\n".format(angle))

    def tosingletxt(self, fmt):
        bond_angles, bond_chain_angles = bonds.calculate_bond_angles(self, self.bonds)
        fmt.write("Bonds:\n")
        for source_index, target_indices in enumerate(self.bonds):
            for target_index in target_indices:
                fmt.write("{} {}\n".format(source_index + 1, target_index + 1))
        fmt.write("Bond Angles:\n")
        for bond1, bond2 in bond_angles.keys():
            if bond1[0] > bond2[1]:
                fmt.write(
                    "{} {} {} {}\n".format(
                        bond1[0] + 1,
                        bond1[1] + 1,
                        bond2[1] + 1,
                        bond_angles[bond1, bond2],
                    )
                )
        fmt.write("Bond Dihedral Angles:\n")
        for bond_chain, angle in bond_chain_angles.items():
            fmt.write("{} {} {} {}".format(*[index + 1 for index in bond_chain]))
            fmt.write(" {}\n".format(angle))


class CavitiesBase(object):
    """
    Base class to store multiple surface-based objects in the 3-dimensional
    space. The :class:`Domains` and :class:`Cavities` class inherit from it.
    """

    def __init__(self, *args):
        """
        The constructor can be called in two ways:

        - ``CavitiesBase(timestamp, volumes, surface_areas, triangles)`` :
            create the object using the given data

        - ``CavitiesBase(hdf5group)`` :
            read the data from this hdf5 group
        """
        if isinstance(args[0], h5py.Group):

            def getobj_from_h5group(attr):
                if attr in h5group:
                    return h5group[attr]
                else:
                    return None

            h5group = args[0]
            timestamp = dateutil.parser.parse(h5group.attrs["timestamp"])
            number = int(h5group.attrs["number"])
            volumes = getobj_from_h5group("volumes")
            surface_areas = getobj_from_h5group("surface_areas")
            triangles = [None] * number
            for i in range(number):
                triangles[i] = getobj_from_h5group("triangles{}".format(i))
            mass_centers = getobj_from_h5group("mass_centers")
            squared_gyration_radii = getobj_from_h5group("squared_gyration_radii")
            asphericities = getobj_from_h5group("asphericities")
            acylindricities = getobj_from_h5group("acylindricities")
            anisotropies = getobj_from_h5group("anisotropies")
            characteristic_radii = getobj_from_h5group("characteristic_radii")
            cyclic_area_indices = getobj_from_h5group("cyclic_area_indices")
        else:
            (
                timestamp,
                volumes,
                surface_areas,
                triangles,
                mass_centers,
                squared_gyration_radii,
                asphericities,
                acylindricities,
                anisotropies,
                characteristic_radii,
                cyclic_area_indices,
            ) = args[:11]

        if not isinstance(timestamp, datetime):
            timestamp = dateutil.parser.parse(str(timestamp))
        self.timestamp = timestamp
        self.volumes = np.asarray(volumes, dtype=np.float64)
        self.number = len(volumes)
        self.surface_areas = np.asarray(surface_areas, dtype=np.float64)
        self.triangles = [np.asarray(triangle, dtype=np.float64) for triangle in triangles]
        self.mass_centers = np.asarray(mass_centers, dtype=np.float64)
        self.squared_gyration_radii = np.asarray(squared_gyration_radii, dtype=np.float64)
        self.asphericities = np.asarray(asphericities, dtype=np.float64)
        self.acylindricities = np.asarray(acylindricities, dtype=np.float64)
        self.anisotropies = np.asarray(anisotropies, dtype=np.float64)
        self.characteristic_radii = np.asarray(characteristic_radii, dtype=np.float64)
        self.cyclic_area_indices = (
            np.asarray(cyclic_area_indices, dtype=np.int32) if cyclic_area_indices is not None else np.array([])
        )

    def tohdf(self, h5group, overwrite=True):
        """
        Write the data to a hdf5 Group.

        **Parameters:**
            `h5group` :
                the hdf5 group in which the data will be written

            `overwrite` :
                specifies if existing data should be overwritten
        """
        h5group.attrs["timestamp"] = str(self.timestamp)
        h5group.attrs["number"] = self.number
        writedataset(h5group, "volumes", self.volumes, overwrite)
        writedataset(h5group, "surface_areas", self.surface_areas, overwrite)
        for index, triangles in enumerate(self.triangles):
            writedataset(h5group, "triangles{}".format(index), np.array(triangles), overwrite)
        writedataset(h5group, "mass_centers", self.mass_centers, overwrite)
        writedataset(h5group, "squared_gyration_radii", self.squared_gyration_radii, overwrite)
        writedataset(h5group, "asphericities", self.asphericities, overwrite)
        writedataset(h5group, "acylindricities", self.acylindricities, overwrite)
        writedataset(h5group, "anisotropies", self.anisotropies, overwrite)
        writedataset(h5group, "characteristic_radii", self.characteristic_radii, overwrite)
        writedataset(h5group, "cyclic_area_indices", self.cyclic_area_indices, overwrite)

    def _export_gyration_parameters(self, fmt):
        mass_centers_file_name = fmt.format(property="centers_of_mass")
        squared_gyration_radii_file_name = fmt.format(property="squared_gyration_radii")
        asphericities_file_name = fmt.format(property="asphericities")
        acylindricities_file_name = fmt.format(property="acylindricities")
        anisotropies_file_name = fmt.format(property="anisotropies")
        characteristic_radii_file_name = fmt.format(property="characteristic_radii")

        mass_centers = self.getattr_normalized("mass_centers")
        squared_gyration_radii = self.getattr_normalized("squared_gyration_radii")
        asphericities = self.getattr_normalized("asphericities")
        acylindricities = self.getattr_normalized("acylindricities")
        anisotropies = self.getattr_normalized("anisotropies")
        characteristic_radii = self.getattr_normalized("characteristic_radii")

        export_filenames = []

        if mass_centers is not None:
            with open(mass_centers_file_name, "w") as outfile:
                for index, mass_center in enumerate(mass_centers, start=1):
                    outfile.write("{} {}\n".format(index, mass_center))
            export_filenames.append(mass_centers_file_name)
        if squared_gyration_radii is not None:
            with open(squared_gyration_radii_file_name, "w") as outfile:
                for index, squared_gyration_radius in enumerate(squared_gyration_radii, start=1):
                    outfile.write("{} {}\n".format(index, squared_gyration_radius))
            export_filenames.append(squared_gyration_radii_file_name)
        if asphericities is not None:
            with open(asphericities_file_name, "w") as outfile:
                for index, asphericity in enumerate(asphericities, start=1):
                    outfile.write("{} {}\n".format(index, asphericity))
            export_filenames.append(asphericities_file_name)
        if acylindricities is not None:
            with open(acylindricities_file_name, "w") as outfile:
                for index, acylindricity in enumerate(acylindricities, start=1):
                    outfile.write("{} {}\n".format(index, acylindricity))
            export_filenames.append(acylindricities_file_name)
        if anisotropies is not None:
            with open(anisotropies_file_name, "w") as outfile:
                for index, anisotropy in enumerate(anisotropies, start=1):
                    outfile.write("{} {}\n".format(index, anisotropy))
            export_filenames.append(anisotropies_file_name)
        if characteristic_radii is not None:
            with open(characteristic_radii_file_name, "w") as outfile:
                for index, characteristic_radius in enumerate(characteristic_radii, start=1):
                    outfile.write("{} {}\n".format(index, characteristic_radius))
            export_filenames.append(characteristic_radii_file_name)

        return export_filenames

    def getattr_normalized(self, attr):
        if hasattr(self, attr):
            value = getattr(self, attr)
            is_numpy_array = isinstance(value, np.ndarray)
            if (is_numpy_array and len(value.shape) > 0) or (not is_numpy_array and len(value) > 0):
                return value
        return None


class Domains(CavitiesBase):
    """
    Stores the calculated data about the domains.
    """

    def __init__(self, *args):
        """
        The constructor can be called in three ways:

        - ``Domains(timestamp, volumes, surface_areas, triangles, centers)`` :
            create the object using the given data

        - ``Domains(domaincalculation)`` :
            copy the data from this
            :class:`core.calculation.algorithm.DomainCalculation` object

        - ``Domains(hdf5group)`` :
            read the data from this hdf5 group
        """
        # Import this here to avoid cyclic imports
        from .calculation import algorithm

        if isinstance(args[0], h5py.Group):
            super().__init__(*args)
            h5group = args[0]
            centers = h5group["centers"]
        elif isinstance(args[0], algorithm.DomainCalculation):
            calculation = args[0]
            timestamp = datetime.now()
            volumes = calculation.domain_volumes
            surface_areas = calculation.domain_surface_areas
            triangles = calculation.domain_triangles
            centers = calculation.centers
            discretization = calculation.discretization
            mass_centers = calculation.mass_centers
            squared_gyration_radii = calculation.squared_gyration_radii
            asphericities = calculation.asphericities
            acylindricities = calculation.acylindricities
            anisotropies = calculation.anisotropies
            characteristic_radii = calculation.characteristic_radii
            cyclic_area_indices = calculation.cyclic_area_indices
            super().__init__(
                timestamp,
                volumes,
                surface_areas,
                triangles,
                mass_centers,
                squared_gyration_radii,
                asphericities,
                acylindricities,
                anisotropies,
                characteristic_radii,
                cyclic_area_indices,
            )
        else:
            super().__init__(*args)
            centers = args[4]

        self.centers = np.asarray(centers, dtype=np.int32)
        if "discretization" in locals():
            # TODO: get discretization also from other constructor calls!
            self.continuous_centers = np.array(
                [discretization.discrete_to_continuous(center) for center in centers],
                dtype=np.float64,
            )

    def tohdf(self, h5group, overwrite=True):
        """
        Write the data to a hdf5 Group.

        **Parameters:**
            `h5group` :
                the hdf5 group in which the data will be written

            `overwrite` :
                specifies if existing data should be overwritten
        """
        super(Domains, self).tohdf(h5group, overwrite)
        writedataset(h5group, "centers", self.centers, overwrite)

    def totxt(self, fmt):
        domain_center_file_name = fmt.format(property="centers")
        domain_surface_file_name = fmt.format(property="surface_areas")
        domain_volume_file_name = fmt.format(property="volumes")
        domain_surface_to_volume_ratio_file_name = fmt.format(property="surface_area_to_volume_ratios")

        export_filenames = [
            domain_center_file_name,
            domain_surface_file_name,
            domain_volume_file_name,
            domain_surface_to_volume_ratio_file_name,
        ]

        with open(domain_surface_file_name, "w") as outfile:
            for index, surface_area in enumerate(self.surface_areas, start=1):
                outfile.write("{} {}\n".format(index, surface_area))
        with open(domain_volume_file_name, "w") as outfile:
            for index, volume in enumerate(self.volumes, start=1):
                outfile.write("{} {}\n".format(index, volume))
        with open(domain_surface_to_volume_ratio_file_name, "w") as outfile:
            for index, t in enumerate(zip(self.volumes, self.surface_areas), start=1):
                volume, surface_area = t
                outfile.write("{} {}\n".format(index, surface_area / volume))
        continuous_centers = self.getattr_normalized("continuous_centers")
        if continuous_centers is not None:
            with open(domain_center_file_name, "w") as outfile:
                for index, continuous_center in enumerate(continuous_centers, start=1):
                    outfile.write(
                        "{} {} {} {}\n".format(
                            index,
                            continuous_center[0],
                            continuous_center[1],
                            continuous_center[2],
                        )
                    )
        else:
            raise ValueError(
                "No discretization present -> can only access discrete domain centers, no conversion to continuous "
                "space possible."
            )

        export_filenames.extend(self._export_gyration_parameters(fmt))

        return export_filenames

    def tosingletxt(self, fmt):
        fmt.write("Surface Areas:\n")
        for index, surface_area in enumerate(self.surface_areas, start=1):
            fmt.write("{} {}\n".format(index, surface_area))
        fmt.write("Volumes:\n")
        for index, volume in enumerate(self.volumes, start=1):
            fmt.write("{} {}\n".format(index, volume))
        fmt.write("Surface Area to Volume Ratios:\n")
        for index, t in enumerate(zip(self.volumes, self.surface_areas), start=1):
            volume, surface_area = t
            fmt.write("{} {}\n".format(index, surface_area / volume))
        continuous_centers = self.getattr_normalized("continuous_centers")
        if continuous_centers is not None:
            fmt.write("Centers:\n")
            for index, continuous_center in enumerate(continuous_centers, start=1):
                fmt.write(
                    "{} {} {} {}\n".format(
                        index,
                        continuous_center[0],
                        continuous_center[1],
                        continuous_center[2],
                    )
                )
        else:
            raise ValueError(
                "No discretization present -> can only access discrete domain centers, no conversion to continuous "
                "space possible."
            )


class Cavities(CavitiesBase):
    """
    Stores the calculated data about the cavities.
    """

    def __init__(self, *args):
        """
        The constructor can be called in three ways:

        - ``Cavities(timestamp, volumes, surface_areas, triangles, multicavities)`` :
            create the object using the given data

        - ``Cavities(cavitycalculation)`` :
            copy the data from this
            :class:`core.calculation.algorithm.CavityCalculation` object

        - ``Cavities(hdf5group)`` :
            read the data from this hdf5 group
        """
        # Import this here to avoid cyclic imports
        from .calculation import algorithm

        if isinstance(args[0], h5py.Group):
            super().__init__(*args)
            h5group = args[0]
            multicavities = [None] * self.number
            for i in range(self.number):
                multicavities[i] = h5group["multicavities{}".format(i)]
        elif isinstance(args[0], algorithm.CavityCalculation):
            calculation = args[0]
            timestamp = datetime.now()
            volumes = calculation.multicavity_volumes
            surface_areas = calculation.cavity_surface_areas
            triangles = calculation.cavity_triangles
            multicavities = calculation.multicavities
            mass_centers = calculation.mass_centers
            squared_gyration_radii = calculation.squared_gyration_radii
            asphericities = calculation.asphericities
            acylindricities = calculation.acylindricities
            anisotropies = calculation.anisotropies
            characteristic_radii = calculation.characteristic_radii
            cyclic_area_indices = calculation.cyclic_area_indices
            super().__init__(
                timestamp,
                volumes,
                surface_areas,
                triangles,
                mass_centers,
                squared_gyration_radii,
                asphericities,
                acylindricities,
                anisotropies,
                characteristic_radii,
                cyclic_area_indices,
            )
        else:
            super().__init__(*args)
            multicavities = args[4]

        self.multicavities = [None] * self.number
        for index, cavities in enumerate(multicavities):
            # cavities might be a 0-dimensional ndarray of python objects
            if isinstance(cavities, np.ndarray):
                cavities = cavities.tolist()
            self.multicavities[index] = np.array(list(cavities), dtype=np.int32)

    def tohdf(self, h5group, overwrite=True):
        """
        Write the data to a hdf5 Group.

        **Parameters:**
            `h5group` :
                the hdf5 group in which the data will be written

            `overwrite` :
                specifies if existing data should be overwritten
        """
        super(Cavities, self).tohdf(h5group, overwrite)
        for index, cavities in enumerate(self.multicavities):
            writedataset(h5group, "multicavities{}".format(index), cavities, overwrite)

    def totxt(self, fmt):
        cavity_surface_file_name = fmt.format(property="surface_areas")
        cavity_volume_file_name = fmt.format(property="volumes")
        cavity_domains_file_name = fmt.format(property="domain_indices")
        cavity_surface_to_volume_ratio_file_name = fmt.format(property="surface_area_to_volume_ratios")

        export_filenames = [
            cavity_surface_file_name,
            cavity_surface_file_name,
            cavity_volume_file_name,
            cavity_surface_to_volume_ratio_file_name,
        ]

        with open(cavity_domains_file_name, "w") as outfile:
            for index, multicavity in enumerate(self.multicavities, start=1):
                outfile.write("{}".format(index))
                for domain_index in multicavity:
                    outfile.write(" {}".format(domain_index + 1))
                outfile.write("\n")
        with open(cavity_surface_file_name, "w") as outfile:
            for index, surface_area in enumerate(self.surface_areas, start=1):
                outfile.write("{} {}\n".format(index, surface_area))
        with open(cavity_volume_file_name, "w") as outfile:
            for index, volume in enumerate(self.volumes, start=1):
                outfile.write("{} {}\n".format(index, volume))
        with open(cavity_surface_to_volume_ratio_file_name, "w") as outfile:
            for index, t in enumerate(zip(self.volumes, self.surface_areas), start=1):
                volume, surface_area = t
                outfile.write("{} {}\n".format(index, surface_area / volume))

        export_filenames.extend(self._export_gyration_parameters(fmt))

        return export_filenames

    def tosingletxt(self, fmt):
        fmt.write("Domain indices:\n")
        for index, multicavity in enumerate(self.multicavities, start=1):
            fmt.write("{}".format(index))
            for domain_index in multicavity:
                fmt.write(" {}".format(domain_index + 1))
            fmt.write("\n")
        fmt.write("Surface areas:\n")
        for index, surface_area in enumerate(self.surface_areas, start=1):
            fmt.write("{} {}\n".format(index, surface_area))
        fmt.write("Volumes:\n")
        for index, volume in enumerate(self.volumes, start=1):
            fmt.write("{} {}\n".format(index, volume))
        fmt.write("Surface area to volume ratios:\n")
        for index, t in enumerate(zip(self.volumes, self.surface_areas), start=1):
            volume, surface_area = t
            fmt.write("{} {}\n".format(index, surface_area / volume))


class Results(object):
    """
    Container class to store the calculated putput data together with its
    input data. This can be passed to the Visualization:

        - `filepath`
        - `frame`
        - `resolution`
        - `atoms`
        - `domains`
        - `surface_cavities`
        - `center_cavities`
    """

    def __init__(
        self,
        filepath,
        frame,
        resolution,
        atoms,
        domains,
        surface_cavities,
        center_cavities,
    ):
        """
        **Parameters:**
            `filepath` :
                path to the input file

            `frame` :
                frame number

            `resolution`:
                resolution of the discretization

            `atoms` :
                input data

            `domains` :
                the calculated domains or `None`

            `surface_cavities`
                the calculated surface-based cavities or `None`

            `center_cavities`
                the calculated center-based cavities or `None`
        """
        self.filepath = filepath
        self.frame = frame
        self.resolution = resolution
        self.atoms = atoms
        self.domains = domains
        self.surface_cavities = surface_cavities
        self.center_cavities = center_cavities

    def __str__(self):
        return self.description()

    def description(self, domain_volume=True, surface_cavity_volume=True, center_cavity_volume=True):
        s = "{}, frame {}, resolution {}".format(os.path.basename(self.filepath), self.frame + 1, self.resolution)
        if surface_cavity_volume and self.surface_cavities is not None and self.atoms.volume is not None:
            cavvolume = np.sum(self.surface_cavities.volumes)
            volpercent = 100 * cavvolume / self.atoms.volume.volume
            s += ", {:0.1f}% cavities (surface-based)".format(volpercent)
        if center_cavity_volume and self.center_cavities is not None and self.atoms.volume is not None:
            cavvolume = np.sum(self.center_cavities.volumes)
            volpercent = 100 * cavvolume / self.atoms.volume.volume
            s += ", {:0.1f}% cavities (center-based)".format(volpercent)
        if domain_volume and self.domains is not None and self.atoms.volume is not None:
            cavvolume = np.sum(self.domains.volumes)
            volpercent = 100 * cavvolume / self.atoms.volume.volume
            s += ", {:0.1f}% cavities (domains)".format(volpercent)
        return s

    # Properties to be compatible to the old CalculationResults
    @property
    def number_of_atoms(self):
        logger.warn("use of deprecated property")
        return self.atoms.number

    @property
    def atom_positions(self):
        logger.warn("use of deprecated property")
        return self.atoms.positions

    @property
    def atom_radii(self):
        logger.warn("use of deprecated property")
        return self.atoms.radii

    @property
    def number_of_domains(self):
        logger.warn("use of deprecated property")
        if self.domains is not None:
            return self.domains.number
        else:
            return None

    @property
    def domain_volumes(self):
        logger.warn("use of deprecated property")
        if self.domains is not None:
            return self.domains.volumes
        else:
            return None

    @property
    def domain_surface_areas(self):
        logger.warn("use of deprecated property")
        if self.domains is not None:
            return self.domains.surface_areas
        else:
            return None

    @property
    def domain_centers(self):
        logger.warn("use of deprecated property")
        if self.domains is not None:
            return self.domains.centers
        else:
            return None

    @property
    def domain_triangles(self):
        logger.warn("use of deprecated property")
        if self.domains is not None:
            return self.domains.triangles
        else:
            return None

    @property
    def number_of_multicavities(self):
        logger.warn("use of deprecated property")
        if self.surface_cavities is not None:
            return self.surface_cavities.number
        else:
            return None

    @property
    def multicavity_volumes(self):
        logger.warn("use of deprecated property")
        if self.surface_cavities is not None:
            return self.surface_cavities.volumes
        else:
            return None

    @property
    def multicavity_surface_areas(self):
        logger.warn("use of deprecated property")
        if self.surface_cavities is not None:
            return self.surface_cavities.surface_areas
        else:
            return None

    @property
    def multicavities(self):
        logger.warn("use of deprecated property")
        if self.surface_cavities is not None:
            return self.surface_cavities.multicavities
        else:
            return None

    @property
    def multicavity_triangles(self):
        logger.warn("use of deprecated property")
        if self.surface_cavities is not None:
            return self.surface_cavities.triangles
        else:
            return None

    @property
    def number_of_center_multicavities(self):
        logger.warn("use of deprecated property")
        if self.center_cavities is not None:
            return self.center_cavities.number
        else:
            return None

    @property
    def center_multicavity_volumes(self):
        logger.warn("use of deprecated property")
        if self.center_cavities is not None:
            return self.center_cavities.volumes
        else:
            return None

    @property
    def center_multicavity_surface_areas(self):
        logger.warn("use of deprecated property")
        if self.center_cavities is not None:
            return self.center_cavities.surface_areas
        else:
            return None

    @property
    def center_multicavities(self):
        logger.warn("use of deprecated property")
        if self.center_cavities is not None:
            return self.center_cavities.multicavities
        else:
            return None

    @property
    def center_multicavity_triangles(self):
        logger.warn("use of deprecated property")
        if self.center_cavities is not None:
            return self.center_cavities.triangles
        else:
            return None
