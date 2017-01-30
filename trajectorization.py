from trajdata import *
import scipy.spatial.distance as spd
import numpy as np
from PySide import QtCore

def metricEuclidean(gap):
    def metric(a,b):
        return np.sum((np.array(b.pointData[0]) - np.array(a.pointData[-1]))**2)**0.5
    return metric

def metricEuclideanPredict(gap):
    def metric(a,b):
        pa = np.array(a.predict( (-1.+gap)/2 ))
        pb = np.array(b.backPredict( (-1.-gap)/2 ))
        return float(np.sum((pb-pa)**2)**0.5)
    return metric


class Trajectorizer:

    def __init__(self, rdata, progress=None):
        self.rdata = rdata
        self.progress = progress
        self.trajs = []
        self.distanceThreshold = 10

    def match(self, maxGap=3, minGap=0):
        for i in range(minGap, maxGap+1):
            metric = metricEuclidean(0)
            self.matchAdjacentTrajs(metric)
            metric = metricEuclideanPredict(0)
            self.matchAdjacentTrajs(metric)

    def trajectorize(self, maxGap=3):
        print("Trajectorization")
        print("- Distance based trajectorization...")
        self.distanceTraj()
        print("- Matching adjacent trajectories...")
        self.match(maxGap)
        print("Done")

    def noTraj(self):
        trajs = []
        for fr in range(self.rdata.numFrames):
            trajs.extend([Traj.newFromPoint(p,fr) for p in self.rdata[fr].data])
        self.trajs = trajs

    @staticmethod
    def findMatches(distances, threshold):
        matches = []
        for row in range(distances.shape[0]):
            i, j = np.unravel_index(distances.argmin(), distances.shape)
            if distances[i,j] > threshold:
                return matches
            matches.append((i,j))
            distances[i,:] = threshold + 1
            distances[:,j] = threshold + 1
        return matches

    def distanceTraj(self):
        if not (self.progress is None):
            self.progress.setValue(0)
            self.progress.setLabelText("Distance based trajectorization")
            self.progress.show()

        numPoints = sum([p.numPoints for p in self.rdata.frames])

        current = []
        broken = []  # To store trajectories no longer tracked

        # Add points from remaining frames
        for fr in range(self.rdata.numFrames):
            # If no current trajectories, make 1 trajectory for every
            # point in present frame
            if len(current) == 0:
                current.extend( [Traj.newFromPoint(p,fr) for p in \
                                 self.rdata[fr].data] )
                continue

            prev = [t.getFrame(fr-1) for t in current]
            pres = [p for p in self.rdata[fr].data]

            if len(pres) > 0:
                # Find distances from previous frame points to present
                sdist = spd.cdist(prev,pres)
                # Find matches
                matches = Trajectorizer.findMatches(sdist, self.distanceThreshold)
            else:
                matches = []

            # Append matched points and keep track of matched trajs and points
            matchedPts = set()
            matchedTjs = set()
            for prevTj, presPt in matches:
                tj, pt = current[prevTj], pres[presPt]
                tj.addPoint(pt)
                matchedTjs.add(tj)
                matchedPts.add(presPt)
            unmatchedPts = [i for i in range(len(pres)) if not (i in matchedPts)]
            unmatchedTjs = [t for t in current if not (t in matchedTjs)]

            # Make new trajs with unmatched points
            current.extend([Traj.newFromPoint(pres[i],fr) for i in unmatchedPts])

            # Remove unmatched trajs from current
            for t in unmatchedTjs:
                current.remove(t)
            broken.extend(unmatchedTjs)

            # Progress bar
            if not (self.progress is None) and (fr % 100 == 0):
                self.progress.setValue( int(100.*fr / self.rdata.numFrames) )

        self.trajs = broken + current

        if not (self.progress is None):
            self.progress.setValue(100)


    def fill(self, a, b):
        gap = b.beginFrame - a.endFrame
        fromPts = a.pointData[-10:]
        toPts = b.pointData[:10]
        fromLen = len(fromPts)
        toLen = len(toPts)
        fromTime = range(fromLen)
        toTime = range(fromLen+gap, fromLen+gap+toLen)
        gapTime = range(fromLen, fromLen+gap)
        time = fromTime + toTime
        trainData = fromPts + toPts
        x = [p[0] for p in trainData]
        y = [p[1] for p in trainData]
        z = [p[2] for p in trainData]
        order = 2
        if len(time) <= 2:
            order = 1
        fitx = np.polyfit(time, x, order)
        fity = np.polyfit(time, y, order)
        fitz = np.polyfit(time, z, order)
        gapx = np.polyval(fitx, gapTime)
        gapy = np.polyval(fity, gapTime)
        gapz = np.polyval(fitz, gapTime)
        return [np.array([gapx[fr], gapy[fr]. gapz[fr]]) for fr in range(gap)]

    def matchAdjacentTrajs(self, metric, gap=0):
        print("Matching adjacent trajectories")

        adj = self.findAdjacentTrajs(gap, metric)
        N = len(adj)
        print ("  %d pairs" % len(adj))

        if not (self.progress is None):
            self.progress.setValue(0)
            self.progress.setLabelText("Matching adjacent trajectories (gap=%d)" % gap)
            self.progress.show()

        def sortKey(x):
            try:
                return x[0]
            except:
                return 1000000

        while True:            
            if len(adj) == 0:
                break

            adj.sort(key=sortKey)
            m, a, b = adj[0]

            if m > 2*self.distanceThreshold:
                break

            # Remove pairs having a as first or b as second (idx 0 is measurement)
            removeList = []
            for p in adj:
                if (p[1] == a) or (p[2] == b):
                    removeList.append(p)
            for p in removeList:
                adj.remove(p)

            # Pairs having b as first now must have a as first
            for i in range(len(adj)):
                p = adj[i]
                if p[1] == b:
                    adj[i] = (p[0], a, p[2])                    

            # Join a and b into one trajectory
            if a == b:
                print("Error. Tried to join the same traj.")
            elif b.beginFrame - a.endFrame != gap:
                print("Error. Tried to join trajs that are not adjacent.")
            else:
                if gap > 0:
                    a.pointData.extend(self.fill(a,b))
                elif gap < 0:
                    b.pointData = b.pointData[-gap:]

                a.pointData.extend(b.pointData)
                self.trajs.remove(b)

            if not (self.progress is None):
                n = N - len(adj)
                self.progress.setValue( int(100.0*n/N) )

        if not (self.progress is None):
            self.progress.setValue(100)

    def findAdjacentTrajs(self, gap, metric):
        if not (self.progress is None):
            self.progress.setValue(0)
            self.progress.setLabelText("Finding adjacent trajectories")
            self.progress.show()

        N = len(self.trajs)
        NxN = N*N

        print("Finding adjacent trajs (N=%d)" % len(self.trajs))
        adjacent = []
        trajs = self.trajs
        i = 0
        for a in trajs:
            for b in trajs:
                if (a != b) and ((b.beginFrame - a.endFrame) == gap):
                    adjacent.append( (metric(a,b), a, b) )
                i += 1
                if not (self.progress is None) and (i % 10 == 0):
                    self.progress.setValue( int(100.0*i/NxN) )
        
        if not (self.progress is None):
            self.progress.setValue(100)
        return adjacent
