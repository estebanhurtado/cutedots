import os
import numpy as np
import dotsio as dio
import analysis as an
import pystats as stats
import pylab as pl
import random
import sys
import time
import transform
import segmentation as seg
import traceback

t = None

def corrOneFile(fn, timespan, method, randomize=False):
    global t

    try:
        td = dio.trajDataFromH5(fn)
    except:
        print("*** Warning: could not open '%s'" % fn)

    try:
        print("Processing file '%s'" % fn, end='')
        if method == 'log-energy':
            x1, x2 = an.logEnergyPairFromTrajData(td)
            c, t  = stats.fftCorrPair(x1, x2, timespan, td.framerate, randomize)
        elif method == 'pca':
            c, t = stats.pcaCorrTrajData(td, timespan, td.framerate, randomize)
            c = np.abs(c)
            

        if (len(c)/td.framerate) < (2*timespan):
            print("\n\t*** Recording too short. Must be at least %.3f seconds." % (2*timespan))
            return None

        print (" [Ok]")

        peak = c.max()
        peaktime = (c.argmax() / td.framerate) - timespan
        time.sleep(0)
        return fn, c, peak, peaktime, td.numFrames
    except:
        print("\n\t*** Error processing file.")
        traceback.print_exc(file=sys.stdout)

def corrFiles(key, filelist, timespan, method, outfile, randomize=False):
    curves = [corrOneFile(fn, timespan, method, randomize) for fn in filelist]

    curves = [x for x in curves if (not x is None)]
    for fn, c, peak, peaktime, length in curves:
        outfile.write("%s,%s,%f, %f\n" % (fn, key, peaktime, peak))
    totalFrames = sum(x[4] for x in curves)
    curves = [x[1] * float(x[4])/totalFrames for x in curves]
    
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
    with open(os.path.join(root, "data.csv"), "w") as outfile:
        outfile.write("file,key,peaktime,peak\n")
        for k in datafiles:
            if randomize:
                curves['boot'] = corrFiles(k, datafiles[k], timespan, method, outfile, randomize)
            else:
                curves[k] = corrFiles(k, datafiles[k], timespan, method, outfile, randomize)

    return curves

colorIdx=0

def xcorr(infolder, timespan, method, display, bootstrap):
    global colorIdx
    curves = corrFolder(infolder, timespan, method)

    trialNum = 0

    def trial():
        global trialNum
        trialNum += 1
        print("BOOTSTRAP TRIAL %d" % trialNum)
        return corrFolder(infolder, timespan, method, True)

    boot = None

    if bootstrap:
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
                lab = name.strip("\/")
                pl.plot(t, curves[name], colors[colorIdx % len(names)], label=lab)
            pl.xlabel("Delay (seconds)")
            pl.ylabel("Correlation in PCA space")
#            print("%s: (t,r) = %f, %f" % (name, t[curves[name].argmax()], curves[name].max()))
            colorIdx += 1

    makePlot(curves)

    if bootstrap:
        names = ['boot']
        for curves in boot:
            makePlot(curves)

    pl.legend(loc='upper right')

    if display:
        pl.show()


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
    parser.add_argument('--timespan', default=10, type=float)
    parser.add_argument('--bootstrap', default=False)
    args = parser.parse_args()

    import cProfile
    cProfile.run("xcorr(args.infolder, args.timespan, args.method, args.display, args.bootstrap)", sort='cumulative')
