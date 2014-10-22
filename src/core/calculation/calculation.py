# -*- coding: utf-8 -*-
# TODO: where to create the calculation object?
# TODO: what if i want a results object without calculated results, e.g. for the visualization?


__all__ = ["Calculation",
           "CalculationCache",
           "calculated",
           "count_frames",
           "calculated_frames",
           "calculate_cavities"
          ]


import os
import core.data as data
import core.file
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation
from discretization import DiscretizationCache, AtomDiscretization
import util.message as message
from hashlib import sha256
from util.trap import trap


class Calculation(object):
    def __init__(self, cachedir=None):
        if cachedir is None:
            #TODO: read cachedir from config
            cachedir = "../results"
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

    def __contains__(self, args):
        inputfile, frame, resolution = args[:3]
        if len(args) > 3:
            center = args[3]
        else:
            center=False
        return not self.timestamp(inputfile, frame,
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


#TODO: remove deprecated operations below


calculation = Calculation()


def calculated(filename, frame_nr, resolution, use_center_points):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    return (f, frame_nr - 1, resolution, use_center_points) in calculation


def count_frames(filename):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    return f.info.num_frames


def calculated_frames(filename, resolution):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    timestamps = calculation.calculatedframes(f, resolution, False)
    return [i + 1 for i, ts in enumerate(timestamps) if not ts is None]


def calculate_cavities(filename, frame_nr, volume, resolution, use_center_points=False):
    trap("DEPRECATED")
    f = core.file.XYZFile(filename)
    message.print_message("Cavity calculation...")
    results = calculation[f, frame_nr - 1, resolution, use_center_points]
    message.print_message('calculation finished')
    message.finish()
    return results


#def atom_volume_discretization(atoms, volume, resolution):
#    """
#    calculates the discretization of the volume and the atoms from the given resolution
#    """
#    num_atoms = len(atoms)
#    atom_positions = [atom.coords for atom in atoms]
#
#    print_message(num_atoms, "atoms")
#    for atom_index in range(num_atoms):
#        atom_positions[atom_index] = volume.get_equivalent_point(atom_positions[atom_index])
#    atoms = Atoms(atom_positions, [config.Computation.ATOM_RADIUS] * num_atoms)
#    print_message("Volume discretization...")
#    discretization_cache = DiscretizationCache('cache.hdf5')
#    discretization = discretization_cache.get_discretization(volume, resolution)
#    print_message("Atom discretization...")
#    atom_discretization = AtomDiscretization(atoms, discretization)
#
#    return atom_discretization, discretization
#
#
#def calculate_domains(filename, frame_nr, volume, resolution):
#    import pybel
#
#    n = 0
#    generator = pybel.readfile("xyz", filename)
#    molecule = None
#    try:
#        for i in range(frame_nr):
#            molecule = generator.next()
#    except StopIteration:
#        if frame_nr > n:
#            print_message('Error: This frame does not exist.')
#            sys.exit(0)
#    (atom_discretization, discretization) = atom_volume_discretization(molecule.atoms, volume, resolution)
#
#    print_message("Cavity domain calculation...")
#    domain_calculation = DomainCalculation(discretization, atom_discretization)
#
#    return domain_calculation
#
#
#if __name__ == "__main__":
#    import pybel
#
#    # volume = volumes.HexagonalVolume(17.68943, 22.61158)
#    #    xyz/structure_c.xyz
#    box_size = 27.079855
#    volume = volumes.CubicVolume(box_size)
#    #for i in range(1, count_frames("xyz/structure_c.xyz")+1):
#    calculate_cavities("../xyz/structure_c.xyz", 1, volume, 64)
#    calculate_cavities("../xyz/structure_c.xyz", 1, volume, 64, False)
#
## calculate_cavities("xyz/hexagonal.xyz", 1, volume, 64)
##    calculate_cavities("xyz/hexagonal.xyz", 1, volume, 64, False)
