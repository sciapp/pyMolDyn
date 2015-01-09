# -*- coding: utf-8 -*-
"""
Calculate radial distribution functions.
"""


__all__ = ["RDF"]


import numpy as np
import math
from util.logger import Logger
import sys
from core.calculation.discretization import DiscretizationCache


logger = Logger("statistics.rdf")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class RDF(object):
    """
    Calculate radial distribution functions for atoms and cavities.
    """

    def __init__(self, *args):
        """
        Create a sample from atom and cavity positions and smooth them to
        get the RDFs

        The constructor can be called in two ways:

        - ``RDF(results)`` :
            retrieve the data from :class:`core.data.Results`

        - ``RDF(positions, elements, cavitycenters, volume)`` :
            use the given arrays and the volume object
        """
        if len(args) == 1:
            results = args[0]
            positions = results.atoms.positions
            elements = results.atoms.elements
            volume = results.atoms.volume
            if not results.domains is None:
                centers = results.domains.centers
                dcache = DiscretizationCache('cache.hdf5')
                disc = dcache.get_discretization(volume, results.resolution)
                centers = map(disc.discrete_to_continuous, centers)
            else:
                centers = []
        elif len(args) == 4:
            positions, elements, centers, volume = args
        else:
            raise TypeError("RDF expects 1 or 4 parameters")

        self.positions = np.array(positions, copy=False)
        self.elements = np.array(elements, dtype="|S4", copy=False)
        self.centers = np.array(centers, copy=False)
        self.volume = volume
        self.num_atoms = np.where(self.elements != "cav")[0].size
        self.numberdensity = float(self.num_atoms) / self.volume.volume

        self.stats = self._genstats(self.positions,
                                    self.elements,
                                    self.centers,
                                    self.volume)

    def rdf(self, elem1, elem2, cutoff=None, h=0.5, kernel=None):
        """
        Calculate a smoothed radial distribution function between the elements
        `elem1` and `elem2`.

        **Parameters:**
            `elem1`, `elem2` :
                Chemical element, e.g. 'Ge', 'Te' or 'cav' for cavities

            `h` :
                Smoothing parameter. The greater `h` is,
                the more the function is smoothed.

            `kernel` :
                Smoothing kernel

        **Returns:**
            Python function that represents the radial distribution function.
            It also accepts Numpy arrays as input.
            Returns `None` if the given elements do not exist or if there is
            not enough data to create the function.
        """
        if kernel is None:
            kernel = Kernels.epanechnikov

        data = None
        for s in self.stats:
            if set((elem1.lower(), elem2.lower())) \
                    == set((s[0].lower(), s[1].lower())):
                data = s[2]
                break;
        if data is None:
            logger.debug("No statistical data for '{}-{}' found.".format(
                    elem1, elem2))
            return None # TODO: raise Exception
        
        if cutoff is None:
            cutoff = data.max()
        sel = np.where(np.logical_and(data > 1e-10, data <= cutoff))[0]
        sel = data[sel]
        if len(sel) < 2:
            logger.debug("Not enough data for '{}-{}' in cutoff={} range.".format(elem1, elem2, cutoff))
            return None # TODO: raise Exception

        if h > 0.9 * sel.min():
            logger.debug("Bandwidth {} above threshold. Setting to {}.".format(h, 0.9 * sel.min()))
            h = 0.9 * sel.min()
        kde = Functions.Convolution(sel, h=h, kernel=Kernels.epanechnikov)

        def wfunc(r):
            y = np.zeros_like(r)
            i = np.where(np.abs(r) > 1e-10)[0]
            y[i] = self.volume.volume / (data.size * 4 * math.pi * r[i]**2)
            return y

        return Functions.Product(kde, wfunc)

    @staticmethod
    def _correlatedistance(pos1, pos2=None, volume=None):
        """
        Measure the distances between coordinates.

        - ``_correlatedistance(pos1)`` :
            Correlate the coordinates in `pos1` with each other

        - ``_correlatedistance(pos1, pos2)`` :
            Correlate each coordinate in pos1 with each coordinate in pos2

        **Returns:**
            A sorted sample.
        """
        if volume is None:
            distance = lambda x, y: y-x
        else:
            distance = volume.get_distance

        if pos2 is None:
            n = pos1.shape[0]
            # TODO: list comprehension
            a1 = pos1[0:-1]
            a2 = pos1[1:]
            for i in range(2, n):
                a1 = np.vstack((a1, pos1[0:-i]))
                a2 = np.vstack((a2, pos1[i:]))
        else:
            n1 = pos1.shape[0]
            n2 = pos2.shape[0]
            a1 = np.hstack([pos1] * n2).reshape(n1 * n2, 3)
            a2 = np.vstack([pos2] * n1)
        samples = np.linalg.norm(distance(a1, a2), 2, axis=-1)
        samples.sort()

        return samples

    @classmethod
    def _genstats(cls, positions, elements, centers, volume=None):
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
                    s = cls._correlatedistance(pos[i], volume=volume)
                else:
                    s = cls._correlatedistance(pos[i], pos[j], volume=volume)
                if len(s) > 1:
                    stats.append((e1, e2, s))

        return stats


