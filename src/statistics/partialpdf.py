# -*- coding: utf-8 -*-
"""
Calculate partial pair distribution functions.
"""


__all__ = ["PartialPDF"]


import numpy as np
import math
import matplotlib.pyplot as plt
from util.logger import Logger
import sys
from core.calculation.discretization import DiscretizationCache


logger = Logger("statistics.partialpdf")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class PartialPDF(object):
    """
    Calculate partial pair distribution functions for atoms and cavities.
    """

    def __init__(self, *args):
        """
        Create a sample from atom and cavity positions and smooth them to
        get the partial PDFs

        The constructor can be called in two ways:

        - ``PartialPDF(results)`` :
            retrieve the data from :class:`core.data.Results`

        - ``PartialPDF(positions, elements, cavitycenters, totalvolume)`` :
            use the given arrays and the total volume of the crystal
        """
        if len(args) == 1:
            results = args[0]
            positions = results.atoms.positions
            elements = results.atoms.elements
            volume = results.atoms.volume.volume
            if not results.domains is None:
                centers = results.domains.centers
                dcache = DiscretizationCache('cache.hdf5')
                disc = dcache.get_discretization(results.atoms.volume,
                                                 results.resolution)
                centers = map(disc.discrete_to_continuous, centers)
            else:
                centers = []
        elif len(args) == 4:
            positions, elements, centers, volume = args
        else:
            raise TypeError("PartialPDF expects 1 or 4 parameters")

        self.positions = np.array(positions, copy=False)
        self.elements = np.array(elements, dtype="|S4", copy=False)
        self.centers = np.array(centers, copy=False)
        self.volume = float(volume)
        self.num_atoms = np.where(self.elements != "cav")[0].size
        self.numberdensity = float(self.num_atoms) / self.volume

        self.stats = self._genstats(self.positions,
                                    self.elements,
                                    self.centers)

    def pdf(self, elem1, elem2, h=1.0):
        """
        Calculate a smoothed pair distribution function between the elements
        `elem1` and `elem2`.

        **Parameters:**
            `elem1`, `elem2` :
                Chemical element, e.g. 'Ge', 'Te' or 'cav' for cavities

            `h` :
                Smoothing parameter. The greater `h` is,
                the more the function is smoothed.

        **Returns:**
            Python function that represents the pair distribution function.
            It also accepts Numpy arrays as input.
            Returns `None` if the given elements do not exist or if there is
            not enough data to create the function.
        """
        data = None
        for s in self.stats:
            if set((elem1.lower(), elem2.lower())) \
                    == set((s[0].lower(), s[1].lower())):
                data = s[2]
                break;
        if data is None:
            logger.debug("No statistical data for '{}-{}' found.".format(
                    elem1, elem2))
            return None

        #TODO
        weights = self.volume / (4.0 * math.pi * data**2 \
                * data.size)
        return Smoothing.smooth(data, weights, h, Smoothing.gausskernel)

    @staticmethod
    def _correlatedistance(pos1, pos2=None):
        """
        Measure the distances between coordinates.

        - ``correlatedistance(pos1)`` :
            Correlate the coordinates in `pos1` with each other

        - ``correlatedistance(pos1, pos2)`` :
            Correlate each coordinate in pos1 with each coordinate in pos2

        **Returns:**
            A sorted sample.
        """
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

    @classmethod
    def _genstats(cls, positions, elements, centers):
        """
        Iterate through the elements and cavities and correlate the
        distances between atoms of that element/cavity and atoms of
        the other elements.
        """
        elemlist = np.unique(elements).tolist()
        if len(centers) > 0 and not "cav" in elemlist:
            elemlist.append("cav")
        pos = [None] * len(elemlist)
        for i, e in enumerate(elemlist):
            pos[i] = positions[np.where(elements == e)[0], :]

        if len(centers) > 0:
            i = elemlist.index("cav")
            if pos[i].size > 0:
                pos[i] = np.vstack((pos[i], centers))
            else:
                pos[i] = centers

        stats = []
        for i, e1 in enumerate(elemlist):
            for j in range(i, len(elemlist)):
                e2 = elemlist[j]
                if i == j:
                    s = cls._correlatedistance(pos[i])
                else:
                    s = cls._correlatedistance(pos[i], pos[j])
                #s = s[np.where(s <= 13.8)[0]]
                if len(s) > 1:
                    stats.append((e1, e2, s))

        return stats


