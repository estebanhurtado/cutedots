from xcorr import CorrCurves
import pickle
import pylab as pl
import os
import random
import numpy as np
import numpy.ma as ma
from scipy.stats import scoreatpercentile

styles = ['b', 'r', 'y', 'g', 'k']
stylen = 0


def resample(curves):
    n = len(curves)
    newSample = []
    for c in curves:
        targetDof = c.dof['avg']
        randCurve = curves[random.randint(0, n-1)]
        sourceDof = randCurve.dof['avg']
        newCurve = CorrCurves(frameRate = randCurve.frameRate)
        def scale(seq):
            return (seq / sourceDof) * targetDof
        newCurve.sab['avg'] = scale(randCurve.sab['avg'])
        newCurve.ssa['avg'] = scale(randCurve.ssa['avg'])
        newCurve.ssb['avg'] = scale(randCurve.ssb['avg'])
        newCurve.dof['avg'] = targetDof
        newSample.append(newCurve)
    return newSample

def resample1(curves):
    n = len(curves)
    newSample = []
    def dof(curve):
        return curve.dof['avg']
    currentDof = np.zeros(dof(curves[0]).shape, int)
    totalDof = np.sum([dof(c) for c in curves], 0)

    while True:
        new = curves[random.randint(0, n-1)]
        newDof = dof(new)
        futureDof = currentDof + newDof
        if np.all(futureDof == totalDof):
            newSample.append(new)
            break
        elif np.any(futureDof > totalDof):
            newSample.append(new)
            break
        else:
            newSample.append(new)
        currentDof = futureDof
    return newSample

def bootstrap(curves, bootn):
    bootCurves = []
    for i in range(bootn):
        r = resample(curves)
        avg = averageCurves(r)
        bootCurves.append(avg.calcForName('avg'))
    bootCurves = np.array(bootCurves)
    length = bootCurves.shape[1]
#    top = np.max(bootCurves, 0)
#    bottom = np.min(bootCurves, 0)
    top = [scoreatpercentile(bootCurves[:,i], 97.5) for i in range(length)]
    bottom = [scoreatpercentile(bootCurves[:,i], 2.5) for i in range(length)]
    return top, bottom

def averageCurves(curves):
    return CorrCurves.average(curves)
    #return avg.averageParts()

def ic(curve, dof):
    z = np.arctanh(curve)
    std = 1.0 / np.sqrt(dof-2)
    zc = 3.0308053371488461
    top = z + zc*std
    bottom = z - zc*std
    return np.tanh(top), np.tanh(bottom)

def curvesdata(curves, bootn, name):
    avg = averageCurves(curves)
    fr = avg.frameRate
    avg = avg.calcForName('avg')
    n = len(avg)
    t = (np.arange(n) - n/2) * 0.1
    dof = np.sum([c.dof['avg'] for c in curves], 0)
    top, bottom = ic(avg, dof)

    return name, t, avg, top, bottom 

def plotCurves(c1, c2):
    name1, t, avg1, top1, bottom1 = c1
    name2, t, avg2, top2, bottom2 = c2
    pl.plot(t, np.zeros(len(t)), 'k-')
    s1 = ma.array(avg1)
    s2 = ma.array(avg2)
    zx1 = np.logical_and(np.greater_equal(top1, 0), np.less_equal(bottom1, 0))
    zx2 = np.logical_and(np.greater_equal(top2, 0), np.less_equal(bottom2, 0))
    ix = np.logical_or(
            np.logical_and(
                np.greater_equal(top1, top2),
                np.less_equal(bottom1, top2)),
            np.logical_and(
                np.greater_equal(top1, bottom2),
                np.less_equal(bottom1, bottom2)))
    mask1 = np.logical_or(zx1, ix)
    mask2 = np.logical_or(zx2, ix)

    print mask1
    print mask2
    print zx1
    print zx2
    print ix

    pl.plot(t, s1, "k--", linewidth=1)
    pl.plot(t, s2, "k-", linewidth=1)
    s1.mask = ix
    s2.mask = ix
    pl.plot(t, s1, "k--", linewidth=3, label=name1)
    pl.plot(t, s2, "k-", linewidth=3, label=name2)
    pl.xlabel('Time (secs)')
    pl.ylabel("Pearson correlation")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ylim', nargs=2, type=float, default=None)
    parser.add_argument('--bootn', default=1000, type=int)
    parser.add_argument('--title', default="Cross-correlation")
    parser.add_argument('infiles', nargs=2)
    args = parser.parse_args()

    plotdata = []
    all = []
    for fn in args.infiles:
        name, ext = os.path.splitext(fn)
        with open(fn, "rb") as f:
            curves = [c.averageParts() for c in pickle.load(f)]
            all.extend(curves)
            for c in curves:
                c.printStats()
            plotdata.append(curvesdata(curves, args.bootn, name))
    plotCurves(plotdata[0], plotdata[1])


    if args.ylim is not None:
        pl.ylim(*(args.ylim))

    pl.title(args.title)
    pl.legend()
    pl.show()
