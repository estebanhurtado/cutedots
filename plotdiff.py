import numpy as np
import pylab as pl
import argparse
import h5py
import random
import scipy.stats as st
from impmean import average

BOOTN = 1000
BOOTTOP = 95
BOOTBOT = 5


def beautify(curves):
    return np.mean(curves,0)
    x = np.array(curves)
    n, l = x.shape
    model = np.mean(x, 0)
    for i in range(10):
        ss = np.sum((x - model) ** 2, 1)
        p = ss / np.sum(ss)
        model = np.zeros(l)
        for i in range(n):
            model += x[i] * p[i]
    return model

def bootmean(curves, N):
    n, l = curves.shape
#    print n
    idx = np.random.randint(0, n, N)
    newcurves = curves[idx]
    for i in range(N):
        nc = newcurves[i]
        newcurves[i] = np.roll(nc, np.random.randint(0, len(nc)))
    return beautify(newcurves)
#    return np.mean(newcurves,0)

def bootstrap(curves):
    n, l = curves.shape
    means = []
    for i in range(BOOTN):
        idx = np.random.randint(0, n, n)
        newcurves = curves[idx]
        for i in range(n):
            nc = newcurves[i]
#            newcurves[i] = np.roll(nc, np.random.randint(0, len(nc)))
        means.append(np.mean(newcurves,0))
    top = st.scoreatpercentile(means, BOOTTOP, axis=0)
    bot = st.scoreatpercentile(means, BOOTBOT, axis=0)
    avg = np.mean(means, 0)
    return bot, top, avg

def bootDiff(c1, c2):
    c = np.vstack((c1,c2))
    n1, n2 = c1.shape[0], c2.shape[0]
    means = [bootmean(c, n1) - bootmean(c, n2) for i in range(BOOTN)]
    top = st.scoreatpercentile(means, BOOTTOP, axis=0)
    bot = st.scoreatpercentile(means, BOOTBOT, axis=0)
    avg = np.mean(means, 0)
    return bot, top, avg

def plotDiff(t, curves, names):
    print curves.keys()
    colors = ['g','r']
    names.sort()
    n1, n2 = names
    colorIdx = 0
    c1 = np.array(curves[n1])
    c2 = np.array(curves[n2])
    c =  beautify(c1) - beautify(c2)
    pl.plot(t, c)

    bot, top, avg = bootDiff(c1, c2)
    pl.fill_between(t, bot, top, alpha=0.5)
    pl.plot(t, avg, linewidth=3)

#    bot, top, avg = bootstrap(c)
#    pl.fill_between(t, bot, top, color=colors[colorIdx % len(names)], alpha=0.5)
#    pl.plot(t, avg, colors[colorIdx % len(names)], linewidth=3, label=lab)
#    colorIdx += 1
    pl.xlabel("Delay (seconds)")
    pl.ylabel("Correlation difference")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--infile', default="curves.h5")
    parser.add_argument('--compare', nargs=2, required=True)
    args = parser.parse_args()

    with h5py.File(args.infile, 'r') as f:
        t = f['t']
        curves = f['curves']
        plotDiff(t, curves, args.compare)
        pl.show()
