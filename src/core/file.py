# -*- coding: utf-8 -*-
"""
This module provides classes to handle pyMolDyn related files.
"""


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
    """
    Abstract access to a file that contains atom data for one or more frames.
    Subclasses need to implement the `readinfo` and `readatoms` methods.
    """

    def __init__(self, path):
        """
        **Parameters:**
            `path` :
                absolute path to the file
        """
        self.path = path
        self._info = data.FileInfo()
        self.inforead = False

    @property
    def info(self):
        """
        `FileInfo` object that contains metadata
        """
        if not self.inforead:
            self.readinfo()
        return self._info

    def getatoms(self, frame):
        """
        Read atom data for a specified frame.

        **Parameters:**
            `frame` :
                the frame number

        **Returns:**
            an `Atoms` object
        """
        return self.readatoms(frame)

    def readinfo(self):
        raise NotImplementedError

    def readatoms(self, frame):
        raise NotImplementedError


class XYZFile(InputFile):
    """
    Implementation on `InputFile` for Open Babel 'xyz' files.
    """
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
    """
    Abstract access to a file that contains both input data (atoms) and
    calculated results.
    The `info` attribute has the type `ResultInfo`.
    In addition the `readinfo` and `readatoms` methods, subclasses must
    implement `writeinfo`, `readresults` and `writeresults`.
    """

    def __init__(self, path, sourcefilepath=None):
        """
        **Parameters:**
            `path` :
                absolute path to the file

            `sourcefilepath` :
                path to the file where the input data originally came from
        """
        super(ResultFile, self).__init__(path)
        self._info = data.ResultInfo()
        self._info.sourcefilepath = sourcefilepath

    def getresults(self, frame, resolution):
        """
        Read results from this file.

        **Parameters:**
            `frame` :
                the frame number
            `resolution` :
                the resolution of the calculation

        **Returns:**
            A `Results` object, if the file contains results for the
            specified parameters. Otherwise it return `None`.
        """
        if not self.info[resolution].domains[frame] is None:
            return self.readresults(frame, resolution)
        else:
            return None

    def addresults(self, results, overwrite=True):
        """
        Write calculated results into this file.

        **Parameters:**
            `results` :
                the results to write
            `overwrite` :
                specifies if existing results should be overwritten
        """
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
    """
    Implementation on `ResultFile` for 'hdf5' files.
    """
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
    """
    Provides static methods for easy access to files and directories.
    The class attribute `types` associates filename endings with
    classes to handle them.
    """
    types = {"xyz": XYZFile,
             "hdf5": HDF5File}

    @classmethod
    def listdir(cls, directory):
        """
        List all (possible) pyMolDyn files in the directory.

        **Parameters:**
            `directory` :
                path to a directory

        **Returns:**
            A list of filenames which can be opened.
        """
        return [f for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))
                   and f.split(".")[-1] in cls.types]

    @classmethod
    def open(cls, filepath):
        """
        Get the associated `InputFile` class for the given file.

        **Parameters:**
            `filepath` :
                path to the file

        **Returns:**
            An object of a subclass of `InputFile`.
        """
        e = filepath.split(".")[-1]
        if not e in cls.types:
            raise ValueError("Unknown file format")
        FileClass = cls.types[e]
        return FileClass(os.path.abspath(filepath))

    @classmethod
    def exists(cls, filepath):
        """
        Check if a file exists and if it can be opened.

        **Parameters:**
            `filepath` :
                path to the file

        **Returns:**
            `True` if the file exists and there is a subclass of `InputFile`
            associated with the filename ending.
        """
        name = os.path.basename(filepath)
        directory = os.path.dirname(filepath)
        return name in cls.filelist(directory)



