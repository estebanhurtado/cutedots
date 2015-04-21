import os
import numpy as np
import dotsio as dio
import analysis as an
import pystats as stats
import pylab as pl

t = None

def corrOneFile(fn, timespan, method):
    global t
    td = dio.trajDataFromH5(fn)
    print("Processing file '%s'" % fn, end='')
    if method == 'log-energy':
        x1, x2 = an.logEnergyPairFromTrajData(td)
        c, t  = stats.fftCorrPair(x1, x2, timespan, td.framerate)
    else:
        c, t = stats.pcaCorrTrajData(td, timespan, td.framerate)
        c = np.abs(c)
    print (" [Ok]")
    if fn.find('p9a') == -1:
        return c[::-1]
    return c

def corrFiles(filelist, timespan, method):
    curves = [corrOneFile(fn, timespan, method) for fn in filelist]
    return np.mean(curves,0)

def corrFolder(root, timespan, method):
    datafiles = {}

    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.qtd'):
                key = dirpath[len(root):]
                fullfn = os.path.join(dirpath, fn)
                datafiles.setdefault(key, []).append(fullfn)

    curves = {}
    for k in datafiles:
        curves[k] = corrFiles(datafiles[k], timespan, method)

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
    args = parser.parse_args()

    curves = corrFolder(args.infolder, args.timespan, method=args.method)

    names = list(curves.keys())
    names.sort()

    for name in names:
        pl.plot(t, curves[name], label=name)
    pl.legend(loc='upper right')

    if args.display:
        pl.show()