class Smoothing(object):
    """
    Contains smoothing kernels and kernel-based smoothing functions.
    """

    @staticmethod
    def gausskernel(h):
        c = 1.0 / h / math.sqrt(2.0 * math.pi)
        def kern(x):
            return c * np.exp(-0.5 * (x / h)**2)
        return kern

    @staticmethod
    def compactkernel(h):
        h *= 2.0
        c = 2.25228362104 / h
        def kern(x):
            if not isinstance(x, np.ndarray):
                if abs(x) < h:
                    return c * math.exp(1.0 / ((x / h)**2 - 1.0))
                else:
                    return 0.0
            else:
                i = np.where(np.abs(x) < h)
                y = np.zeros(x.size)
                y[i] = c * np.exp(1.0 / ((x[i] / h)**2 - 1.0))
                return y

        return kern

    @staticmethod
    def triangkernel(h):
        h *= 2.0
        c = 1.0 / h
        def kern(x):
            if not isinstance(x, np.ndarray):
                if abs(x) < h:
                    return c * (1.0 - abs(x / h))
                else:
                    return 0.0
            else:
                i = np.where(np.abs(x) < h)
                y = np.zeros(x.size)
                y[i] = c * (1.0 - np.abs(x[i] / h))
                return y

        return kern

    @staticmethod
    def quadkernel(h):
        h *= 2.0
        c = 0.5 / h
        def kern(x):
            if not isinstance(x, np.ndarray):
                if abs(x) < h:
                    return c
                else:
                    return 0.0
            else:
                i = np.where(np.abs(x) < h)
                y = np.zeros(x.size)
                y[i] = c
                return y

        return kern

    @staticmethod
    def bandwidth(n, d=1):
        return n ** (-1.0 / (d + 4.0))

    @classmethod
    def kde(cls, samples, h, kernelgen=None):
        if kernelgen is None:
            kernelgen = cls.gausskernel
        kernel = kernelgen(cls.bandwidth(len(samples)) * h)
        def pdf(x):
            s = np.zeros([x.size])
            for xi in samples:
                s += kernel(x - xi)
            return s / len(samples)
        return pdf

    @classmethod
    def smooth(cls, xval, yval, h, kernelgen=None):
        if kernelgen is None:
            kernelgen = cls.gausskernel
        kernel = kernelgen(cls.bandwidth(len(xval)) * h)
        def func(x):
            s = np.zeros([x.size])
            for xi, yi in zip(xval, yval):
                s += yi * kernel(x - xi)
            return s
        return func


class TestPartialPDF(object):
    @staticmethod
    def continuous_coordinates(coords, volume, resolution):
        dcache = DiscretizationCache('cache.hdf5')
        disc = dcache.get_discretization(volume, resolution)

        return np.array(map(disc.discrete_to_continuous, coords))

    @staticmethod
    def plotfunc(pdf, e1, e2, px, h, *args):
        gr = pdf.pdf(e1, e2, h)
        plt.plot(px, gr(px), *args, label=str(h))

    @classmethod
    def plotpdf(cls, pdf, e1, e2):
        px = np.linspace(0, 10, 400)
        plt.figure()
        cls.plotfunc(pdf, e1, e2, px, 0.5, "g--")
        cls.plotfunc(pdf, e1, e2, px, 1.0, "r-")
        cls.plotfunc(pdf, e1, e2, px, 5.0, "b--")
        plt.legend(loc=0)
        plt.title("{}-{}".format(e1, e2))

    @classmethod
    def run(cls):
        import core.calculation as calculation
        calc = calculation.Calculation("../results")
        filename = "../xyz/structure_c.xyz"
        resolution = 64
        frame = 9
        #filename = "../xyz/GST_111_128_bulk.xyz"
        #resolution = 256
        #frame = 0
        settings = calculation.CalculationSettings(
                [filename],
                [frame], resolution, True, False, False)
        print "calculating..."
        res = calc.calculate(settings)[0][0]
        centers = cls.continuous_coordinates(res.domains.centers,
                                             res.atoms.volume,
                                             res.resolution)
        print "generating statistics..."
        pdf = PartialPDF(res)
        #pdf = PartialPDF(res.atoms.positions, res.atoms.elements,
        #                  centers, res.atoms.volume.volume)



        print "plotting..."
        cls.plotpdf(pdf, "Ge", "Ge")
        cls.plotpdf(pdf, "Ge", "Te")
        cls.plotpdf(pdf, "cav", "cav")
        plt.show()


if __name__ == "__main__":
    TestPartialPDF.run()
