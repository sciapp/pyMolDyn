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
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation
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

    def calculatedframes(self, inputfile, resolution, center=False):
        info = None
        if isinstance(inputfile, core.file.ResultFile):
            info = inputfile.info
        else:
            if inputfile.path in self.cache:
                cf = self.cache[inputfile.path]
                info = cf.info
        if not info is None:
            if center:
                return info[resolution].center_cavities
            else:
                return info[resolution].surface_cavities
        else:
            return data.TimestampList(inputfile.info.num_frames)

    def timestamp(self, inputfile, frame, resolution, center=False):
        calc = self.calculatedframes(inputfile, resolution, center)
        return calc[frame]

    def iscalculated(self, *args):
        inputfile, frame, resolution = args[:3]
        if len(args) > 3:
            center = args[3]
        else:
            center=False
        return not self.timestamp(inputfile, frame,
                                  resolution, center) is None

    def getresults(self, *args):
        inputfile, frame, resolution = args[:3]
        if len(args) > 3:
            center = args[3]
        else:
            center=False
        if isinstance(inputfile, core.file.ResultFile):
            resultfile = inputfile
        else:
            resultfile = self.cache[inputfile.path]
        results = resultfile.getresults(frame, resolution)

    def calculate(self, *args):
        inputfile, frame, resolution = args[:3]
        if len(args) > 3:
            center = args[3]
        else:
            center=False
        if isinstance(inputfile, core.file.ResultFile):
            resultfile = inputfile
        else:
            resultfile = self.cache[inputfile.path]
        results = resultfile.getresults(frame, resolution)

        if not results is None \
                and not results.domains is None \
                and ((center and results.center_cavities) \
                        or (not center and results.surface_cavities)):
            message.print_message("Reusing results")
        else:
            volume = inputfile.info.volume
            atoms = inputfile.getatoms(frame)

            discretization_cache = DiscretizationCache('cache.hdf5')
            discretization = discretization_cache.get_discretization(volume, resolution)
            atom_discretization = AtomDiscretization(atoms, discretization)
            domain_calculation = DomainCalculation(discretization, atom_discretization)
            cavity_calculation = CavityCalculation(domain_calculation, use_surface_points = not center)

            domains = data.Domains(domain_calculation)
            if center:
                surface_cavities = None
                center_cavities = data.Cavities(cavity_calculation)
            else:
                surface_cavities = data.Cavities(cavity_calculation)
                center_cavities = None
            results = data.Results(inputfile.path, frame, resolution,
                                   atoms, domains,
                                   surface_cavities, center_cavities)
            resultfile.addresults(results)
        return results


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
    f = core.file.XYZFile(filename)
    return calculation.iscalculated(f, frame_nr - 1, resolution, use_center_points)


def count_frames(filename):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    return f.info.num_frames


def calculated_frames(filename, resolution):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    timestamps = calculation.calculatedframes(f, resolution, False)
    return [i + 1 for i, ts in enumerate(timestamps) if not ts is None]


def getresults(filename, frame_nr, volume, resolution):
    trap("DEPRECATED")
    results = None
    if filename in calculation.cache:
        cachefile = calculation.cache[filename]
        results = cachefile.getresults(frame_nr - 1, resolution)
    if results is None:
        f = core.file.XYZFile(filename)
        results = data.Results(f.path, frame_nr - 1, resolution, f.getatoms(frame_nr - 1), None, None, None)
    return results


def calculate_cavities(filename, frame_nr, volume, resolution, use_center_points=False):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    message.print_message("Cavity calculation...")
    results = calculation.calculate(f, frame_nr - 1, resolution, use_center_points)
    message.print_message('calculation finished')
    message.finish()
    return results

