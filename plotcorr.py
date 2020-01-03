import numpy as np
import pylab as pl
import argparse
import h5py
import random
import scipy.stats as st
from impmean import average

BOOTN = 1000
BOOTTOP = 55
BOOTBOT = 45

def boot(x):
    n = len(x)
    means = []
    for i in range(BOOTN):
        sample = x[np.random.randint(0, n, n)]
        means.append(np.mean(sample))
    top = st.scoreatpercentile(means, BOOTTOP)
    bot = st.scoreatpercentile(means, BOOTBOT)
    return [bot, top]

def boot2(curves):
    n, l = curves.shape
    cols = []
    for col in range(l):
        cols.append(boot(curves[:, col]))
    cols = np.array(cols)
    return [cols[:,0], cols[:,1]]

def bootstrap(curves):
    n, l = curves.shape
    means = []
    for i in range(BOOTN):
        idx = np.random.randint(0, n, n)
        newcurves = curves[idx]
#        for i in range(n):
#            nc = newcurves[i]
#            newcurves[i] = np.roll(nc, np.random.randint(0, len(nc)))
        means.append(np.mean(newcurves,0))
    top = st.scoreatpercentile(means, BOOTTOP, axis=0)
    bot = st.scoreatpercentile(means, BOOTBOT, axis=0)
    avg = np.mean(means, 0)
    return bot, top, avg

def plotCurves(t, curves, boot=True):
    names = list(curves.keys())
    colors = ['g','r','b','c','m','y','k'][:len(names)]
    names.sort()
    colorIdx = 0
    for name in names:
        lab = name.strip("\/")
        c = np.array(curves[name])
        bot, top, avg = bootstrap(c)
        if boot:
            pl.fill_between(t, bot, top, color=colors[colorIdx % len(names)], alpha=0.5)
        pl.plot(t, avg, colors[colorIdx % len(names)], linewidth=3, label=lab)
        colorIdx += 1
    pl.xlabel("Delay (seconds)")
    pl.ylabel("Correlation")
    pl.legend(loc='upper right')

#     if len(names) == 27:
#         curves = [np.array(curves[name]) for name in names]
#         N = [c.shape[0] for c in curves]
#         l = len(t)
#         all = np.vstack(curves).flatten()
#         diffs = []
#         for i in range(BOOTN):
#             A = np.random.choice(all, (N[0], l))
#             B = np.random.choice(all, (N[1], l))
#             diffs.append( np.mean(A,0) - np.mean(B,0) )
#         top = st.scoreatpercentile(diffs, 97.5, axis=0)
#         bot = st.scoreatpercentile(diffs, 2.5, axis=0)
#         pl.plot(t, top, 'k-')
#         pl.plot(t, bot, 'k-')

parser = argparse.ArgumentParser()
parser.add_argument('--infile', default="curves.h5")
parser.add_argument('--no-boot', action='store_true')
args = parser.parse_args()

with h5py.File(args.infile, 'r') as f:
    t = f['t']
    curves = f['curves']
    plotCurves(t, curves, not args.no_boot)

pl.show()
