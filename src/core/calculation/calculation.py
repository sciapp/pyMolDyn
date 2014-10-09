# -*- coding: utf-8 -*-
# TODO: where to create the calculation object?


__all__ = ["Calculation", "calculated"]


import os
import core.data as data
import core.file
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation
from discretization import DiscretizationCache, AtomDiscretization
import util.message as message
from hashlib import sha256


class Calculation(object):
    def __init__(self, cachedir=None):
        if cachedir is None:
            #TODO: read cachedir from config
            cachedir = "../results"
        self.cache = CalculationCache(cachedir)

    def calculatedframes(self, inputfile, resolution, center=False):
        calc = None
        if isinstance(inputfile, core.file.ResultFile):
            calc = inputfile.calculated
        else:
            cf = self.cache[inputfile.path]
            if not cf is None:
                calc = cf.calculated
        if not calc is None:
            if center:
                return calc[resolution].center_cavities
            else:
                return calc[resolution].surface_cavities
        else:
            return data.TimestampList(inputfile.num_frames)

    def timestamp(self, inputfile, frame, resolution, center=False):
        calc = self.calculatedframes(inputfile, resolution, center)
        return calc[frame]

    def __contains__(self, args):
        inputfile, frame, resolution = args[:3]
        if len(args) > 3:
            center = args[3]
        else:
            center=False
        return not self.timestamp(self, inputfile, frame,
                                  resolution, center) is None

    def __getitem__(self, args):
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
        #TODO: writing happens implicit

        if not results is None \
                and not results.domains is None \
                and ((center and results.center_cavities) \
                        or (not center and results.surface_cavities)):
            message.print_message("Reusing results")
        else:
            volume = inputfile.volume
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
        #TODO: create file if it not exists?
        sourcefilepath = os.path.abspath(filepath)
        cachefilepath = self.abspath(self.cachefile(sourcefilepath))
        if not sourcefilepath in self.index:
            self.index[sourcefilepath] = cachefilepath
            self.writeindex()
        cachefile = core.file.HDF5File(cachefilepath, sourcefilepath)
        #TODO: if not sourcefilepath == cachefile.info.sourcefilepath:
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
            #TODO: error handling
            cachefile = core.file.HDF5File(cachepath)
            filepath = cachefile.info.sourcefilepath
            if not filepath is None \
                    and filename == self.cachefile(filepath):
                self.index[filepath] = filename

    def writeindex(self):
        with open(self.indexfilepath, "w") as f:
            for filepath, cachefile in sorted(self.index.iteritems(),
                                              key=lambda x: x[0]):
                print >>f, filepath + "; " + cachefile

