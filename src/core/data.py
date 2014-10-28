# -*- coding: utf-8 -*-


__all__ = ["Atoms",
           "Domains",
           "Cavities",
           "Results",
           "FileInfo",
           "ResultInfo",
           "CalculatedFrames"]


import numpy as np
import sys
from datetime import datetime
import dateutil.parser
import h5py
import pybel
import volumes
import calculation.algorithm as algorithm
from config.configuration import config


def writedataset(h5group, name, data, overwrite=True):
    if name in h5group:
        if overwrite:
            del h5group[name]
        else:
            return False
    h5group[name] = data
    return True


class TimestampList(object):
    def __init__(self, *args):
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
        return any(map(lambda x: not x is None, self.timestamps))

    def tostrlist(self):
        return ["" if x is None else str(x) for x in self.timestamps]


class CalculatedFrames(object):
    def __init__(self, *args):
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
        return self.domains.hasdata() or \
               self.surface_cavities.hasdata() or \
               self.center_cavities.hasdata()

    def tohdf(self, h5group, overwrite=True):
        if self.hasdata():
            writedataset(h5group, "domains", self.domains.tostrlist(), overwrite)
            writedataset(h5group, "surface_cavities", self.surface_cavities.tostrlist(), overwrite)
            writedataset(h5group, "center_cavities", self.center_cavities.tostrlist(), overwrite)


class FileInfo(object):
    def __init__(self, num_frames=None, volumestr=None):
        self.num_frames = num_frames
        self.volumestr = volumestr
        self._volume = None

    @property
    def volume(self):
        if self._volume is None and not self.volumestr is None:
            self._volume = volumes.get_volume_from_string(self.volumestr)
        return self._volume


class ResultInfo(FileInfo):
    def __init__(self, *args):
        super(ResultInfo, self).__init__()
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
            for name, subgroup in h5group.iteritems():
                if not name.startswith("resolution"):
                    continue
                resolution = int(name[10:])
                self.calculatedframes[resolution] = CalculatedFrames(subgroup)

    def __getitem__(self, resolution):
        if not resolution in self.calculatedframes:
            self.calculatedframes[resolution] = CalculatedFrames(self.num_frames)
        return self.calculatedframes[resolution]

    def __contains__(self, resolution):
        return resolution in self.calculatedframes

    def tohdf(self, h5group, overwrite=True):
        h5group.attrs["num_frames"] = self.num_frames
        h5group.attrs["volume"] = self.volumestr
        if not self.sourcefilepath is None:
            h5group.attrs["sourcefile"] = self.sourcefilepath
        elif "sourcefile" in h5group.attrs:
            del h5group.attrs["sourcefile"]
        for resolution, info in self.calculatedframes.iteritems():
            if info.hasdata():
                subgroup = h5group.require_group("resolution{}".format(resolution))
                info.tohdf(subgroup, overwrite)


class Atoms(object):
    '''
    Instances of this class represent a list of atoms and their properties:
    - position
    - cavity cutoff radius
    
    To allow iteration in the order of their radii (from largest to smallest),
    the attributes self.sorted_radii and self.sorted_positions can be used.
    '''

    def __init__(self, *args):
        if isinstance(args[0], h5py.Group):
            h5group = args[0]
            positions = h5group["positions"]
            radii = h5group["radii"]
            if "volume" in h5group.attrs:
                volume = h5group.attrs["volume"]
            else:
                volume = h5group.parent.attrs["volume"]
            self.volume = volumes.get_volume_from_string(str(volume))
        elif isinstance(args[0], pybel.Molecule):
            molecule = args[0]
            if len(args) > 1:
                self.volume = args[1]
                if isinstance(self.volume, str):
                    self.volume = volumes.get_volume_from_string(self.volume)
                func = lambda a: self.volume.get_equivalent_point(a.coords)
            else:
                func = lambda atom: atom.coords
            positions = map(func, molecule)
            radii = None
        else:
            positions = args[0]
            radii = args[1]
            self.volume = args[2]
            if isinstance(self.volume, str):
                self.volume = volumes.get_volume_from_string(self.volume)

        self.positions = np.array(positions, dtype=np.float, copy=False)
        self.number = self.positions.shape[0]
        if not radii is None:
            self.radii = np.array(radii, dtype=np.float, copy=False)
        else:
            self.radii = np.ones((self.number), dtype=np.float) \
                         * config.Computation.atom_radius

        # old code: 
        #self.sorted_radii = sorted(list(set(self.radii)), reverse=True)
        #self.radii_as_indices = []
        #self.sorted_positions = []
        #for index, radius in enumerate(self.sorted_radii):
        #    for atom_index,atom_radius in enumerate(self.radii):
        #        if radius == atom_radius:
        #            self.radii_as_indices.append(index)
        #            self.sorted_positions.append(self.positions[atom_index])
        indices = np.argsort(-self.radii, kind="mergesort")
        self.sorted_positions = self.positions[indices]
        unique_radii, indices = np.unique(-self.radii, return_inverse=True)
        self.sorted_radii = -unique_radii
        self.radii_as_indices = np.sort(indices)

    def tohdf(self, h5group, overwrite=True):
        h5group.parent.attrs["volume"] = str(self.volume)
        writedataset(h5group, "positions", self.positions, overwrite)
        writedataset(h5group, "radii", self.radii, overwrite)


