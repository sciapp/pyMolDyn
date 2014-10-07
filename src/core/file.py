# -*- coding: utf-8 -*-

#TODO: info class for InputFile?

__all__ = ["FileManager",
           "InputFile",
           "ResultFile",
           "XYZFile",
           "HDF5File"]


import os
import pybel
import h5py
from datetime import datetime
from visualization.volumes import get_volume_from_string
import data


class InputFile(object):
    def __init__(self, path):
        self.path = path
        self._info = data.FileInfo()
        self._volume = None
        self.inforead = False

    @property
    def info(self):
        if not self.inforead:
            self.readinfo()
        return self._info

    @property
    def volume(self):
        if self._volume is None:
            self._volume = get_volume_from_string(self.info.volumestr)
        return self._volume

    def getatoms(self, frame):
        return self.readatoms(frame)

    def readinfo(self):
        raise NotImplementedError

    def readatoms(self, frame):
        raise NotImplementedError


class XYZFile(InputFile):
    def __init__(self, path):
        super(XYZFile, self).__init__(path)

    def readinfo(self):
        try:
            f = pybel.readfile("xyz", self.path.encode("ascii"))
            molecule = f.next()
            self._info.volumestr = molecule.title
            self._info.num_frames = sum(1 for _ in f) + 1
            self._volume = get_volume_from_string(self._info.volumestr)
            self.inforead = True
        except:
            raise ValueError("Cannot read file info")
        finally:
            f.close()

    def readatoms(self, frame):
        try:
            f = pybel.readfile("xyz", self.path.encode("ascii"))
            i = 0
            molecule = f.next()
            if not self.inforead:
                self._info.volumestr = molecule.title
                self._volume = get_volume_from_string(self._info.volumestr)
            for m in f:
                i += 1
                if i == frame:
                    molecule = m
                    if self.inforead:
                        break
            if not self.inforead:
                self._info.num_frames = i + 1
                self.inforead = True
            if i < frame:
                raise IndexError("Frame not found")
        finally:
            f.close()
        return data.Atoms(molecule, self.volume)


class ResultFile(InputFile):
    #TODO: specify when to overwrite
    def __init__(self, path, sourcefilepath=None):
        super(ResultFile, self).__init__(path)
        self._info = data.ResultInfo()
        self._info.sourcefilepath = sourcefilepath

    def getresults(self, frame, resolution):
        if not self.info[resolution].domains[frame] is None:
            return self.readresults(frame, resolution)
        else:
            return None

    def addresults(self, results):
        self.writeresults(results)
        resinfo = self.info[results.resolution]
        if results.domains:
            resinfo.domains[results.frame] \
                = results.domains.timestamp
        if results.surface_cavities:
            resinfo.surface_cavities[results.frame] \
                = results.surface_cavities.timestamp
        if results.center_cavities:
            resinfo.center_cavities[results.frame] \
                = results.center_cavities.timestamp
        self.writeinfo()

    def writeinfo(self):
        raise NotImplementedError

    def readresults(self, frame, resolution):
        raise NotImplementedError

    def writeresults(self, results):
        raise NotImplementedError


class HDF5File(ResultFile):
    def __init__(self, path, sourcefilepath=None):
        super(HDF5File, self).__init__(path, sourcefilepath)

    def readatoms(self, frame):
        #TODO: error handling
        if os.path.isfile(self.path):
            with h5py.File(self.path) as f:
                atoms = data.Atoms(f["atoms/frame{}".format(frame)])
        else:
            atoms = None
        return atoms

    def readinfo(self):
        #TODO: error handling
        with h5py.File(self.path) as f:
            if "info" in f:
                info = data.ResultInfo(f["info"])
                if not self._info.sourcefilepath is None:
                    info.sourcefilepath = self._info.sourcefilepath
                self._info = info
                self._volume = get_volume_from_string(self._info.volumestr)
                self.inforead = True
        if not self.inforead \
                and not self._info.sourcefilepath is None \
                and os.path.isfile(self._info.sourcefilepath):
            fm = FileManager(os.path.dirname(self._info.sourcefilepath))
            sf = fm.getfile(os.path.basename(self._info.sourcefilepath))
            self._info.num_frames = sf.info.num_frames
            self._info.volumestr = sf.info.volumestr
            self._volume = sf.volume
            self.inforead = True


    def writeinfo(self):
        #TODO: error handling
        with h5py.File(self.path) as f:
            h5group = f.require_group("info")
            self.info.tohdf(h5group)

    def readresults(self, frame, resolution):
        #TODO: error handling
        if os.path.isfile(self.path):
            with h5py.File(self.path) as f:
                groupname = "results/frame{}/resolution{}".format(frame, resolution)
                if groupname in f:
                    group = f[groupname]
                    atoms = data.Atoms(f["atoms/frame{}".format(frame)])
                    domains = data.Domains(group["domains"])
                    if "surface_cavities" in group:
                        surface_cavities = data.Cavities(group["surface_cavities"])
                    else:
                        surface_cavities = None
                    if "center_cavities" in group:
                        center_cavities = data.Cavities(group["center_cavities"])
                    else:
                        center_cavities = None
                    results = data.Results(self.path, frame, resolution,
                                   atoms, domains, surface_cavities,
                                   center_cavities)
        else:
            results = None
        return results

    def writeresults(self, results):
        #TODO: error handling
        #TODO: results valid? 
        with h5py.File(self.path) as f:
            #TODO: only write when neccessary? overwrite parameter
            group = f.require_group("atoms/frame{}".format(results.frame))
            results.atoms.tohdf(group)
            group = f.require_group("results/frame{}/resolution{}".format(
                                    results.frame, results.resolution))
            subgroup = group.require_group("domains")
            results.domains.tohdf(subgroup)
            if not results.surface_cavities is None:
                subgroup = group.require_group("surface_cavities")
                results.surface_cavities.tohdf(subgroup)
            if not results.center_cavities is None:
                subgroup = group.require_group("center_cavities")
                results.center_cavities.tohdf(subgroup)


class FileManager(object):
    #TODO: detectfiletype method that can be overridden
    def __init__(self, directory="."):
        self._directory = os.path.abspath(directory)
        self.types = {"xyz": XYZFile,
                      "hdf5": HDF5File}

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        if not os.path.isdir(value):
            raise ValueError("Invalid directory")
        self._directory = os.path.abspath(value)

    def abspath(self, filename):
        return os.path.abspath(os.path.join(self.directory, filename))

    def filelist(self):
        #TODO: unfiltered list?
        return [f for f in os.listdir(self.directory)
                if os.path.isfile(self.abspath(f))
                   and f.split(".")[-1] in self.types]

    def __getitem__(self, filename):
        e = filename.split(".")[-1]
        if not e in self.types:
            raise ValueError("Unknown file format")
        FileClass = self.types[e]
        return FileClass(self.abspath(filename))

    def __contains__(self, filename):
        return filename in self.filelist()


