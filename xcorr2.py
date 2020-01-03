from __future__ import print_function
from xcorrfile import xcorrFile
import os
import numpy as np
from itertools import chain

def report(outfile, key, filenames, curves, samplerate):
    for fn, c in zip(filenames, curves):
        n = len(c)
        center = n/2
        fr100 = int(0.1 * samplerate + 0.5)
        fr1000 = int(samplerate + 0.5)
        t0 = np.mean(c[center - fr100 : center + fr100 + 1])
        lisIm = np.mean(c[center + fr100 + 1 :])
        spkIm = np.mean(c[: center - fr100])
        outfile.write("%s,%s,%f,%f,%f\n" % (fn, key, t0, lisIm, spkIm))

def corrFiles(key, filelist, timespan, wintime, outfile):
    curves = []
    for fn in filelist:
        t, c = xcorrFile(fn, timespan, wintime, args.plot)
        curves.append(c)
    report(outfile, key, filelist, curves, (len(t)-1) / float(timespan*2))
    return t, curves

def corrFolder(root, timespan, wintime):
    datafiles = {}

    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.qtd'):
                key = dirpath[len(root):]
                fullfn = os.path.join(dirpath, fn)
                subj = fn.split('-')[0]
                datafiles.setdefault(key, {}).setdefault(subj, []).append(fullfn)

    curves = {}
    with open(os.path.join(root, "data.csv"), "w") as outfile:
        outfile.write("file,key,t0,lisIm,spkIm\n")
        for k, subjs in datafiles.items():
            for subj, files in subjs.items():
                t, c = corrFiles(k, files, timespan, wintime, outfile)
                c = np.mean(c, 0)
                curves.setdefault(k, []).append(c)
    return t, curves

if __name__ == "__main__":
    import argparse
    import h5py

    parser = argparse.ArgumentParser()
    parser.add_argument('--infolder', required=True)
    parser.add_argument('--timespan', default=3.0, type=float)
    parser.add_argument('--wintime', default=4.0, type=float)
    parser.add_argument('--outfile', default="curves.h5")
    parser.add_argument('--plot', default=False, type=bool)
    args = parser.parse_args()

    with h5py.File(args.outfile, 'w') as f:
        t, curves = corrFolder(args.infolder, args.timespan, args.wintime)
        f.create_dataset('t', data=np.array(t))
        group = f.create_group('curves')
        for k in curves:
            print (k)
            group.create_dataset(k, data=np.array(curves[k]))

    print("Finished!") 