class Functions(object):
    """
    Utility class with Callables
    """

    class Convolution(object):
        """
        Discrete convolution
        """

        def __init__(self, x, y=None, h=1.0, kernel=None):
            if y is None:
                y = np.ones_like(x)
            if kernel is None:
                kernel = Kernels.gauss
            self.x = x
            self.y = y
            self.h = h
            self.kernel = kernel

        def __call__(self, x):
            fx = np.zeros_like(x)
            for xi, yi in zip(self.x, self.y):
                fx += yi * self.kernel((x - xi) / self.h) / self.h
            return fx

    class Product(object):
        """
        Product of two functions
        """

        def __init__(self, f, g):
            self.f = f
            self.g = g

        def __call__(self, x):
            return self.f(x) * self.g(x)


class Kernels(object):
    """
    Utility class with smoothing kernels
    """

    @staticmethod
    def gauss(x):
        c = 1.0 / math.sqrt(2.0 * math.pi)
        return c * np.exp(-0.5 * x**2)

    @staticmethod
    def compact(x):
        c = 2.25228362104
        if not isinstance(x, np.ndarray):
            if abs(x) < 1.0:
                return c * math.exp(1.0 / (x**2 - 1.0))
            else:
                return 0.0
        else:
            i = np.where(np.abs(x) < 1.0)[0]
            y = np.zeros(x.size)
            y[i] = c * np.exp(1.0 / (x[i]**2 - 1.0))
            return y

    @staticmethod
    def triang(x):
        c = 1.0
        if not isinstance(x, np.ndarray):
            if abs(x) < 1.0:
                return c * (1.0 - abs(x))
            else:
                return 0.0
        else:
            i = np.where(np.abs(x) < 1.0)[0]
            y = np.zeros(x.size)
            y[i] = c * (1.0 - np.abs(x[i]))
            return y

    @staticmethod
    def quad(x):
        c = 0.5
        if not isinstance(x, np.ndarray):
            if abs(x) < 1.0:
                return c
            else:
                return 0.0
        else:
            i = np.where(np.abs(x) < 1.0)[0]
            y = np.zeros(x.size)
            y[i] = c
            return y

    @staticmethod
    def posquad(x):
        c = 1.0
        if not isinstance(x, np.ndarray):
            if 0 <= x < 1.0:
                return c
            else:
                return 0.0
        else:
            i = np.where(np.logical_and(x >= 0.0, x < 1.0))[0]
            y = np.zeros(x.size)
            y[i] = c
            return y

    @staticmethod
    def negquad(x):
        c = 1.0
        if not isinstance(x, np.ndarray):
            if -1.0 < x <= 0.0:
                return c
            else:
                return 0.0
        else:
            i = np.where(np.logical_and(x > -1.0, x <= 0.0))[0]
            y = np.zeros(x.size)
            y[i] = c
            return y

    @staticmethod
    def epanechnikov(x):
        if not isinstance(x, np.ndarray):
            if abs(x) < 1.0:
                return 3 / 4 * (1.0 - x**2)
            else:
                return 0.0
        else:
            i = np.where(np.abs(x) < 1.0)[0]
            y = np.zeros_like(x)
            y[i] = 3.0 / 4.0 * (1.0 - x[i]**2)
            return y

    @staticmethod
    def bandwidth(n, d=1):
        """
        Scott's factor for bandwidth estimation
        """
        return (4.0 / 3.0 * n) ** (-1.0 / (d + 4.0))


class _TestRDF(object):
    @staticmethod
    def continuous_coordinates(coords, volume, resolution):
        dcache = DiscretizationCache('cache.hdf5')
        disc = dcache.get_discretization(volume, resolution)

        return np.array(map(disc.discrete_to_continuous, coords))

    @staticmethod
    def plotfunc(rdf, e1, e2, px, h, *args):
        gr = rdf.rdf(e1, e2, h=h)
        plt.plot(px, gr(px), *args, label=str(h))

    @classmethod
    def plotrdf(cls, rdf, e1, e2):
        px = np.linspace(0, 10, 400)
        plt.figure()
        cls.plotfunc(rdf, e1, e2, px, 0.25, "g--")
        cls.plotfunc(rdf, e1, e2, px, 0.5, "r-")
        cls.plotfunc(rdf, e1, e2, px, 1.0, "b--")
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
        print "generating statistics..."
        rdf = RDF(res)
        #centers = cls.continuous_coordinates(res.domains.centers,
        #                                     res.atoms.volume,
        #                                     res.resolution)
        #rdf = RDF(res.atoms.positions, res.atoms.elements,
        #                  centers, res.atoms.volume)

        print "plotting..."
        cls.plotrdf(rdf, "Ge", "Ge")
        cls.plotrdf(rdf, "Ge", "Te")
        cls.plotrdf(rdf, "cav", "cav")
        plt.show()


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    _TestRDF.run()
    #x = np.linspace(-2, 2, 200)
    #plt.plot(x, Kernels.gauss(x))
    #plt.plot(x, Kernels.compact(x))
    #plt.plot(x, Kernels.triang(x))
    #plt.plot(x, Kernels.quad(x))
    #plt.plot(x, Kernels.epanechnikov(x))
    #plt.show()
