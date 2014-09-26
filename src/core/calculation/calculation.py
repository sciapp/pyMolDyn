# -*- coding: utf-8 -*-

__all__ = ["Calculation", "calculated"]

from file import CalculationCache
from data import Results, Domains, Cavities
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation
from discretization import DiscretizationCache, AtomDiscretization
import message


class Calculation(object):
    #TODO:
    # cache lookup OR isinstance(inputfile, ResultFile); inputfile.getresults()
    # dependencies
    # calculation
    # cache write
    def __init__(self):
        self.cache = CalculationCache("../results")

    def iscalculated(self, inputfile, frame, resolution, center=False):
        info = self.cache.getinfo(inputfile.path)
        if resolution in info:
            if center:
                frames = info[resolution].center.frames
            else:
                frames = info[resolution].surface.frames
            return frame in frames
        return False

    def calculate(self, inputfile, frame, resolution, center=False):
        results = self.cache.getresults(inputfile.path, frame, resolution)
        if results and ((center and results.center_cavities) or
                        (not center and results.surface_cavities)):
            message.print_message("Reusing results")
        else:
            volume = inputfile.volume
            atoms = inputfile.getatoms(frame)

            discretization_cache = DiscretizationCache('cache.hdf5')
            discretization = discretization_cache.get_discretization(volume, resolution)
            atom_discretization = AtomDiscretization(atoms, discretization)
            domain_calculation = DomainCalculation(discretization, atom_discretization)
            cavity_calculation = CavityCalculation(domain_calculation, use_surface_points = not center)

            domains = Domains.fromcalculation(domain_calculation)
            if center:
                surface_cavities = None
                center_cavities = Cavities.fromcalculation(cavity_calculation)
            else:
                surface_cavities = Cavities.fromcalculation(cavity_calculation)
                center_cavities = None
            results = Results(inputfile.path, frame, resolution, atoms, domains, surface_cavities, center_cavities)
            self.cache.addresults(results)
        return results


# for compatibility, because this function, which used a nasty hardcoded path, is called everywhere
def calculated(filename, frame_nr, resolution, use_center_points):
    """
    returns whether there is a result for the given parameters
    """
    return False # i hate you
