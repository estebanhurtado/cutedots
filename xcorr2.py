from __future__ import print_function
from xcorrfile import xcorrFile
import os
import numpy as np

def report(outfile, key, filenames, curves, samplerate):
    for fn, c in zip(filenames, curves):
        n = len(c)
        center = n/2
        fr100 = int(0.1 * samplerate + 0.5)
        print("FR100 =", fr100)
        t0 = np.mean(c[center - fr100 : center + fr100 + 1])
        lisIm = np.mean(c[center + fr100 + 1 :])
        spkIm = np.mean(c[:center - fr100])
        outfile.write("%s,%s,%f,%f,%f\n" % (fn, key, t0, lisIm, spkIm))

def corrFiles(key, filelist, timespan, wintime, outfile):
    results = [xcorrFile(fn, timespan, wintime) for fn in filelist]
    t = results[0][0]
    curves = [c for t,c in results]
    report(outfile, key, filelist, curves, (len(t)-1) / float(timespan*2))
    c = np.mean(curves, 0)
    return t, c

def corrFolder(root, timespan, wintime):
    datafiles = {}

    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.qtd'):
                key = dirpath[len(root):]
                fullfn = os.path.join(dirpath, fn)
                datafiles.setdefault(key, []).append(fullfn)

    curves = {}
    with open(os.path.join(root, "data.csv"), "w") as outfile:
        outfile.write("file,key,t0,lisIm,spkIm\n")
        for k in datafiles:
            t, curves[k] = corrFiles(k, datafiles[k], timespan, wintime, outfile)
    return t, curves

def plotCurves(t, curves):
    names = list(curves.keys())
    colors = ['b','g','r','c','m','y','k'][:len(names)]
    names.sort()
    colorIdx = 0
    for name in names:
        lab = name.strip("\/")
        pl.plot(t, curves[name], colors[colorIdx % len(names)], label=lab)
        pl.xlabel("Delay (seconds)")
        pl.ylabel("Correlation")
        colorIdx += 1

if __name__ == "__main__":
    import argparse
    import pylab as pl

    parser = argparse.ArgumentParser()
    parser.add_argument('--infolder', required=True)
    parser.add_argument('--timespan', default=3.0, type=float)
    parser.add_argument('--wintime', default=4.0, type=float)
    args = parser.parse_args()

    t, curves = corrFolder(args.infolder, args.timespan, args.wintime)
    plotCurves(t, curves)
    pl.legend(loc='upper right')
    pl.show()