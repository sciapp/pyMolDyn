# -*- coding: utf-8 -*-
# TODO: where to create the calculation object?


__all__ = ["Calculation", "calculated"]


from file import CalculationCache
from data import Results, Domains, Cavities, TimestampList
from file import ResultFile
from datetime import datetime
from algorithm import CavityCalculation, DomainCalculation
from discretization import DiscretizationCache, AtomDiscretization
import message


class Calculation(object):
    def __init__(self):
        self.cache = CalculationCache("../results")

    def calculatedframes(self, inputfile, frame, resolution, center=False):
        calc = None
        if isinstance(inputfile, ResultFile):
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
            return TimestampList(inputfile.num_frames)

    def timestamp(self, inputfile, frame, resolution, center=False):
        calc = self.calculatedframes(inputfile, resolution, center)
        return calc[frame]

    def iscalculated(self, inputfile, frame, resolution, center=False):
        return not self.timestamp(self, inputfile, frame,
                                  resolution, center) is None

    def __contains__(self, tup):
        return self.iscalculated(*tup)

    def calculate(self, inputfile, frame, resolution, center=False):
        results = None
        if isinstance(inputfile, ResultFile):
            results = inputfile.getresults(frame, resolution)
        if results is None:
            cf = self.cache[inputfile.path]
            if not cf is None:
                results = cf.getresults(frame, resolution)

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

            domains = Domains.fromcalculation(domain_calculation)
            if center:
                surface_cavities = None
                center_cavities = Cavities.fromcalculation(cavity_calculation)
            else:
                surface_cavities = Cavities.fromcalculation(cavity_calculation)
                center_cavities = None
            results = Results(inputfile.path, frame, resolution,
                              atoms, domains,
                              surface_cavities, center_cavities)
            self.cache.addresults(results)
        return results

    def __getitem__(self, inputfile, frame, resolution, center=False):
        return self.calculate(inputfile, frame, resolution, center)


# for compatibility, because this function is called everywhere
def calculated(filename, frame_nr, resolution, use_center_points):
    """
    returns whether there is a result for the given parameters
    """
    return False
