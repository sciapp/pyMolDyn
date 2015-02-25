# -*- coding: utf-8 -*-
"""
This module provides classes to handle pyMolDyn related files.
"""

import os
import pybel
import h5py
from datetime import datetime
import data
import sys
from util.logger import Logger

__all__ = ["File",
           "InputFile",
           "ResultFile",
           "XYZFile",
           "HDF5File"]

logger = Logger("core.file")
logger.setstream("default", sys.stdout, Logger.WARNING)


class FileError(Exception):
    """
    Exception which will be raised by the subclasses of :class:`InputFile`
    if errors occur when handling the data inside the file.
    """

    def __init__(self, message, cause=None):
        super(FileError, self).__init__(message, cause)
        self.message = message
        self.cause = cause

    def __str__(self):
        if self.cause is None:
            f = "{}: {}"
        else:
            f = "{}: {} (caused by: {})"
        return f.format(self.__class__.__name__, self.message, str(self.cause))


class InputFile(object):
    """
    Abstract access to a file that contains atom data for one or more frames.
    Subclasses need to implement the ``readinfo()`` and ``readatoms(frame)`` methods.
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
        :class:`core.data.FileInfo` object that contains metadata
        """
        if not self.inforead:
            try:
                self.readinfo()
            except IOError as e:
                # logger.error(str(e))
                pass
        return self._info

    def getatoms(self, frame):
        """
        Read atom data for a specified frame.

        **Parameters:**
            `frame` :
                the frame number

        **Returns:**
            an :class:`core.data.Atoms` object

        **Raises:**
            - :class:`IndexError`: if the frame is not in the file
            - :class:`FileError`: if there are problems with the data in the file
            - :class:`IOError`: if the file cannot be read
        """
        return self.readatoms(frame)

    def readinfo(self):
        raise NotImplementedError

    def readatoms(self, frame):
        raise NotImplementedError


class XYZFile(InputFile):
    """
    Implementation on :class:`InputFile` for Open Babel 'xyz' files.
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
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot read file info.", e)
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
        except (IOError, IndexError):
            raise
        except Exception as e:
            raise FileError("Cannot read atom data.", e)
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

        **Raises:**
            - :class:`FileError`: if there are problems with the data in the file
            - :class:`IOError`: if the file cannot be read
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

        **Raises:**
            - :class:`FileError`: if there are problems with the data in the file
            - :class:`IOError`: if the file cannot be read or written
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
    Implementation on :class:`ResultFile` for 'hdf5' files.
    """
    def __init__(self, path, sourcefilepath=None):
        super(HDF5File, self).__init__(path, sourcefilepath)

    def readatoms(self, frame):
        atoms = None
        if not os.path.isfile(self.path):
            raise IOError(2, "File not found.")
        try:
            with h5py.File(self.path) as f:
                group = "atoms/frame{}".format(frame)
                if group not in f:
                    raise IndexError("Frame {} not found".format(frame))
                atoms = data.Atoms(f[group])
        except (IOError, IndexError):
            raise
        except Exception as e:
            raise FileError("Cannot read atom data.", e)
        return atoms

    def readinfo(self):
        if not os.path.isfile(self.path):
            raise IOError(2, "File not found.")
        try:
            with h5py.File(self.path) as f:
                if "info" in f:
                    info = data.ResultInfo(f["info"])
                    if self._info.sourcefilepath is not None:
                        info.sourcefilepath = self._info.sourcefilepath
                    self._info = info
                    self.inforead = True
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot read file info.", e)

        if not self.inforead \
                and self._info.sourcefilepath is not None \
                and os.path.isfile(self._info.sourcefilepath):
            try:
                sf = File.open(self._info.sourcefilepath)
                self._info.num_frames = sf.info.num_frames
                self._info.volumestr = sf.info.volumestr
                self.inforead = True
            except IOError:
                raise
            except Exception as e:
                raise FileError("Cannot read file info.", e)

    def writeinfo(self):
        try:
            with h5py.File(self.path) as f:
                h5group = f.require_group("info")
                self.info.tohdf(h5group)
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot write file info.", e)

    def readresults(self, frame, resolution):
        if not os.path.isfile(self.path):
            raise IOError(2, "File not found.")
        try:
            results = None
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
                    if self.info.sourcefilepath is not None:
                        filepath = self.info.sourcefilepath
                    else:
                        filepath = self.path
                    results = data.Results(filepath, frame, resolution,
                                           atoms, domains, surface_cavities,
                                           center_cavities)
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot read results.", e)
        return results

    def writeresults(self, results, overwrite=True):
        # TODO: results valid?
        try:
            with h5py.File(self.path) as f:
                group = f.require_group("atoms/frame{}".format(results.frame))
                # TODO: is it OK to never overwrite atoms?
                results.atoms.tohdf(group, overwrite=False)
                group = f.require_group("results/frame{}/resolution{}".format(
                                        results.frame, results.resolution))
                if results.domains is not None:
                    subgroup = group.require_group("domains")
                    results.domains.tohdf(subgroup, overwrite=overwrite)
                if results.surface_cavities is not None:
                    subgroup = group.require_group("surface_cavities")
                    results.surface_cavities.tohdf(subgroup, overwrite=overwrite)
                if results.center_cavities is not None:
                    subgroup = group.require_group("center_cavities")
                    results.center_cavities.tohdf(subgroup, overwrite=overwrite)
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot write results.", e)


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
        Get the associated :class:`InputFile` object for the given file.

        **Parameters:**
            `filepath` :
                path to the file

        **Returns:**
            An object of a subclass of :class:`InputFile`.

        **Raises:**
            :class:`ValueError` if the file format is unknown.
        """
        e = filepath.split(".")[-1]
        if e not in cls.types:
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
            `True` if the file exists and there is a subclass of :class:`InputFile`
            associated with the filename ending.
        """
        name = os.path.basename(filepath)
        directory = os.path.dirname(filepath)
        return name in cls.filelist(directory)
