def corrFiles(key, filelist, timespan, wintime, outfile):
    results = [xcorrFile(fn, timespan, wintime) for fn in filelist]
    t = results[0][0]
    curves = [c for t,c in results]
    return np.mean(curves,0)


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
        outfile.write("file,key,peaktime,peak\n")
        for k in datafiles:
            curves[k] = corrFiles(k, datafiles[k], timespan, wintime, outfile)
    return curves


if __name__ == "__main__":
    import argparse
    import pylab as pl

    parser = argparse.ArgumentParser()
    parser.add_argument('--infolder', default="data")
    parser.add_argument('--timespan', default=10, type=float)
    parser.add_argument('--bootstrap', default=False)
    args = parser.parse_args()

    curves = xcorr(args.infolder, args.timespan, args.method, args.display, args.bootstrap)

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
