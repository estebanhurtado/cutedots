import os
import numpy as np
import dotsio as dio
import analysis as an
import pystats as stats
import pylab as pl

t = None

def logEnergyCorrOneFile(fn, timespan):
    global t
    td = dio.trajDataFromH5(fn)
    e1, e2 = an.logEnergyPairFromTrajData(td)
    c, t  = stats.fftCorrPair(e1, e2, timespan, td.framerate)
    return c

def logEnergyCorrFiles(filelist, timespan):
    curves = [logEnergyCorrOneFile(fn, timespan) for fn in filelist]
    return np.mean(curves,0)

def logEnergyCorrFolder(root, timespan):
    datafiles = {}

    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.qtd'):
                key = dirpath[len(root):]
                fullfn = os.path.join(dirpath, fn)
                datafiles.setdefault(key, []).append(fn)

    curves = {}
    for k in datafiles:
        curves[k] = logEnergyCorrFiles(datafiles[k], timespan)

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
    parser.add_argument('--display', default=True)
    parser.add_argument('--timespan', default=10)
    args = parser.parse_args()

    curves = logEnergyCorr(args.infolder, args.timespan)


    for name, curve in curves.items():
        pl.plot(t, curve, label=name)
    pl.legend(loc='upper right')

    if args.display:
        pl.show()

