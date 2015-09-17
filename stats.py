import scipy as sp
import numpy as np
from scipy import linalg as la
import pylab as pl

class TrajSignal:
    """Similar to traj. But instead of a list of points, it's data member
    is a numpy array."""
    def __init__(self, name, beginFrame, data):
        self.name = name
        self.beginFrame = beginFrame
        self.data = data

    @property
    def numFrames(self):
        return np.shape(self.data)[0]

    @property
    def endFrame(self):
        return self.beginFrame + self.numFrames

    def indexForFrame(self, frameNum):
        return frameNum - self.beginFrame


    def slice(self, beginFrame, endFrame):
        beginIdx = self.indexForFrame(beginFrame)
        endIdx = self.indexForFrame(endFrame)
        ts = TrajSignal(self.name, beginFrame,
                        self.data[beginIdx:endIdx,...])
        return ts

    def __and__(self, other):
        "Returns the two signals sliced to the same range of their intersecting time"
        begin = max(self.beginFrame, other.beginFrame)
        end = min(self.endFrame, other.endFrame)
        selfSlice = self.slice(begin, end)
        otherSlice = self.slice(begin, end)
        return (selfSlice, otherSlice)


def speeds(trajdata):
    results = []
    for t in trajdata.trajs:
        x = t.pointData
        speed = np.sum(np.subtract(x[1:], x[:-1])**2,1)**0.5
        results.append(TrajSignal(t.name, t.beginFrame, speed))
    return results
        
def covMat(tsigs):
    N = len(tsigs)
    m = np.zeros((N,N))
    for i in range(N):
        for j in range(N):
            a,b = tsigs[i] & tsigs[j]
            c = np.cov(a.data,b.data)
            m[i,j] = c[0,1]
            m[j,i] = c[1,0]
            m[i,i] = c[0,0]
            m[j,j] = c[1,1]
    return m

def pca(trajdata):
    spd = speeds(trajdata)
    cm = covMat(spd)
    names = [t.name for t in spd]
    header = ",".join(names)
    np.savetxt("cov.csv", cm, delimiter=",", header=header)
    eigval, eigvec = la.eigh(cm)
    idx = np.argsort(eigval)[::-1]
    eigval = eigval[idx]
    eigvec = eigvec[idx]

    eye = np.eye(trajdata.numTrajs)
    dirs = np.dot(eigvec[:2,:],eye)

    names = np.array([t.name for t in trajdata.trajs])
    names = names[idx]

    numDirs = np.shape(dirs)[1]
    pl.figure()
    ax = pl.gca()
    for i in range(numDirs):
        pl.text(dirs[0,i], dirs[1,i], names[i])


    pl.draw()
    pl.show()

    
