"""
Calculate pair distribution functions.
"""

__all__ = ["PDF"]


import math
import os.path
import sys

import numpy as np

from ..config.configuration import config
from ..core.calculation.discretization import DiscretizationCache
from ..util.logger import Logger

MINDISTANCE = 2.0  # shorter distances are ignored
PDFCUTOFF = 1.0  # g(r) = 0 if r < PDFCUTOFF


logger = Logger("statistics.pdf")
logger.setstream("default", sys.stdout, Logger.DEBUG)


class PDF(object):
    """
    Calculate pair distribution functions for atoms and cavities.
    """

    def __init__(self, *args):
        """
        Create a sample from atom and cavity positions and smooth them to
        get the PDFs

        The constructor can be called in two ways:

        - ``PDF(results)`` :
            retrieve the data from :class:`core.data.Results`

        - ``PDF(positions, elements, cavitycenters, volume)`` :
            use the given arrays and the volume object
        """
        if len(args) == 1:
            results = args[0]
            positions = results.atoms.positions
            elements = results.atoms.elements
            volume = results.atoms.volume
            if results.domains is not None:
                centers = results.domains.centers
                cachedir = os.path.expanduser(config.Path.cache_dir)
                cachepath = os.path.join(cachedir, "discretization_cache.hdf5")
                dcache = DiscretizationCache(cachepath)
                disc = dcache.get_discretization(volume, results.resolution)
                centers = list(map(disc.discrete_to_continuous, centers))
            else:
                centers = []
        elif len(args) == 4:
            positions, elements, centers, volume = args
        else:
            raise TypeError("PDF expects 1 or 4 parameters")

        self.positions = np.asarray(positions)
        self.elements = np.asarray(elements, dtype="|S4")
        self.centers = np.asarray(centers)
        self.volume = volume
        self.num_atoms = np.where(self.elements != "cav")[0].size
        self.numberdensity = float(self.num_atoms) / self.volume.volume

        self.stats = self._genstats(self.positions, self.elements, self.centers, self.volume)

    def pdf(self, elem1, elem2, cutoff=None, h=None, kernel=None):
        """
        Calculate a smoothed pair distribution function between the elements
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
            Python function that represents the pair distribution function.
            It also accepts Numpy arrays as input.
            Returns `None` if the given elements do not exist or if there is
            not enough data to create the function.
        """
        if kernel is None:
            # kernel = Kernels.epanechnikov
            kernel = Kernels.epanechnikov

        data = None
        for s in self.stats:
            if set((elem1.lower(), elem2.lower())) == set((s[0].lower(), s[1].lower())):
                data = s[2]
                break
        if data is None:
            logger.debug("No statistical data for '{}-{}' found.".format(elem1, elem2))
            raise Exception("No statistical data for '{}-{}' found.".format(elem1, elem2))

        if cutoff is None:
            cutoff = data.max()
        sel = np.where(np.logical_and(data > MINDISTANCE, data <= cutoff))[0]
        sel = data[sel]
        if h == 0:
            return sel
        if len(sel) < 2:
            logger.debug("Not enough data for '{}-{}' in cutoff={} range.".format(elem1, elem2, cutoff))
            raise Exception("Not enough data for '{}-{}' in cutoff={} range.".format(elem1, elem2, cutoff))

        if h is None:
            # magic constant
            # minimizes the first peak
            # h = min(0.5, 0.5772778 * sel.min())
            h = 0.4

        # if h > 0.9 * sel.min():
        #    logger.debug("Bandwidth {} above threshold. Setting to {}.".format(h, 0.9 * sel.min()))
        #    h = 0.9 * sel.min()
        kde = Functions.KDE(sel, h=h, kernel=kernel)

        def wfunc(r):
            y = np.zeros_like(r)
            i = np.where(np.abs(r) > PDFCUTOFF)[0]
            y[i] = self.volume.volume / (data.size * 4 * math.pi * r[i] ** 2)
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

            def distance(x, y):
                return np.abs(y - x)

        else:
            distance = volume.get_distance

        if pos2 is None:
            n = pos1.shape[0]
            if n < 2:
                return np.zeros(0)
            a1 = np.vstack([pos1[0:-i, :] for i in range(1, n)])
            a2 = np.vstack([pos1[i:, :] for i in range(1, n)])
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
        if len(centers) > 0 and "cav" not in elemlist:
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
        for i in range(len(elemlist)):
            try:
                elemlist[i] = elemlist[i].decode("utf-8")
            except AttributeError:
                pass
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

    class KDE(object):
        """
        Kernel density estimation. Calculate a convolution
        of delta pulses with a smoothing kernel.
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

        def __call__(self, p):
            result = np.zeros_like(p)
            if len(self.x) <= len(p):
                p = np.asarray(p)
                for xi, yi in zip(self.x, self.y):
                    result += yi * self.kernel((p - xi) / self.h) / self.h
            else:
                x = np.asarray(self.x)
                y = np.asarray(self.y)
                for i, pi in enumerate(p):
                    result[i] = np.sum(y * self.kernel((pi - x) / self.h) / self.h)

            return result

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
            y[i] = c * np.exp(1.0 / (x[i] ** 2 - 1.0))
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
            y[i] = 3.0 / 4.0 * (1.0 - x[i] ** 2)
            return y

    @staticmethod
    def bandwidth(n, d=1):
        """
        Scott's factor for bandwidth estimation
        """
        return (4.0 / 3.0 * n) ** (-1.0 / (d + 4.0))


class _TestPDF(object):
    @staticmethod
    def continuous_coordinates(coords, volume, resolution):
        cachedir = os.path.expanduser(config.Path.cache_dir)
        cachepath = os.path.join(cachedir, "discretization_cache.hdf5")
        dcache = DiscretizationCache(cachepath)
        disc = dcache.get_discretization(volume, resolution)

        return np.array(map(disc.discrete_to_continuous, coords))

    @staticmethod
    def plotfunc(pdf, e1, e2, px, h, *args):
        gr = pdf.pdf(e1, e2, h=h)
        plt.plot(px, gr(px), *args, label=str(h))
        py = gr(px)
        m = np.argmax(py)
        print("h={}, xi={}, g({}) = {}".format(gr.f.h, gr.f.x.min(), px[m], py[m]))

    @classmethod
    def plotpdf(cls, pdf, e1, e2):
        px = np.linspace(0, 2, 1000)
        plt.figure()
        cls.plotfunc(pdf, e1, e2, px, 0.25, "g--")
        cls.plotfunc(pdf, e1, e2, px, 0.5, "r-")
        # cls.plotfunc(pdf, e1, e2, px, 1.0, "b--")
        plt.legend(loc=0)
        plt.title("{}-{}".format(e1, e2))

    @classmethod
    def run(cls):
        from ..core import calculation

        calc = calculation.Calculation("../results")
        filename = "../xyz/structure_c.xyz"
        resolution = 64
        frame = 9
        # filename = "../xyz/GST_111_128_bulk.xyz"
        # resolution = 256
        # frame = 0
        settings = calculation.CalculationSettings({filename: [frame]}, resolution, True, False, False)
        print("calculating...")
        res = calc.calculate(settings)[0][0]
        print("generating statistics...")
        pdf = PDF(res)
        # centers = cls.continuous_coordinates(res.domains.centers,
        #                                     res.atoms.volume,
        #                                     res.resolution)
        # pdf = PDF(res.atoms.positions, res.atoms.elements,
        #                  centers, res.atoms.volume)

        print("plotting...")
        # cls.plotpdf(pdf, "Ge", "Ge")
        # cls.plotpdf(pdf, "Ge", "Te")
        cls.plotpdf(pdf, "cav", "cav")
        plt.show()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    _TestPDF.run()
    # x = np.linspace(-2, 2, 200)
    # plt.plot(x, Kernels.gauss(x))
    # plt.plot(x, Kernels.compact(x))
    # plt.plot(x, Kernels.triang(x))
    # plt.plot(x, Kernels.quad(x))
    # plt.plot(x, Kernels.epanechnikov(x))
    # plt.show()
