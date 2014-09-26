# -*- coding: utf-8 -*-

__all__ = ["InputFileManager",
           "CalculationCache"]
import os
import pybel
import h5py
from datetime import datetime
from hashlib import sha256
from visualization.volumes import get_volume_from_string
from data import Atoms, CalculationInfo, Domains, Cavities, Results


class InputFile(object):
    def __init__(self, path):
        self.path = path
        self._num_frames = None
        self._volumestr = None
        self._volume = None
        self.inforead = False

    @property
    def filename(self):
        return os.path.basename(self.path)
    
    @property
    def volumestr(self):
        if not self.inforead:
            self.readinfo()
        return self._volumestr

    @property
    def num_frames(self):
        if not self.inforead:
            self.readinfo()
        return self._num_frames

    @property
    def volume(self):
        if not self.inforead:
            self.readinfo()
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
            self._volumestr = molecule.title
            self._num_frames = sum(1 for _ in f) + 1
            self._volume = get_volume_from_string(self._volumestr)
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
            if not self._num_frames is None:
                self._volumestr = molecule.title
                self._volume = get_volume_from_string(self._volumestr)
            for m in f:
                i += 1
                if i == frame:
                    molecule = m
                    if not self._num_frames is None:
                        break
            if self._num_frames is None:
                self._num_frames = i + 1
            if i < frame:
                raise IndexError("Frame not found")
        finally:
            f.close()
        return Atoms.frompybel(molecule, self.volume)


class ResultFile(InputFile):
    #TODO: specify when to overwrite
    def __init__(self, path, sourcefilepath=None):
        super(ResultFile, self).__init__(path)
        self.sourcefilepath = sourcefilepath
        self._calculated = None

    @property
    def calculated(self):
        if not self.inforead:
            self.readinfo()
        return self._calculated

    def calculatedframes(self, resolution):
        if not self.inforead:
            self.readinfo()
        return self.calculated[resolution]

    def getresults(self, frame, resolution):
        if not self.calculatedframes(resolution).domains[frame] is None:
            return self.readresults(frame, resolution)
        else:
            return None

    def addresults(self, results):
        self.writeresults(results)
        resinfo = self.calculated[results.resolution]
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
            self.readinfo()
            with h5py.File(self.path) as f:
                atoms = Atoms.fromhdf(f["atoms/frame{}".format(frame)])
        else:
            atoms = None
        return atoms


    def readinfo(self):
        #TODO: error handling
        with h5py.File(self.path) as f:
            if "num_frames" in f.attrs:
                self._num_frames = f.attrs["num_frames"]
                if self.sourcefilepath is None and "sourcefile" in f.attrs:
                    self.sourcefilepath = f.attrs["sourcefile"]
                self._volumestr = f.attrs["volume"]
                self._volume = get_volume_from_string(self._volumestr)
                self._calculated = CalculationInfo.fromhdf(f["info"])
                self.inforead = True
        if not self.inforead and os.path.isfile(self.sourcefilepath):
            fm = InputFileManager(os.path.dirname(self.sourcefilepath))
            sf = fm.getfile(os.path.basename(self.sourcefilepath))
            sf.readinfo()
            self._num_frames = sf.num_frames
            self._volumestr = sf.volumestr
            self._volume = sf.volume
            self._calculated = CalculationInfo(sf.num_frames)
            self.inforead = True


    def writeinfo(self):
        #TODO: error handling
        with h5py.File(self.path) as f:
            f.attrs["num_frames"] = self.num_frames
            f.attrs["volume"] = self.volumestr
            if not self.sourcefilepath is None:
                f.attrs["sourcefile"] = self.sourcefilepath
            self.calculated.tohdf(f.require_group("info"))

    def readresults(self, frame, resolution):
        #TODO: error handling
        if os.path.isfile(self.path):
            with h5py.File(self.path) as f:
                groupname = "results/frame{}/resolution{}".format(frame, resolution)
                if groupname in f:
                    group = f[groupname]
                    atoms = Atoms.fromhdf(f["atoms/frame{}".format(frame)])
                    domains = Domains.fromhdf(group["domains"])
                    if "surface_cavities" in group:
                        surface_cavities = Cavities.fromhdf(group["surface_cavities"])
                    else:
                        surface_cavities = None
                    if "center_cavities" in group:
                        center_cavities = Cavities.fromhdf(group["center_cavities"])
                    else:
                        center_cavities = None
                    results = Results(self.path, frame, resolution,
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
        self.types = dict()

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

    def getfile(self, filename):
        e = filename.split(".")[-1]
        if not e in self.types:
            raise ValueError("Unknown file format")
        FileClass = self.types[e]
        return FileClass(self.abspath(filename))

    def __getitem__(self, filename):
        return self.getfile(filename)


class InputFileManager(FileManager):
    def __init__(self, directory="."):
        super(InputFileManager, self).__init__(directory)
        self.types = {"xyz": XYZFile,
                      "hdf5": HDF5File}


class CalculationCache(FileManager):
    #TODO: inherit from FileManager or not?
    #TODO: replacement strategy
    def __init__(self, directory="."):
        super(CalculationCache, self).__init__(directory)
        self.types = {"hdf5": HDF5File}
        self.index = dict()
        self.indexfile = self.abspath("index.txt")
        self.buildindex()
        self.writeindex()

    def getfile(self, filename):
        sourcefilepath = os.path.abspath(filename)
        cachefilepath = self.abspath(self.cachefile(sourcefilepath))
        e = cachefilepath.split(".")[-1]
        if not e in self.types:
            raise ValueError("Unknown file format")
        FileClass = self.types[e]
        return FileClass(cachefilepath, sourcefilepath)

    def filelist(self):
        return list(self.index.keys())

    def __getitem__(self, filename):
        return self.getfile(filename)

    def cachefile(self, filepath):
        return sha256(filepath).hexdigest() + ".hdf5"

    def buildindex(self):
        for cachefile in self.filelist():
            cachepath = self.abspath(cachefile)
            with h5py.File(cachepath) as f:
                if "sourcefile" in f.attrs:
                    filepath = f.attrs["sourcefile"]
                    if cachefile == self.cachefile(filepath):
                        self.index[filepath] = cachefile

    def writeindex(self):
        with open(self.indexfile, "w") as f:
            for filepath, cachefile in sorted(self.index.iteritems(),
                                              key=lambda x: x[0]):
                print >>f, filepath + "; " + cachefile

    def addindex(self, filepath):
        filepath = os.path.abspath(filepath)
        if not filepath in self.index:
            self.index[filepath] = self.cachefile(filepath)
            self.writeindex()

    def getinfo(self, filepath):
        #TODO: error handling
        cf = self.getfile(filepath)
        info = cf.info
        return info

    def getresults(self, filepath, frame, resolution):
        #TODO: error handling
        cf = self.getfile(filepath)
        results = cf.getresults(frame, resolution)
        return results

    def addresults(self, results):
        #TODO: error handling
        cf = self.getfile(results.filepath)
        cf.addresults(results)
        self.addindex(results.filepath)

