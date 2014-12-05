# -*- coding: utf-8 -*-


import numpy as np
import scipy as sp
from scipy import stats
import matplotlib.pyplot as plt
from util.logger import Logger
import sys
from core.calculation.discretization import DiscretizationCache


logger = Logger("statistics.partialpdf")
logger.setstream("default", sys.stdout, Logger.DEBUG)


def createstat(pos1, pos2=None):
    if pos2 is None:
        n = pos1.shape[0]
        samples = np.zeros([(n * n - n) / 2])
        k = 0
        for i in range(n):
            for j in range(i + 1, n):
                samples[k] = np.linalg.norm(pos1[i, :] - pos1[j, :], 2)
                k += 1
    else:
        n1 = pos1.shape[0]
        n2 = pos2.shape[0]
        samples = np.zeros([n1 * n2])
        k = 0
        for i in range(n1):
            for j in range(n2):
                samples[k] = np.linalg.norm(pos1[i, :] - pos2[j, :], 2)
                k += 1
    samples.sort()

    return samples
    

def partialpdf(atoms, cavitycenters=None):
    elements = np.unique(atoms.elements).tolist()
    if not cavitycenters is None and not "cav" in elements:
        elements.append("cav")
    positions = [None] * len(elements)
    for i, e in enumerate(elements):
        positions[i] = atoms.positions[np.where(atoms.elements == e)[0], :]

    if not cavitycenters is None:
        i = elements.index("cav")
        if positions[i].size > 0:
            positions[i] = np.vstack((positions[i], cavitycenters))
        else:
            positions[i] = cavitycenters

    stat = []
    for i, e1 in enumerate(elements):
        for j in range(i, len(elements)):
            e2 = elements[j]
            if i == j:
                s = createstat(positions[i])
            else:
                s = createstat(positions[i], positions[j])
            stat.append((e1, e2, s))

    return stat


def continuous_coordinates(coords, volume, resolution):
    dcache = DiscretizationCache('cache.hdf5')
    disc = dcache.get_discretization(volume, resolution)

    return np.array(map(disc.discrete_to_continuous, coords))


class TestPartialPDE(object):
    @staticmethod
    def plotpde(samples, **kwargs):
        kde = sp.stats.gaussian_kde(samples)
        kx = np.linspace(0, samples.max(), 200)
        ky = kde(kx)
        #iy = sp.integrate.cumtrapz(ky, kx)

        plt.figure()
        plt.plot(kx, ky, "r", **kwargs)
        #plt.figure()
        #plt.plot(kx, iy, "r", **kwargs)

    class TestAtoms(object):
        def __init__(self):
            self.elements = np.array(["Te", "Ge", "Ge", "Sb", "Ge", "Te"])
            self.positions = np.arange(e.size * 3, dtype=float).reshape(-1, 3)
            self.centers = np.array([[6, 5, 4], [3, 2, 1]], dtype=float)

    @classmethod
    def run(cls):
        #a = TestAtoms()
        #stat = partialpdf(a, a.centers)

        import core.calculation as calculation
        calc = calculation.Calculation("../results")
        filename = "../xyz/structure_c.xyz"
        resolution = 64
        #filename = "../xyz/GST_111_128_bulk.xyz"
        #resolution = 128
        settings = calculation.CalculationSettings(
                [filename],
                [0], resolution, True, False, False)
        print "calculating..."
        res = calc.calculate(settings)[0][0]
        centers = continuous_coordinates(res.domains.centers,
                                         res.atoms.volume,
                                         resolution)
#        np.savez("structure_c_128",
#                positions=res.atoms.positions,
#                elements=res.atoms.elements,
#                centers=centers)

        print "generating statistics..."
        stat = partialpdf(res.atoms, centers)
        for e1, e2, s in stat:
            if s.size > 1:
                print "{} - {}: {} distances".format(e1, e2, s.size)
                cls.plotpde(s)
                plt.title(e1 + " - " + e2)
        plt.show()


if __name__ == "__main__":
    TestPartialPDE.run()

