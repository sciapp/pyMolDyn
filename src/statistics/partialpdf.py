# -*- coding: utf-8 -*-


import numpy as np
import scipy as sp
from scipy import stats
import matplotlib.pyplot as plt


def createstats(pos1, pos2=None):
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
    

def plotstep(x, y, colors='b'):
    plt.hlines(y[:-1], x[:-1], x[1:], colors=colors)
    plt.xlim((x[0], x[-1]))
    plt.ylim((y.min(), y.max()))

def plotpde(samples, **kwargs):
    xval = np.hstack((0.0, samples))
    yval = np.linspace(0, 1, xval.size)
    #d = (yval[1:] - yval[:-1]) / (xval[1:] - xval[:-1])

    kde = sp.stats.gaussian_kde(samples)
    kx = np.linspace(0, samples.max(), 200)
    ky = kde(kx)
    iy = sp.integrate.cumtrapz(ky, kx)

    plt.figure()
    plt.plot(kx, ky, "r", **kwargs)
    #plt.figure()
    #plotstep(xval, yval)
    #plt.plot(kx, iy, "r", **kwargs)


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

    stats = []
    for i, e1 in enumerate(elements):
        for j in range(i, len(elements)):
            e2 = elements[j]
            if i == j:
                s = createstats(positions[i])
            else:
                s = createstats(positions[i], positions[j])
            stats.append((e1, e2, s))
            print (e1, e2), (positions[i].shape[0], positions[j].shape[0]), s.size

    for e1, e2, s in stats:
        if s.size > 1:
            plotpde(s)
            plt.title(e1 + " - " + e2)
    plt.show()


def test():
    class TestAtoms:
        def __init__(self, e, p):
            self.elements = e
            self.positions = p

    e = np.array(["Te", "Ge", "Ge", "Sb", "Ge", "Te"])
    p = np.arange(e.size * 3, dtype=float).reshape(-1, 3)
    a = TestAtoms(e, p)
    cc = np.array([[6, 5, 4], [3, 2, 1]], dtype=float)
    print e
    print p
    print cc
    print

    partialpdf(a, cc)


if __name__ == "__main__":
    test()

