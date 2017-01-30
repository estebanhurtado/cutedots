from __future__ import print_function
import h5py
import numpy as np
import pylab as pl
import copy
from scipy.stats import t as tDist

class MotionData:
    def __init__(self, data={}, frameRate=100):
        self.data = data
        self.frameRate = frameRate

    def readFromH5(self, fn):
        with h5py.File(fn, 'r') as f:
            trajs = f["trajectories"]
            if not 'frame_rate' in trajs.attrs:
                print("Warning, no framerate specified in file. Default to 100.")
            else:
                self.frameRate = trajs.attrs['frame_rate']
            self.data = {}
            for trName in list(trajs):
                tr = trajs[trName]
                bframe = tr.attrs['begin_frame']
                if bframe != 0:
                    print("Error. Trajectory", trName, "begins at frame", tr.attrs['bframe'])
                    return None
                self.data[tr.attrs['name']] = np.array(tr)
            trajLen = None
            for name, traj in self.data.iteritems():
                if trajLen is None:
                    trajLen = traj.shape[0]
                else:
                    if trajLen != traj.shape[0]:
                        print("Error. Trajectory", trName, "has unequal length.")

    @staticmethod
    def fromH5(fn):
        print(fn)
        md = MotionData()
        md.readFromH5(fn)
        return md

    def diff(self):
        md = MotionData(self.data, self.frameRate)
        for name, traj in self.data.iteritems():
            md.data[name] = traj[1:] - traj[:-1]
        return md

    def avgHeads(self):
        d = {}
        heads = {}
        for name, traj in self.data.iteritems():
            if name[:2] == 'Hd':
                k = 'Hd_' + name[3]
                heads.setdefault(k, []).append(traj)
            else:
                d[name] = traj
                
        for headName, trajs in heads.iteritems():
            d[headName] = np.mean(trajs, 0)
        self.data = d

    def avgAll(self, newName):
        p = []
        for name, traj in self.data.iteritems():
            print ("NAME:", name)
            p.append(traj)
        d = {newName: np.mean(p, 0)}
        self.data = d

    def scale(self, sc):
        for name, traj in self.data.iteritems():
            self.data[name] *= sc

    def splitBySubj(self):
        subjs = {}
        for name, traj in self.data.iteritems():
            subject = name[3]
            if not subject in subjs:
                subjs[subject] = MotionData({}, self.frameRate)
            subjs[subject].data[name[:3]] = traj
        return subjs['1'], subjs['2']

    def filterParts(self, names):
        md = MotionData({}, self.frameRate)
        for name, traj in self.data.iteritems():
            for n in names:
                if name.startswith(n):
                    md.data[name] = traj
        return md


