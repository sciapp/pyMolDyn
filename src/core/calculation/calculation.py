# -*- coding: utf-8 -*-


__all__ = ["Calculation",
           "CalculationCache",
           "CalculationSettings",
           "calculated",
           "count_frames",
           "calculated_frames",
           "calculate_cavities",
           "getresults"]


import os
import core.data as data
import core.file
from core.file import File
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation, FakeDomainCalculation
from discretization import DiscretizationCache, AtomDiscretization
import util.message as message
from hashlib import sha256
from util.trap import trap
from config.configuration import config


class CalculationSettings(object):

    def __init__(self,
            filenames,
            frames=[-1],
            resolution=config.Computation.std_resolution,
            domains=False,
            surface_cavities=False,
            center_cavities=False):
        self.filenames = list(filenames)
        self.frames = frames
        self.resolution = resolution
        self.domains = domains
        self.surface_cavities = surface_cavities
        self.center_cavities = center_cavities
        self.bonds = False
        self.dihedral_angles = False


class Calculation(object):
    def __init__(self, cachedir=None):
        if cachedir is None:
            cachedir = config.Path.result_dir
        self.cache = CalculationCache(cachedir)

    def calculatedframes(self, filepath, resolution, surface=False, center=False):
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
        calc = self.calculatedframes(filepath, resolution, surface, center)
        return calc[frame]

    def iscalculated(self, filepath, frame, resolution, surface=False, center=False):
        return not self.timestamp(filepath, frame,
                                  resolution, surface, center) is None

    def getresults(self, filepath, frame, resolution, surface=False, center=False):
        inputfile = File.open(filepath)
        # TODO: error handling
        if isinstance(inputfile, core.file.ResultFile):
            results = inputfile.getresults(frame, resolution)
        elif filepath in self.cache: 
            results = self.cache[filepath].getresults(frame, resolution)
        else:
            results = data.Results(filepath, frame, resolution, inputfile.getatoms(frame), None, None, None)
        return results

    def calculateframe(self, filepath, frame, resolution, surface=False, center=False, atoms=None):
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

        if not (results.domains is None
                or (surface and results.surface_cavities is None) \
                or (center and results.center_cavities is None)):
            message.print_message("Reusing results")
        else:
            # TODO: cache directory from config
            discretization_cache = DiscretizationCache('cache.hdf5')
            discretization = discretization_cache.get_discretization(volume, resolution)
            atom_discretization = AtomDiscretization(atoms, discretization)
            if results.domains is None \
                    or (surface and results.surface_cavities is None):
                # CavityCalculation depends on DomainCalculation
                message.print_message("Calculating domains")
                domain_calculation = DomainCalculation(discretization, atom_discretization)
            if results.domains is None:
                results.domains = data.Domains(domain_calculation)

            if surface and results.surface_cavities is None:
                message.print_message("Calculating surface-based cavities")
                cavity_calculation = CavityCalculation(domain_calculation, use_surface_points = True)
                results.surface_cavities = data.Cavities(cavity_calculation)

            if center and results.center_cavities is None:
                message.print_message("Calculating center-based cavities")
                domain_calculation = FakeDomainCalculation(discretization, atom_discretization, results)
                cavity_calculation = CavityCalculation(domain_calculation, use_surface_points = False)
                results.center_cavities = data.Cavities(cavity_calculation)
            # TODO: overwrite?
            resultfile.addresults(results)

        return results

    def calculate(self, calcsettings):
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
                        surface=calcsettings.surface_cavities,
                        center=calcsettings.center_cavities)
                fileresults.append(frameresult)
            allresults.append(fileresults)
        return allresults


class CalculationCache(object):
    #TODO: replacement strategy
    def __init__(self, directory):
        self.directory = directory
        self.index = dict()
        self.indexfilepath = self.abspath("index.txt")
        self.buildindex()
        self.writeindex()

    def __contains__(self, filepath):
        sourcefilepath = os.path.abspath(filepath)
        cachefilepath = self.abspath(self.cachefile(sourcefilepath))
        return os.path.isfile(cachefilepath)

    def __getitem__(self, filepath):
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
    trap("DEPRECATED")
    filepath = os.path.abspath(filename)
    frame = frame_nr - 1
    return calculation.iscalculated(filepath, frame, resolution, not use_center_points, use_center_points)


def count_frames(filename):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    return f.info.num_frames


def calculated_frames(filename, resolution):
    trap("DEPRECATED")
    filepath = os.path.abspath(filename)
    timestamps = calculation.calculatedframes(filepath, resolution, True, False)
    return [i + 1 for i, ts in enumerate(timestamps) if not ts is None]


def getresults(filename, frame_nr, volume, resolution):
    trap("DEPRECATED")
    filepath = os.path.abspath(filename)
    frame = frame_nr - 1
    return calculation.getresults(filepath, frame, resolution, True, True)


def calculate_cavities(filename, frame_nr, volume, resolution, use_center_points=False):
    trap("DEPRECATED")
    filepath = os.path.abspath(filename)
    frame = frame_nr - 1
    message.print_message("Cavity calculation...")
    results = calculation.calculateframe(filepath, frame, resolution, not use_center_points, use_center_points)
    message.print_message('calculation finished')
    message.finish()
    return results

