# -*- coding: utf-8 -*-
"""
With the classes in this module the rather complicated calculation process
can be started with a simple method call.
Additionally, results are stored in a cache and can be reused later.
"""

import os
import core.data as data
import core.file
from core.file import File
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation, FakeDomainCalculation
from discretization import DiscretizationCache, AtomDiscretization
import util.message as message
from hashlib import sha256
from config.configuration import config
from util.logger import Logger
import sys
import numpy as np
import core.bonds

__all__ = ["Calculation",
           "CalculationCache",
           "CalculationSettings",
           "calculated",
           "count_frames",
           "calculated_frames",
           "calculate_cavities",
           "getresults",
           "delete_center_cavity_information",
           "timestamp",
           "calculate"]

logger = Logger("core.calculation")
logger.setstream("default", sys.stdout, Logger.WARNING)


class CalculationSettings(object):
    """
    Structure to store the parameters for one or more calculation.

    **Attributes:**
        `datasets` :
            Dictionary, which contains filenames (Strings) as keys.
            Each value is a list of Integers, which contains the frames.
            The value ``[-1]`` means 'all frames'.
        `resolution` :
            resolution parameter for the discretization
        `domains` :
            calculate cavitiy domains
        `surface_cavities` :
            calculate surface-based cavities
        `center_cavities` :
            calculate center-based cavities
        `recalculate` :
            results will be calculated even if cached results exists
        `exporthdf` :
            ``True`` if the results should be written into a hdf5 file.
            If ``False``, they are stored in the cache.
        `exporttext` :
            ``True`` if the results should be written into text files.
        `exportdir` :
            Directory for the exports. Only used, when at least one of
            the export parameters is ``True``. If `exportdir` is ``None``,
            the directory of the input file is used.
        `bonds` :
            calculate bonds
        `dihedral_angles` :
            calculate dihedral angles
    """

    def __init__(self,
                 datasets,
                 resolution=config.Computation.std_resolution,
                 domains=False,
                 surface_cavities=False,
                 center_cavities=False,
                 recalculate=False,
                 exporthdf5=False,
                 exporttext=False,
                 exportdir=None):
        """
        """
        self.datasets = datasets
        self.resolution = resolution
        self.domains = domains
        self.surface_cavities = surface_cavities
        self.center_cavities = center_cavities
        self.recalculate = recalculate
        self.exporthdf5 = exporthdf5
        self.exporttext = exporttext
        self.exportdir = exportdir
        self.bonds = False
        self.dihedral_angles = False

    def copy(self):
        """
        **Returns:**
            A deep copy of this object.
        """
        datasets = dict()
        for filename, frames in self.datasets.iteritems():
            datasets[filename] = [f for f in frames]
        dup = self.__class__(datasets, self.resolution)
        dup.domains = self.domains
        dup.surface_cavities = self.surface_cavities
        dup.center_cavities = self.center_cavities
        dup.recalculate = self.recalculate
        dup.exporthdf5 = self.exporthdf5
        dup.exporttext = self.exporttext
        dup.exportdir = self.exportdir
        dup.bonds = self.bonds
        dup.dihedral_angles = self.dihedral_angles
        return dup