class CorrCurves:
    def __init__(self, sab={}, ssa={}, ssb={}, dof={}, frameRate=100):
        self.sab = copy.deepcopy(sab)
        self.ssa = copy.deepcopy(ssa)
        self.ssb = copy.deepcopy(ssb)
        self.dof = copy.deepcopy(dof)
        self.frameRate = frameRate

    def clone(self):
        return CorrCurves(self.sab, self.ssa, self.ssb, self.dof, self.frameRate)

    def __add__(self, cc):
        assert self.frameRate == cc.frameRate
        sab = copy.deepcopy(self.sab)
        ssa = copy.deepcopy(self.ssa)
        ssb = copy.deepcopy(self.ssb)
        dof = copy.deepcopy(self.dof)
        for name in cc.sab:
            if name in sab:
                sab[name] += cc.sab[name]
                ssa[name] += cc.ssa[name]
                ssb[name] += cc.ssb[name]
                dof[name] += cc.dof[name]
            else:
                sab[name] = cc.sab[name][:]
                ssa[name] = cc.ssa[name][:]
                ssb[name] = cc.ssb[name][:]
                dof[name] = dof.ss[name][:]
        return CorrCurves(sab, ssa, ssb, dof, self.frameRate)

    @staticmethod
    def average(ccList):
        sab = copy.deepcopy(ccList[0].sab)
        ssa = copy.deepcopy(ccList[0].ssa)
        ssb = copy.deepcopy(ccList[0].ssb)
        dof = copy.deepcopy(ccList[0].dof)
        fr = ccList[0].frameRate

        for cc in ccList[1:]:
            assert cc.frameRate == fr
            for name in cc.sab:
                if name in sab:
                    sab[name] += cc.sab[name]
                    ssa[name] += cc.ssa[name]
                    ssb[name] += cc.ssb[name]
                    dof[name] += cc.dof[name]
                else:
                    sab[name] = cc.sab[name][:]
                    ssa[name] = cc.ssa[name][:]
                    ssb[name] = cc.ssb[name][:]
                    dof[name] = cc.dof[name][:]
        return CorrCurves(sab, ssa, ssb, dof, fr)


    @staticmethod
    def fromMotionData(md, scale, span=20, step=12):
        md.avgHeads()
        speed = md.diff()
        s1, s2 = md.splitBySubj()
        s2.scale(scale)
        return CorrCurves.fromTwoMd(s1, s2, span, step)
    
    @staticmethod
    def fromTwoMd(md1, md2, span=20, step=12):
       # md1.frameRate = 120
        #md2.frameRate = 120
        assert md1.frameRate == md2.frameRate
        print ("Framerate:", md1.frameRate)
        print ("Step:", step)
        md1.avgAll('UBL')
        md2.avgAll('UBL')
        cc = CorrCurves(frameRate=md1.frameRate / step)
        for name in md1.data:
            if name in md2.data:
                cc.sab[name], cc.ssa[name], cc.ssb[name], cc.dof[name] = \
                    CorrCurves.xcorrPair(md1.data[name], md2.data[name], span=20, step=step)
        return cc

    @staticmethod
    def xcorrPair(sig1, sig2, span=20, step=12):
        corrLen = 2 * span + 1
        sab = np.zeros(corrLen, dtype=float)
        ssa = np.zeros(corrLen, dtype=float)
        ssb = np.zeros(corrLen, dtype=float)
        dof = np.zeros(corrLen, dtype=int)
        for t in range(1, span+1):
            i = span - t
            sab[i], ssa[i], ssb[i], dof[i] = CorrCurves.singleCorr(sig1[t*step:], sig2[:-t*step])
            i = span + t
            sab[i], ssa[i], ssb[i], dof[i] = CorrCurves.singleCorr(sig1[:-t*step], sig2[t*step:])
        sab[span], ssa[span], ssb[span], dof[span] = CorrCurves.singleCorr(sig1, sig2)
        return sab, ssa, ssb, dof

    @staticmethod
    def singleCorr(sig1, sig2, permutation=False):
        n = len(sig1)
        c1 = sig1 - np.mean(sig1, 0)
        c2 = sig2 - np.mean(sig2, 0)
        if permutation:
            idx = np.arange(c2.shape[0])
            np.random.shuffle(idx)
            c2 = c2[idx]
        sab = np.sum(c1*c2)
        ssa = np.sum(c1**2)
        ssb = np.sum(c2**2)
        try:
            dof = globDof*(n-1)
        except:
            dof = 3000
        return sab, ssa, ssb, dof

    def averageParts(self, name="avg"):
        sab = np.sum(self.sab.values(), 0)
        ssa = np.sum(self.ssa.values(), 0)
        ssb = np.sum(self.ssb.values(), 0)
        dof = np.sum(self.dof.values(), 0)
        return CorrCurves({name:sab}, {name:ssa}, {name:ssb}, {name:dof}, self.frameRate)

    @staticmethod
    def calc(sab, ssa, ssb):
        return sab / (np.sqrt(ssa) * np.sqrt(ssb))

    def calcForName(self, name):
        return CorrCurves.calc(self.sab[name], self.ssa[name], self.ssb[name])

    def plot(self, step=12):
        dy = 0
        for name, sab in self.sab.iteritems():
            ssa = self.ssa[name]
            ssb = self.ssb[name]
            c = CorrCurves.calc(sab, ssa, ssb)
            t = np.linspace(0, step*len(c), len(c))
            t -= np.mean(t)
            pl.plot(t, c, 'm', linewidth=2, label=name)

    @staticmethod
    def bonferroni(p, alpha=0.05):
        n = len(p)
        newP = np.ones(n)
        idx = np.argsort(p)
        for i in range(n):
            loc = idx[i]
            newP[loc] = (n-i) * p[loc]
        return newP 

    def pVal(self):
        p = {}
        for name, sab in self.sab.iteritems():
            ssa = self.ssa[name]
            ssb = self.ssb[name]
            dof = self.dof[name]
            r = CorrCurves.calc(sab, ssa, ssb)
            df = dof - 1
            t = r * np.sqrt(df/(1-r**2))
            rawP = tDist.sf(np.abs(t), df)
            p[name] = CorrCurves.bonferroni(rawP)
            
        return p

    def plotP(self):
        pVals = self.pVal()
        for name, p in pVals.iteritems():
            pl.plot(p, label=name)
            print(np.sum(p<0.05) / float(len(p)))

    def printStats(self):
        for name in self.sab:
            x = self.calcForName(name)
            print(name, "mean:", np.mean(x), "\tstd:", np.std(x))

def corrFile(fn, filter, scale, framerate):
    md = MotionData.fromH5(fn)
    md.frameRate = framerate
    md = md.filterParts(filter)
    cc = CorrCurves.fromMotionData(md, scale, step=framerate/10)
    return cc

if __name__ == "__main__":

    import argparse
    import os
    import pickle

    parser = argparse.ArgumentParser()
    parser.add_argument('--infolder', required=True)
    parser.add_argument('--outfile', required=True)
    parser.add_argument('--scale', nargs=3, type=float, default=[-1.0, -1.0, 1.0])
    parser.add_argument('--dof', type=int, default = 3)
    parser.add_argument('--framerate', type=int, default=120)
    args = parser.parse_args()
    globDof = args.dof

    filter = ['UB', 'LB']
    curveList = []
    for dirpath, dirnames, filenames in os.walk(args.infolder):
        for fn in filenames:
            if fn.endswith('.qtd'):
                print(fn)
                filePath = os.path.join(args.infolder, fn)
                curveList.append(corrFile(filePath, filter, args.scale, args.framerate))


    with open(args.outfile, "wb") as f:
        pickle.dump(curveList, f)

#    avg = CorrCurves.average(curveList)
#    avg = avg.averageParts()
#    avg.plot()
#    avg.plotP()
#    pl.legend()
#    pl.show()

    print("Finished!")
