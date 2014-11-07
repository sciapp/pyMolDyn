# -*- coding: utf-8 -*-


__all__ = ["File",
           "InputFile",
           "ResultFile",
           "XYZFile",
           "HDF5File"]


import os
import pybel
import h5py
from datetime import datetime
import data


class InputFile(object):
    def __init__(self, path):
        self.path = path
        self._info = data.FileInfo()
        self.inforead = False

    @property
    def info(self):
        if not self.inforead:
            self.readinfo()
        return self._info

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
                raise IndexError("Frame {} not found".format(frame))
        finally:
            f.close()
        return data.Atoms(molecule, self.info.volume)


class ResultFile(InputFile):
    def __init__(self, path, sourcefilepath=None):
        super(ResultFile, self).__init__(path)
        self._info = data.ResultInfo()
        self._info.sourcefilepath = sourcefilepath

    def getresults(self, frame, resolution):
        if not self.info[resolution].domains[frame] is None:
            return self.readresults(frame, resolution)
        else:
            return None

    def addresults(self, results, overwrite=True):
        self.writeresults(results, overwrite=overwrite)
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

    def writeresults(self, results, overwrite=True):
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
                self.inforead = True
        if not self.inforead \
                and not self._info.sourcefilepath is None \
                and os.path.isfile(self._info.sourcefilepath):
            sf = File.open(self._info.sourcefilepath)
            self._info.num_frames = sf.info.num_frames
            self._info.volumestr = sf.info.volumestr
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
                    if not self.info.sourcefilepath is None:
                        filepath = self.info.sourcefilepath
                    else:
                        filepath = self.path
                    results = data.Results(filepath, frame, resolution,
                                   atoms, domains, surface_cavities,
                                   center_cavities)
        else:
            results = None
        return results

    def writeresults(self, results, overwrite=True):
        #TODO: error handling
        #TODO: results valid? 
        with h5py.File(self.path) as f:
            #TODO: only write when neccessary
            group = f.require_group("atoms/frame{}".format(results.frame))
            # TODO: is it OK to never overwrite atoms?
            results.atoms.tohdf(group, overwrite=False)
            group = f.require_group("results/frame{}/resolution{}".format(
                                    results.frame, results.resolution))
            subgroup = group.require_group("domains")
            results.domains.tohdf(subgroup, overwrite=overwrite)
            if not results.surface_cavities is None:
                subgroup = group.require_group("surface_cavities")
                results.surface_cavities.tohdf(subgroup, overwrite=overwrite)
            if not results.center_cavities is None:
                subgroup = group.require_group("center_cavities")
                results.center_cavities.tohdf(subgroup, overwrite=overwrite)


class File(object):
    types = {"xyz": XYZFile,
             "hdf5": HDF5File}

    @classmethod
    def listdir(cls, directory):
        return [f for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))
                   and f.split(".")[-1] in cls.types]

    @classmethod
    def open(cls, filepath):
        e = filepath.split(".")[-1]
        if not e in cls.types:
            raise ValueError("Unknown file format")
        FileClass = cls.types[e]
        return FileClass(os.path.abspath(filepath))

    @classmethod
    def exists(cls, filepath):
        name = os.path.basename(filepath)
        directory = os.path.dirname(filepath)
        return name in cls.filelist(directory)



