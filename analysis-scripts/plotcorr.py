from xcorr import CorrCurves
import pickle
import pylab as pl
import os
import random
import numpy as np
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

def plotCurves(curves, bootn, name):
    global stylen
    style = styles[stylen]
    stylen = (stylen + 1) % len(styles)
    avg = averageCurves(curves)
    fr = avg.frameRate
    avg = avg.calcForName('avg')
    n = len(avg)
    t = (np.arange(n) - n/2) * 0.1
    pl.plot(t, np.zeros(len(t)), 'k-')
    #top, bottom = bootstrap(curves, bootn)
    dof = np.sum([c.dof['avg'] for c in curves], 0)
    top, bottom = ic(avg, dof)
    pl.fill_between(t, top, bottom, facecolor=style, label=name)
    pl.xlabel('Time (secs)')
    pl.ylabel("Pearson correlation")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ylim', nargs=2, type=float, default=None)
    parser.add_argument('--bootn', default=1000, type=int)
    parser.add_argument('--title', default="Cross-correlation")
    parser.add_argument('infiles', nargs='+')
    args = parser.parse_args()

    all = []
    for fn in args.infiles:
        name, ext = os.path.splitext(fn)
        with open(fn, "rb") as f:
            curves = [c.averageParts() for c in pickle.load(f)]
            all.extend(curves)
            for c in curves:
                c.printStats()

            plotCurves(curves, args.bootn, name)

 #   plotCurves(all, args.bootn, 'all')

    if args.ylim is not None:
        pl.ylim(*(args.ylim))

    pl.title(args.title)
    pl.legend()
    pl.show()
