# -*- coding: utf-8 -*-
"""
With the classes in this module the rather complicated calculation process
can be started with a simple method call.
Additionally, results are stored in a cache and can be reused later.
"""

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


logger = Logger("calculation")
logger.setstream("default", sys.stdout, Logger.WARNING)


class CalculationSettings(object):
    """
    Structure to store the parameters for one or more calculation.

    **Attributes:**
        `filenames` :
            list of names of input files, from which the atoms will be loaded
        `frames` :
            list of frame numbers which are used for every filename
            in `filenames`. ``[-1]`` means 'all frames'.
        `resolution` :
            resolution parameter for the discretization
        `domains` :
            calculate cavitiy domains
        `surface_cavities` :
            calculate surface-based cavities
        `center_cavities` :
            calculate center-based cavities
        `bonds` :
            calculate bonds
        `dihedral_angles` :
            calculate dihedral angles
        `recalculate` :
            results will be calculated even if cached results exists
    """

    def __init__(self,
            filenames,
            frames=[-1],
            resolution=config.Computation.std_resolution,
            domains=False,
            surface_cavities=False,
            center_cavities=False,
            recalculate=False):
        """
        """
        self.filenames = list(filenames)
        self.frames = frames
        self.resolution = resolution
        self.domains = domains
        self.surface_cavities = surface_cavities
        self.center_cavities = center_cavities
        self.bonds = False
        self.dihedral_angles = False
        self.recalculate = recalculate

    def copy(self):
        """
        **Returns:**
            A deep copy of this object.
        """
        filenames = [f for f in self.filenames]
        frames = [f for f in self.frames]
        return CalculationSettings(filenames,
                frames,
                self.resolution,
                self.domains,
                self.surface_cavities,
                self.center_cavities,
                self.recalculate)


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
            cachedir = config.Path.result_dir
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
        if not info is None:
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

    def getresults(self, filepath, frame, resolution, surface=False, center=False):
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
        if isinstance(inputfile, core.file.ResultFile):
            results = inputfile.getresults(frame, resolution)
        elif filepath in self.cache: 
            results = self.cache[filepath].getresults(frame, resolution)
        else:
            results = data.Results(filepath, frame, resolution, inputfile.getatoms(frame), None, None, None)
        return results

    def calculateframe(self, filepath, frame, resolution, domains=False, surface=False, center=False, atoms=None, recalculate=False):
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
        results = resultfile.getresults(frame, resolution)

        if atoms is None:
            atoms = inputfile.getatoms(frame)
        volume = atoms.volume
        if results is None:
            results = data.Results(filepath, frame, resolution, atoms, None, None, None)

        if recalculate:
            results.domains = None
            if surface:
                results.surface_cavities = None
            if center:
                results.center_cavities = None

        if not ((domains and results.domains is None) \
                or (surface and results.surface_cavities is None) \
                or (center and results.center_cavities is None)):
            message.print_message("Reusing results")
        else:
            # TODO: cache directory from config
            discretization_cache = DiscretizationCache('cache.hdf5')
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
                cavity_calculation = CavityCalculation(domain_calculation, use_surface_points = True)
                results.surface_cavities = data.Cavities(cavity_calculation)
            message.progress(70)

            if center and results.center_cavities is None:
                message.print_message("Calculating center-based cavities")
                domain_calculation = FakeDomainCalculation(discretization, atom_discretization, results)
                cavity_calculation = CavityCalculation(domain_calculation, use_surface_points = False)
                results.center_cavities = data.Cavities(cavity_calculation)
            resultfile.addresults(results, overwrite=recalculate)

        message.progress(100)
        message.print_message('calculation finished')
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
        for filename in calcsettings.filenames:
            fileresults = []
            filepath = os.path.abspath(filename)
            if calcsettings.frames[0] == -1:
                inputfile = File.open(filepath)
                frames = range(inputfile.info.num_frames)
            else:
                frames = calcsettings.frames
            for frame in frames:
                frameresult = self.calculateframe(filepath,
                        frame,
                        calcsettings.resolution,
                        domains=calcsettings.domains,
                        surface=calcsettings.surface_cavities,
                        center=calcsettings.center_cavities,
                        recalculate=calcsettings.recalculate)
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
        if not sourcefilepath in self.index:
            self.index[sourcefilepath] = cachefilepath
            self.writeindex()
        cachefile = core.file.HDF5File(cachefilepath, sourcefilepath)
        #TODO: what if not sourcefilepath == cachefile.info.sourcefilepath
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
                if not filepath is None \
                        and filename == self.cachefile(filepath):
                    self.index[filepath] = filename
            except (IOError, AttributeError):
                pass

    def writeindex(self):
        with open(self.indexfilepath, "w") as f:
            for filepath, cachefile in sorted(self.index.iteritems(),
                                              key=lambda x: x[0]):
                print >>f, filepath + "; " + cachefile


#TODO: remove deprecated operations below


calculation = Calculation()


def calculated(filename, frame_nr, resolution, use_center_points):
    logger.warn("use of deprecated function")
    filepath = os.path.abspath(filename)
    frame = frame_nr - 1
    return calculation.iscalculated(filepath, frame, resolution, not use_center_points, use_center_points)


def count_frames(filename):
    logger.warn("use of deprecated function")
    f = core.file.XYZFile(filename)
    return f.info.num_frames


def calculated_frames(filename, resolution):
    logger.warn("use of deprecated function")
    filepath = os.path.abspath(filename)
    timestamps = calculation.calculatedframes(filepath, resolution, True, False)
    cf = [i + 1 for i, ts in enumerate(timestamps) if not ts is None]
    return cf


def getresults(filename, frame_nr, volume, resolution):
    logger.warn("use of deprecated function")
    filepath = os.path.abspath(filename)
    frame = frame_nr - 1
    return calculation.getresults(filepath, frame, resolution, True, True)


def calculate_cavities(filename, frame_nr, volume, resolution, use_center_points=False):
    logger.warn("use of deprecated function")
    filepath = os.path.abspath(filename)
    frame = frame_nr - 1
    message.print_message("Cavity calculation...")
    results = calculation.calculateframe(filepath, frame, resolution, True, not use_center_points, use_center_points)
    message.print_message('calculation finished')
    message.finish()
    return results


def delete_center_cavity_information(*args):
    logger.warn("use of deprecated function")
    pass


def timestamp(filename, resolution, center_based, frames):
    logger.warn("use of deprecated function")
    filepath = os.path.abspath(filename)
    ts = calculation.calculatedframes(filepath, resolution, not center_based, center_based)
    if frames[0] != -1:
        ts = [ts[f - 1] for f in frames]
    def fmt(t):
        if t is None:
            return "X"
        else:
            t.strftime("%d.%m.%Y %H:%M:%S")

    ts = map(fmt, ts)
    return ts

def calculate(settings):
    logger.warn("use of deprecated function")
    settings.frames = [f - 1 for f in settings.frames]
    return calculation.calculate(settings)

