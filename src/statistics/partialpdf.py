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

    def pdf(self, elem1, elem2, h=1.0, cutoff=None):
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
        
        if cutoff is None:
            cutoff = data.max()

        sel = np.where(np.logical_and(data > 1e-10, data <= cutoff))[0]
        sel = data[sel]
        if len(sel) < 2:
            logger.debug("Not enough data for '{}-{}' in cutoff={} range.".format(elem1, elem2, cutoff))
            return None

        def wfunc(r):
            y = np.zeros_like(r)
            i = np.where(np.abs(r) > 1e-10)
            y[i] = self.volume / (data.size * 4 * math.pi * (r[i])**2)
            return y
        exact = FunctionKDE(sel, wfunc, h, normalize=False)

        weights = self.volume / (data.size * 4 * math.pi * sel**2)
        approx = WeightedKDE(sel, weights, h, normalize=False)
        return approx

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
                if len(s) > 1:
                    stats.append((e1, e2, s))

        return stats


class Kernels(object):
    @staticmethod
    def gauss(x):
        c = 1.0 / math.sqrt(2.0 * math.pi)
        return c * np.exp(-0.5 * x**2)

    @staticmethod
    def compact(x):
        c = 2.25228362104 / 2.0
        if not isinstance(x, np.ndarray):
            if abs(x) < 2.0:
                return c * math.exp(1.0 / ((x / 2.0)**2 - 1.0))
            else:
                return 0.0
        else:
            i = np.where(np.abs(x) < 2.0)[0]
            y = np.zeros(x.size)
            y[i] = c * np.exp(1.0 / ((x[i] / 2.0)**2 - 1.0))
            return y

    @staticmethod
    def triang(x):
        c = 0.5
        if not isinstance(x, np.ndarray):
            if abs(x) < 2.0:
                return c * (1.0 - abs(x / 2.0))
            else:
                return 0.0
        else:
            i = np.where(np.abs(x) < 2.0)[0]
            y = np.zeros(x.size)
            y[i] = c * (1.0 - np.abs(x[i] / 2.0))
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
    def bandwidth(n, d=1):
        """
        Scott's factor for bandwidth estimation
        """
        return n ** (-1.0 / (d + 4.0))

    @staticmethod
    def halfquad(x):
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


class KDE(object):
    """
    Kernel density estimation.
    """

    def __init__(self, sample, h=1.0, kernel=Kernels.gauss):
        """
        **Parameters:**
            `sample` :
                1-dimensional random sample
            `h` :
                Relative smoothing parameter
            `kernel` :
                Smoothing kernel function

        **Returns:**
            Function of `x` that accepts numpy arrays.
        """
        self.sample = sample
        self.h = h
        self.kernel = kernel
        self.bandwidth = Kernels.bandwidth(len(sample))

    def __call__(self, x):
        hh = self.h * self.bandwidth
        y = np.zeros([x.size])
        for xi in self.sample:
            y += self.kernel((x - xi) / hh) / hh
        return y / len(self.sample)


class WeightedKDE(KDE):
    """
    Multiply a kernel density estimation with weights
    """

    def __init__(self, sample, weights, h=1.0,
            kernel=Kernels.gauss, normalize=True):
        """
        **Parameters:**
            `sample` :
                1-dimensional random sample
            `weights` :
                Array of values with which the kernels get multiplied
            `h` :
                Relative smoothing parameter
            `kernel` :
                Smoothing kernel function
            `normalize` :
                Specifies if the function should be normalized with
                ``1 / len(sample)``, as it is usual for a KDE.
                Set this to ``False`` if the weights already contain a
                normalization.

        **Returns:**
            Function of `x` that accepts numpy arrays.
        """
        super(WeightedKDE, self).__init__(sample, h, kernel)
        self.weights = weights
        self.normalize = normalize

    def __call__(self, x):
        hh = self.h * self.bandwidth
        y = np.zeros([x.size])
        for xi, w in zip(self.sample, self.weights):
            y += w * self.kernel((x - xi) / hh) / hh
        if self.normalize:
            y /= len(self.sample)
        return y


class FunctionKDE(KDE):
    """
    Multiply a function with kernel density estimation
    """

    def __init__(self, sample, func, h=1.0,
            kernel=Kernels.gauss, normalize=True):
        """
        **Parameters:**
            `sample` :
                1-dimensional random sample
            `func` :
                Callable that can work with numpy arrays
            `h` :
                Relative smoothing parameter
            `kernel` :
                Smoothing kernel function
            `normalize` :
                Specifies if the function should be normalized with
                ``1 / len(sample)``, as it is usual for a KDE.
                Set this to ``False`` if the function already contain a
                normalization.

        **Returns:**
            Function of `x` that accepts numpy arrays.
        """
        super(FunctionKDE, self).__init__(sample, h, kernel)
        self.func = func
        self.normalize = normalize

    def __call__(self, x):
        y = super(FunctionKDE, self).__call__(x)
        y *= self.func(x)
        if not self.normalize:
            y *= len(self.sample)
        return y


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
        cls.plotfunc(pdf, e1, e2, px, 2.0, "b--")
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
    #x = np.linspace(-3, 3, 200)
    #plt.plot(x, Kernels.gauss(x))
    #plt.plot(x, Kernels.compact(x))
    #plt.plot(x, Kernels.triang(x))
    #plt.plot(x, Kernels.quad(x))
    #plt.show()