class CavitiesBase(object):
    def __init__(self, *args):
        if isinstance(args[0], h5py.Group):
            h5group = args[0]
            timestamp = dateutil.parser.parse(h5group.attrs["timestamp"])
            number = int(h5group.attrs["number"])
            volumes = h5group["volumes"]
            surface_areas = h5group["surface_areas"]
            triangles = [None] * number
            for i in range(number):
                triangles[i] = h5group["triangles{}".format(i)]
        else:
            timestamp, volumes, surface_areas, triangles = args[:4]

        if not isinstance(timestamp, datetime):
            timestamp = dateutil.parser.parse(str(timestamp))
        self.timestamp = timestamp
        self.volumes = np.array(volumes, dtype=np.float, copy=False)
        self.number = len(volumes)
        self.surface_areas = np.array(surface_areas, dtype=np.float, copy=False)
        self.triangles = map(lambda x: np.array(x, dtype=np.float,
                             copy=False), triangles)

    def tohdf(self, h5group, overwrite=True):
        h5group.attrs["timestamp"] = str(self.timestamp)
        h5group.attrs["number"] = self.number
        writedataset(h5group, "volumes", self.volumes, overwrite)
        writedataset(h5group, "surface_areas", self.surface_areas, overwrite)
        for index, triangles in enumerate(self.triangles):
            writedataset(h5group, "triangles{}".format(index), np.array(triangles), overwrite)


class Domains(CavitiesBase):
    def __init__(self, *args):
        if isinstance(args[0], h5py.Group):
            super(Domains, self).__init__(*args)
            h5group = args[0]
            centers = h5group["centers"]
        elif isinstance(args[0], algorithm.DomainCalculation):
            calculation = args[0]
            timestamp = datetime.now()
            volumes = calculation.domain_volumes
            surface_areas = calculation.domain_surface_areas
            triangles = calculation.domain_triangles
            centers = calculation.centers
            super(Domains, self).__init__(timestamp, volumes,
                                          surface_areas, triangles)
        else:
            super(Domains, self).__init__(*args)
            centers = args[4]

        self.centers = np.array(centers, dtype=np.float, copy=False)

    def tohdf(self, h5group, overwrite=True):
        super(Domains, self).tohdf(h5group, overwrite)
        writedataset(h5group, "centers", self.centers, overwrite)


class Cavities(CavitiesBase):
    def __init__(self, *args):
        if isinstance(args[0], h5py.Group):
            super(Cavities, self).__init__(*args)
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
            super(Cavities, self).__init__(timestamp, volumes,
                                          surface_areas, triangles)
        else:
            super(Cavities, self).__init__(*args)
            multicavities = args[4]

        self.multicavities = [None] * self.number
        for index, cavities in enumerate(multicavities):
            # cavities might be a 0-dimensional ndarray of python objects
            if isinstance(cavities, np.ndarray):
                cavities = cavities.tolist()
            self.multicavities[index] = np.array(list(cavities), dtype=np.int)

    def tohdf(self, h5group, overwrite=True):
        super(Cavities, self).tohdf(h5group, overwrite)
        for index, cavities in enumerate(self.multicavities):
            writedataset(h5group, "multicavities{}".format(index), cavities, overwrite)


class Results(object):
    def __init__(self, filepath, frame, resolution,
                 atoms, domains, surface_cavities, center_cavities):
        self.filepath = filepath
        self.frame = frame
        self.resolution = resolution
        self.atoms = atoms
        self.domains = domains
        self.surface_cavities = surface_cavities
        self.center_cavities = center_cavities

    # Properties to be compatible to the old CalculationResults
    @property
    def number_of_atoms(self):
        return self.atoms.number

    @property
    def atom_positions(self):
        return self.atoms.positions

    @property
    def atom_radii(self):
        return self.atoms.radii

    @property
    def number_of_domains(self):
        if not self.domains is None:
            return self.domains.number
        else:
            return None

    @property
    def domain_volumes(self):
        if not self.domains is None:
            return self.domains.volumes
        else:
            return None

    @property
    def domain_surface_areas(self):
        if not self.domains is None:
            return self.domains.surface_areas
        else:
            return None

    @property
    def domain_centers(self):
        if not self.domains is None:
            return self.domains.centers
        else:
            return None

    @property
    def domain_triangles(self):
        if not self.domains is None:
            return self.domains.triangles
        else:
            return None

    @property
    def number_of_multicavities(self):
        if not self.surface_cavities is None:
            return self.surface_cavities.number
        else:
            return None

    @property
    def multicavity_volumes(self):
        if not self.surface_cavities is None:
            return self.surface_cavities.volumes
        else:
            return None

    @property
    def multicavity_surface_areas(self):
        if not self.surface_cavities is None:
            return self.surface_cavities.surface_areas
        else:
            return None

    @property
    def multicavities(self):
        if not self.surface_cavities is None:
            return self.surface_cavities.multicavities
        else:
            return None

    @property
    def multicavity_triangles(self):
        if not self.surface_cavities is None:
            return self.surface_cavities.triangles
        else:
            return None

    @property
    def number_of_center_multicavities(self):
        if not self.center_cavities is None:
            return self.center_cavities.number
        else:
            return None

    @property
    def center_multicavity_volumes(self):
        if not self.center_cavities is None:
            return self.center_cavities.volumes
        else:
            return None

    @property
    def center_multicavity_surface_areas(self):
        if not self.center_cavities is None:
            return self.center_cavities.surface_areas
        else:
            return None

    @property
    def center_multicavities(self):
        if not self.center_cavities is None:
            return self.center_cavities.multicavities
        else:
            return None

    @property
    def center_multicavity_triangles(self):
        if not self.center_cavities is None:
            return self.center_cavities.triangles
        else:
            return None


