from __future__ import print_function
import dotsio as dio
import analysis
import pylab as pl
import numpy as np
import scipy.signal as sig
import transform
import scipy.stats as st

def plotEnergy(e1, e2):
    pl.subplot(3,1,1)
    pl.plot(e1)
    pl.subplot(3,1,2)
    pl.plot(e2)

def xcorrPair2(e1, e2, framespan, winsize):
    x2 = e2[framespan:-framespan]
    c = sig.fftconvolve(e1, x2, 'valid')
    return c

def xcorrPair(e1, e2, M, W):
    N = len(e1)
    framesize = W + 2*M
    result = []
    n = N - framesize + 1
    for i in range(n):
        x2 = e2[i : i+framesize]
        x1 = e1[i+M : i+framesize-M] 
        c = sig.fftconvolve(x2, x1[::-1], 'valid')
        result.append(c)
    return np.mean(result, 0)

def xcorrFile(fn, timespan, wintime, doPlot=False):
    print(fn)
    td = dio.trajDataFromH5(fn)
    newTd = td.clone()
    transform.LpFilterTrajData(newTd, 10.0)
    e1, e2 = [x for x in analysis.energyPairFromTrajData(newTd)]
    fr = td.framerate
    W = int(wintime * fr + 0.5)
    M = int(timespan * fr + 0.5)
    c = xcorrPair(e1, e2, M, W)
    center = len(c)/2
    t, corr = np.linspace(-timespan, timespan, len(c)), c[center-M:center+M+1]
    if doPlot:
        print(corr)
        pl.plot(t, corr)
        pl.title(fn)
        pl.show()
    return t, corr


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--infile')
    parser.add_argument('--timespan', default=3.0, type=float)
    parser.add_argument('--wintime', default=4.0, type=float)
    args = parser.parse_args()

    t, c = xcorrFile(args.infile, args.timespan, args.wintime)
    pl.plot(t, c)
    pl.show()