class Calculation(object):
    """
    This class provides the methods to start calculations.
    Optionally, results can be read from a cache.
    """

    def __init__(self, cachedir=None):
        """
        **Parameters:**
            `cachedir` :
                directory to store the cache files in; if none is given,
                a default one is used
        """
        if cachedir is None:
            cachedir = os.path.expanduser(config.Path.cache_dir)
        self.cachedir = cachedir
        self.cache = CalculationCache(cachedir)

    def calculatedframes(self, filepath, resolution, surface=False, center=False):
        """
        Query the cache if it contains results for the given parameters.

        **Parameters:**
            `filepath` :
                absolute path of the input file
            `resolution` :
                resolution of the used discretization
            `surface` :
                query calculation results for surface-based cavities
            `center` :
                query calculation results for center-based cavities

        **Returns:**
            A :class:`core.data.TimestampList` containing the dates
            of the calculation or `None`.
        """
        info = None
        inputfile = File.open(filepath)
        # TODO: error handling
        if isinstance(inputfile, core.file.ResultFile):
            info = inputfile.info
        else:
            if filepath in self.cache:
                cf = self.cache[filepath]
                info = cf.info
        if info is not None:
            if surface:
                return info[resolution].surface_cavities
            elif center:
                return info[resolution].center_cavities
            else:
                return info[resolution].domains
        else:
            return data.TimestampList(inputfile.info.num_frames)

    def timestamp(self, filepath, frame, resolution, surface=False, center=False):
        """
        Query the cache if it contains results for the given parameters.

        **Returns:**
            The date and time when cached results were calculated
            on `None` if they do not exist.
        """
        calc = self.calculatedframes(filepath, resolution, surface, center)
        return calc[frame]

    def iscalculated(self, filepath, frame, resolution, surface=False, center=False):
        """
        **Returns:**
            If the cache contains results for the given parameters.
        """
        return not self.timestamp(filepath, frame,
                                  resolution, surface, center) is None

    def getresults(self, filepath, frame, resolution=None, surface=False, center=False):
        """
        Get cached results for the given parameters.

        **Parameters:**
            `filepath` :
                absolute path of the input file
            `frame` :
                the frame number
            `resolution` :
                resolution of the used discretization
            `surface` :
                query calculation results for surface-based cavities
            `center` :
                query calculation results for center-based cavities

        **Returns:**
            A :class:`core.data.Results` object if cached results exist,
            else `None`
        """
        inputfile = File.open(filepath)
        # TODO: error handling
        resultfile = None
        results = None
        if isinstance(inputfile, core.file.ResultFile):
            resultfile = inputfile
        elif filepath in self.cache:
            resultfile = self.cache[filepath]
        if resultfile is not None:
            if resolution is None:
                resolutions = sorted(resultfile.info.resolutions())[::-1]
                resolution = 64
                for res in resolutions:
                    if resultfile.info[res].domains[frame] is not None:
                        resolution = res
                        break
            results = resultfile.getresults(frame, resolution)
        if results is None:
            if resolution is None:
                resolution = 64
            results = data.Results(filepath, frame, resolution, inputfile.getatoms(frame), None, None, None)
        return results

    def calculateframe(self, filepath, frame, resolution, domains=False, surface=False, center=False, atoms=None, recalculate=False, last_frame=True):
        """
        Get results for the given parameters. They are either loaded from the
        cache or calculated.

        **Parameters:**
            `filepath` :
                absolute path of the input file
            `frame` :
                the frame number
            `resolution` :
                resolution of the used discretization
            `domains` :
                calculate cavitiy domains
            `surface` :
                calculate surface-based cavities
            `center` :
                calculate center-based cavities
            `recalculate` :
                results will be calculated even if cached results exists

        **Returns:**
            A :class:`core.data.Results` object.
        """
        message.progress(0)
        inputfile = File.open(filepath)
        # TODO: error handling
        if isinstance(inputfile, core.file.ResultFile):
            resultfile = inputfile
        else:
            resultfile = self.cache[filepath]
        try:
            results = resultfile.getresults(frame, resolution)
        except Exception as e:
            logger.debug("error in resultfile.getresults: {}".format(e))
            results = None

        if atoms is None:
            atoms = inputfile.getatoms(frame)
        volume = atoms.volume
        if results is None:
            results = data.Results(filepath, frame, resolution, atoms, None, None, None)

        if recalculate:
            results.domains = None
            results.surface_cavities = None
            results.center_cavities = None

        if not ((domains and results.domains is None)
                or (surface and results.surface_cavities is None)
                or (center and results.center_cavities is None)):
            message.print_message("Reusing results")
        else:
            cachepath = os.path.join(self.cachedir, 'discretization_cache.hdf5')
            discretization_cache = DiscretizationCache(cachepath)
            discretization = discretization_cache.get_discretization(volume, resolution)
            atom_discretization = AtomDiscretization(atoms, discretization)
            message.progress(10)
            if (domains and results.domains is None) \
                    or (surface and results.surface_cavities is None):
                # CavityCalculation depends on DomainCalculation
                message.print_message("Calculating domains")
                domain_calculation = DomainCalculation(discretization, atom_discretization)
            if results.domains is None:
                results.domains = data.Domains(domain_calculation)
            message.progress(40)

            if surface and results.surface_cavities is None:
                message.print_message("Calculating surface-based cavities")
                cavity_calculation = CavityCalculation(domain_calculation, use_surface_points=True)
                results.surface_cavities = data.Cavities(cavity_calculation)
            message.progress(70)

            if center and results.center_cavities is None:
                message.print_message("Calculating center-based cavities")
                domain_calculation = FakeDomainCalculation(discretization, atom_discretization, results)
                cavity_calculation = CavityCalculation(domain_calculation, use_surface_points=False)
                results.center_cavities = data.Cavities(cavity_calculation)
            resultfile.addresults(results, overwrite=recalculate)

        message.progress(100)
        message.print_message("Calculation finished")
        if last_frame:
            message.finish()
        return results

    def calculate(self, calcsettings):
        """
        Calculate (or load from the cache) all results for the given settings.

        **Parameters:**
            `calcsettings` :
                :class:`CalculationSettings` object

        **Returns:**
            A list of list of :class:`core.data.Results` objects. The outer list contains
            an entry for each entry in `calcsettings.filenames`; the inner
            list has a `Results` entry for each frame specified in
            `calcsettings.frames`.
        """
        allresults = []
        for filename, frames in calcsettings.datasets.iteritems():
            filepath = os.path.abspath(filename)
            fileprefix = os.path.basename(filename).rsplit(".", 1)[0]
            if calcsettings.exportdir is not None:
                exportdir = os.path.abspath(calcsettings.exportdir)
                # replace asterisks with directories
                dirlist = os.path.dirname(filepath).split("/")
                while "*" in exportdir:
                    i = exportdir.rindex("*")
                    exportdir = os.path.join(exportdir[:i], dirlist.pop() + exportdir[i+1:])
                if (calcsettings.exporthdf5 or calcsettings.exporttext) \
                        and not os.path.exists(exportdir):
                    os.makedirs(exportdir)
            else:
                exportdir = os.path.dirname(filepath)
            if calcsettings.exporthdf5:
                efpath = os.path.join(exportdir, fileprefix + ".hdf5")
                efpath = os.path.abspath(efpath)
                # copy atoms into HDF5 file
                exportfile = core.file.HDF5File.fromInputFile(efpath, filepath)
                # use HDF5 file as input
                filepath = efpath

            fileresults = []
            if frames[0] == -1:
                inputfile = File.open(filepath)
                frames = range(inputfile.info.num_frames)
            last_frame = False
            for frame in frames:
                # calculate single frame
                if frame is frames[-1]:
                    last_frame = True
                frameresult = self.calculateframe(
                    filepath,
                    frame,
                    calcsettings.resolution,
                    domains=calcsettings.domains,
                    surface=calcsettings.surface_cavities,
                    center=calcsettings.center_cavities,
                    recalculate=calcsettings.recalculate,
                    last_frame=last_frame)
                # export to text file
                if calcsettings.exporttext:
                    fmt = os.path.join(exportdir, fileprefix) + "-{property}-{frame:06d}.txt"
                    if frameresult.atoms is not None:
                        frameresult.atoms.totxt(fmt.format(property='{property}', frame=frame+1))
                    if frameresult.domains is not None:
                        frameresult.domains.totxt(fmt.format(property='domain_{property}', frame=frame+1))
                    if frameresult.surface_cavities is not None:
                        frameresult.surface_cavities.totxt(fmt.format(property='surface_cavities_{property}', frame=frame+1))
                    if frameresult.center_cavities is not None:
                        frameresult.center_cavities.totxt(fmt.format(property='center_cavities_{property}', frame=frame+1))
                    # TODO: try/except
                # gather results
                fileresults.append(frameresult)
            allresults.append(fileresults)
        return allresults


