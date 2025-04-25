"""
This module provides classes to handle pyMolDyn related files.
"""

import os
import os.path
import sys
from itertools import repeat

import h5py

from .. import core
from ..util.logger import Logger
from . import data

try:
    import pybel

    raise ImportError
except ImportError:

    class pybel:
        """
        Dummy class representing a missing pybel module.
        """

        informats = {}


__all__ = ["File", "InputFile", "ResultFile", "XYZFile", "HDF5File"]

logger = Logger("core.file")
logger.setstream("default", sys.stdout, Logger.WARNING)

SEARCH_PATH = None


def get_abspath(path):
    """
    Return an absolute path for an input file. The difference to abspath from
    os.path is that this function uses SEARCH_PATH instead of the current
    working directory
    """
    global SEARCH_PATH
    if not os.path.isabs(path) and SEARCH_PATH is not None:
        # relative paths use the SEARCH_PATH instead of the current working
        # directory, as that is modified at startup. The SEARCH_PATH is set
        # to the initial cwd in startBatch and startGUI.
        path = os.path.join(SEARCH_PATH, path)
    return os.path.abspath(path)


class FileError(Exception):
    """
    Exception which will be raised by the subclasses of :class:`InputFile`
    if errors occur when handling the data inside the file.
    """

    def __init__(self, message, cause=None):
        super().__init__(message, cause)
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
        self.path = get_abspath(path)
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
                logger.info(str(e))
                return None
            if self._info.volume is None:
                self._info.volume_guessed = True
                minx, maxx = float("inf"), float("-inf")
                miny, maxy = float("inf"), float("-inf")
                minz, maxz = float("inf"), float("-inf")
                for frame in range(self._info.num_frames):
                    atoms = self.getatoms(frame)
                    minx = min(minx, atoms.positions[:, 0].min())
                    maxx = max(maxx, atoms.positions[:, 0].max())
                    miny = min(miny, atoms.positions[:, 1].min())
                    maxy = max(maxy, atoms.positions[:, 1].max())
                    minz = min(minz, atoms.positions[:, 2].min())
                    maxz = max(maxz, atoms.positions[:, 2].max())
                self._info.volumestr = "ORT %f %f %f" % (
                    maxx - minx,
                    maxy - miny,
                    maxz - minz,
                )
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
        super().__init__(path)
        f = open(self.path, "r")
        f.close()

    def readinfo(self):
        try:
            self._info.num_frames = 0
            with open(self.path.encode("utf-8"), "r") as f:
                try:
                    while True:
                        num_atoms = f.readline()
                        if not num_atoms:
                            break
                        num_atoms = int(num_atoms)
                        volume_info = f.readline()
                        for i in range(num_atoms):
                            f.readline()
                        self._info.num_frames += 1
                        if self._info.num_frames == 1:
                            self._info.volumestr = volume_info
                except StopIteration:
                    pass
            self.inforead = True
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot read file info.", e)

    def readatoms(self, frame):
        try:
            if self.info.num_frames <= frame:
                raise IndexError("Frame {} not found".format(frame))
            with open(self.path.encode("utf-8"), "r") as f:
                try:
                    # Skip the first frames
                    for i in range(frame):
                        num_atoms = f.readline()
                        if not num_atoms:
                            break
                        num_atoms = int(num_atoms)
                        f.readline()
                        for i in range(num_atoms):
                            f.readline()
                    # actually read the molecule
                    symbols = []
                    positions = []
                    num_atoms = f.readline()
                    if not num_atoms:
                        raise StopIteration
                    num_atoms = int(num_atoms)
                    f.readline()
                    for i in range(num_atoms):
                        line = f.readline()
                        if line.strip():
                            symbol, x, y, z = line.split()[:4]
                            position = (float(x), float(y), float(z))
                            symbols.append(symbol)
                            positions.append(position)
                except StopIteration:
                    raise IndexError("Frame {} not found".format(frame))
            return data.Atoms(positions, None, symbols, self.info.volume)
        except (IOError, IndexError):
            raise
        except Exception as e:
            raise FileError("Cannot read atom data.", e)


