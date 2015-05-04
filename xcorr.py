import os
import numpy as np
import dotsio as dio
import analysis as an
import pystats as stats
import pylab as pl
import random

t = None

def corrOneFile(fn, timespan, method, randomize=False):
    global t
    td = dio.trajDataFromH5(fn)
    print("Processing file '%s'" % fn, end='')
    if method == 'log-energy':
        x1, x2 = an.logEnergyPairFromTrajData(td)
        c, t  = stats.fftCorrPair(x1, x2, timespan, td.framerate, randomize)
    else:
        c, t = stats.pcaCorrTrajData(td, timespan, td.framerate, randomize)
        c = np.abs(c)
    print (" [Ok]")
    if fn.find('p9a') == -1:
        return c[::-1]
    return c

def corrFiles(filelist, timespan, method, randomize=False):
    curves = [corrOneFile(fn, timespan, method, randomize) for fn in filelist]
    return np.mean(curves,0)

def corrFolder(root, timespan, method, randomize=False):
    datafiles = {}

    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.qtd'):
                key = dirpath[len(root):]
                fullfn = os.path.join(dirpath, fn)
                datafiles.setdefault(key, []).append(fullfn)

    curves = {}
    for k in datafiles:
        if randomize:
            curves['boot'] = corrFiles(datafiles[k], timespan, method, randomize)
        else:
            curves[k] = corrFiles(datafiles[k], timespan, method, randomize)

    return curves


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="""
Computes cross correlation of log-energy curves
between two subjects of each couple in included
files. Then averages curves by subfolder in the
-10 to +10 second range.
""")
    parser.add_argument('--infolder', default="data")
    parser.add_argument('--method', default="pca", choices=['pca', 'log-energy'])
    parser.add_argument('--display', default=True)
    parser.add_argument('--timespan', default=10)
    parser.add_argument('--bootstrap', default=False)
    args = parser.parse_args()

    curves = corrFolder(args.infolder, args.timespan, args.method)
    print(curves)

    trialNum = 0

    def trial():
        global trialNum
        trialNum += 1
        print("BOOTSTRAP TRIAL %d" % trialNum)
        return corrFolder(args.infolder, args.timespan, args.method, True)

    boot = None

    if args.bootstrap:
        boot = [trial() for i in range(100)]

    # Plot
    names = list(curves.keys())
    colors = ['b','g','r','c','m','y','k'][:len(names)]

    names.sort()

    colorIdx = 0
    def makePlot(curves):
        global colorIdx
        for name in names:
            if name == 'boot':
                pl.plot(t, curves[name], 'k')
            else:
                pl.plot(t, curves[name], colors[colorIdx % len(names)], label=name)
            pl.xlabel("Delay (seconds)")
            pl.ylabel("Correlation in PCA space")
            print("%s: (t,r) = %f, %f" % (name, t[curves[name].argmax()], curves[name].max()))
            colorIdx += 1
    
    makePlot(curves)

    if args.bootstrap:
        names = ['boot']
        for curves in boot:
            makePlot(curves)

    pl.legend(loc='upper right')


        

    if args.display:
        pl.show()