class CalculationCache(object):
    """
    Stores calculation results. Associates the input file with a
    'hdf5' file containing the calculated results.
    This is realized with a single directory containing hdf5 files that
    are named after the SHA256 value of the absolute path of the input file.
    Additionally, an index file "index.txt" is created, which contains
    the input file paths and the resulting hdf5 file names.
    """

    # TODO: replacement strategy
    def __init__(self, directory):
        """
        **Parameters:**
            `directory` :
                path of the directory in which the cahce files are stored
        """
        self.directory = directory
        self.index = dict()
        self.indexfilepath = self.abspath("index.txt")
        if not os.path.isdir(directory):
            os.mkdir(directory)
        self.buildindex()
        self.writeindex()

    def __contains__(self, filepath):
        """
        **Parameters:**
            `filepath` :
                path to the input file

        **Returns:**
            If a cache file for the given input file exists.
        """
        sourcefilepath = os.path.abspath(filepath)
        cachefilepath = self.abspath(self.cachefile(sourcefilepath))
        return os.path.isfile(cachefilepath)

    def __getitem__(self, filepath):
        """
        Get the cache file for a given input file.

        **Parameters:**
            `filepath` :
                path to the input file

        **Returns:**
            A :class:`core.file.HDF5File` object.
            If no cache file exist for the input file, a new one is created.
        """
        sourcefilepath = os.path.abspath(filepath)
        cachefilepath = self.abspath(self.cachefile(sourcefilepath))
        if sourcefilepath not in self.index:
            self.index[sourcefilepath] = cachefilepath
            self.writeindex()
        cachefile = core.file.HDF5File(cachefilepath, sourcefilepath)
        # TODO: what if not sourcefilepath == cachefile.info.sourcefilepath
        return cachefile

    def abspath(self, filename):
        return os.path.abspath(os.path.join(self.directory, filename))

    def cachefile(self, filepath):
        return sha256(filepath).hexdigest() + ".hdf5"

    def buildindex(self):
        self.index = dict()
        for filename in os.listdir(self.directory):
            if not filename.split(".")[-1] == "hdf5":
                continue
            cachepath = self.abspath(filename)
            try:
                cachefile = core.file.HDF5File(cachepath)
                filepath = cachefile.info.sourcefilepath
                if filepath is not None \
                        and filename == self.cachefile(filepath):
                    self.index[filepath] = filename
            except (IOError, AttributeError, RuntimeError):
                pass

    def writeindex(self):
        with open(self.indexfilepath, "w") as f:
            for filepath, cachefile in sorted(self.index.iteritems(),
                                              key=lambda x: x[0]):
                print >>f, filepath + "; " + cachefile

calculation = Calculation()