class BabelFile(InputFile):
    """
    Implementation on :class:`InputFile` for Open Babel 'xyz' files.
    """

    def __init__(self, path):
        super().__init__(path)
        # Check if the file exists
        f = open(self.path, "r")
        f.close()

    def readinfo(self):
        try:
            file_extension = os.path.splitext(self.path)[1][1:]
            mol_iter = pybel.readfile(file_extension.encode("utf8"), self.path.encode("utf8"))
            try:
                mol = next(mol_iter)
                self._info.volumestr = mol.title
                self._info.num_frames = 1
                for _ in mol_iter:
                    self._info.num_frames += 1
            except StopIteration:
                self._info.num_frames = 0
            self.inforead = True
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot read file info.", e)

    def readatoms(self, frame):
        try:
            if self.info.num_frames <= frame:
                raise IndexError("Frame {} not found".format(frame))

            file_extension = os.path.splitext(self.path)[1][1:]
            mol_iter = pybel.readfile(file_extension.encode("utf8"), self.path.encode("utf8"))

            # get the correct frame
            try:
                for _ in range(frame):
                    mol_iter.next()
                mol = mol_iter.next()
            except StopIteration:
                raise IndexError("Frame {} not found".format(frame))

            # read the atom information
            symbols = []
            positions = []
            for atom in mol.atoms:
                positions.append(tuple(float(c) for c in atom.coords))
                symbol = core.elements.symbols[atom.atomicnum]
                symbols.append(symbol)
            return data.Atoms(positions, None, symbols, self.info.volume)
        except (IOError, IndexError):
            raise
        except Exception as e:
            raise FileError("Cannot read atom data.", e)


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
        super().__init__(path)
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
            resinfo.domains[results.frame] = results.domains.timestamp
        if results.surface_cavities:
            resinfo.surface_cavities[results.frame] = results.surface_cavities.timestamp
        if results.center_cavities:
            resinfo.center_cavities[results.frame] = results.center_cavities.timestamp
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
        super().__init__(path, sourcefilepath)

    @classmethod
    def fromInputFile(cls, filepath, sourcefilepath):
        """
        Create a new :class:`HDF5File`. Copy atoms from an
        :class:`InputFile`. This is used to initially create a file
        to export results to.
        """
        inputfile = File.open(sourcefilepath)
        outputfile = cls(filepath, sourcefilepath)
        for frame in range(inputfile.info.num_frames):
            atoms = inputfile.getatoms(frame)
            results = data.Results(filepath, frame, 64, atoms, None, None, None)
            outputfile.writeresults(results)
        outputfile.readinfo()
        outputfile.writeinfo()
        return outputfile

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

        if not self.inforead and self._info.sourcefilepath is not None and os.path.isfile(self._info.sourcefilepath):
            try:
                sf = File.open(self._info.sourcefilepath)
                self._info.num_frames = sf.info.num_frames
                self._info.volumestr = sf.info.volumestr
                self.inforead = True
            except IOError:
                raise
            except Exception as e:
                raise FileError("Cannot read file info.", e)

        if not self.inforead:
            raise RuntimeError("No File Info in this file and the source file.")

    def writeinfo(self):
        try:
            with h5py.File(self.path, "a") as f:
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
                    results = data.Results(
                        filepath,
                        frame,
                        resolution,
                        atoms,
                        domains,
                        surface_cavities,
                        center_cavities,
                    )
        except IOError:
            raise
        except Exception as e:
            raise FileError("Cannot read results.", e)
        return results

    def writeresults(self, results, overwrite=True):
        # results valid? I think so!
        try:
            with h5py.File(self.path, "a") as f:
                group = f.require_group("atoms/frame{}".format(results.frame))
                # is it OK to never overwrite atoms? I think they should be saved when recalculating the file!
                results.atoms.tohdf(group, overwrite=overwrite)
                if (
                    results.domains is not None
                    or results.surface_cavities is not None
                    or results.center_cavities is not None
                ):
                    group = f.require_group("results/frame{}/resolution{}".format(results.frame, results.resolution))
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

    types = dict(
        list(zip(pybel.informats.keys(), repeat(BabelFile)))
        + [
            ("xyz", XYZFile),
            ("hdf5", HDF5File),
        ]
    )

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
        if not directory:
            directory = "."
        return [f for f in os.listdir(directory) if cls.exists(f)]

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
        return FileClass(filepath)

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
        filepath = get_abspath(filepath)
        name = os.path.basename(filepath)
        return os.path.isfile(filepath) and name.split(".")[-1] in cls.types
