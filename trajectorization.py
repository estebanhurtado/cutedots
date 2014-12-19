from trajdata import *
import scipy.spatial.distance as spd
import numpy as np
from PySide import QtCore

class Trajectorizer:

    def __init__(self, rdata, progress=None):
        self.rdata = rdata
        self.progress = progress
        self.trajs = []
        self.distanceThreshold = 10

        self.memento = dict()
        self.metric = None

    def trajectorize(self):
        print("Trajectorization")
        print("- Distance based trajectorization...")
        self.distanceTraj()
        print("- Matching adjacent trajectories...")
        self.matchAdjacentTrajs(0)
#        print("- Matching 1 frame gap trajectories...")
#        self.matchAdjacentTrajs(1)
#        print("- Matching 2 frame gap trajectories...")
#        self.matchAdjacentTrajs(2)
        print("Done")

    def distanceTraj(self):
        self.progress.show()

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

            # Find distances from previous frame points to present
            prev = [t[-1] for t in current]
            pres = [p for p in self.rdata[fr].data]
            sdist = spd.cdist(prev,pres)
            
            # For each trajectory, find closest point in new frame
            #   if within threshold, append new point
            #   else, move traj to broken and new point starts new traj

            toMove = []
            toAdd = []

            for i in range(sdist.shape[0]):
                imin = np.argmin(sdist[i,:])
                dist = sdist[i, imin]
                p = pres[imin]

                if dist <= self.distanceThreshold:
                    current[i].addPoint(p)
                else:
                    toMove.append(current[i])
                    toAdd.append(Traj.newFromPoint(p,fr))

            for t in toMove:
                current.remove(t)
            broken.extend(toMove)
            current.extend(toAdd)

            if not (self.progress is None) and (fr % 100 == 0):
                self.progress.setValue( int(100.*fr / self.rdata.numFrames) )

        self.trajs = broken + current
        if not (self.progress is None):
            self.progress.setValue(100)


    def matchAdjacentTrajs(self, gap):
        print("Matching adjacent trajectories")

        def metric1(a,b):
            return np.sum((b.pointData[0] - a.pointData[-1])**2)**0.5

        def metric2(a,b):
            pa = a.predict( (-1.+gap)/2 )
            pb = b.backPredict( (-1.-gap)/2 )
            return float(np.sum((pb-pa)**2)**0.5)

        adj = self.findAdjacentTrajs(gap, metric1)
        N = len(adj)
        print ("  %d pairs" % len(adj))

        if not (self.progress is None):
            self.progress.setValue(0)
            self.progress.setLabelText("Matching adjacent trajectories (gap=%d)" % gap)
            self.progress.show()

        while True:
            if len(adj) == 0:
                break

            m, a, b = adj[0]

            if m > 10*self.distanceThreshold:
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

            # Merge a and b into one trajectory
            a.pointData.extend(b.pointData)
            self.trajs.remove(b)

            print ("  %d pairs" % len(adj))

            if not (self.progress is None):
                n = N - len(adj)
                self.progress.setValue( int(100.0*n/N) )

        self.progress.setValue(100)




#     def matchAdjacentTrajs(self, gap):
#         print("  matching %d trajectories" % len(self.trajs))
#         memento = set()
#         while True:
#             adj = self.findAdjacentTrajs(gap).difference(memento)
#             print("  %d pairs" % len(adj))
#             if len(adj) == 0:
#                 break

#             errorList = []
#             for pair in adj:
#                 a, b = pair
#                 pa = a.predict( (-1.+gap)/2 )
#                 pb = b.backPredict( (-1.-gap)/2 )
#                 dev = float(np.sum((pb-pa)**2)**0.5)
#                 errorList.append((dev,pair))
#                 memento.add(pair)

#             errorList.sort()

#             mindev, pair = errorList[0]
#             if mindev > 2*self.distanceThreshold:
#                 break

#             a, b = pair
#             affectedPairs = [pair for pair in adj if pair[0] == a or pair[1] == b]
#             for p in affectedPairs:
#                 adj.remove(p)
#             self.trajs.remove(b)
#             a.pointData.extend(b.pointData)

    def findAdjacentTrajs(self, gap, metric):
        if not (self.progress is None):
            self.progress.setValue(0)
            self.progress.setLabelText("Finding adjacent trajectories")
            self.progress.show()


        N = len(self.trajs)
        NxN = N*N

        if metric == self.metric:
            self.memento = dict()
            self.metric = metric

        print "Finding adjacent trajs", len(self.trajs)
        adjacent = []
        trajs = self.trajs
        i = 0
        for a in trajs:
            for b in trajs:
                if (a != b) and ((b.beginFrame - a.endFrame) == gap):
                    if not (a,b) in self.memento:
                        self.memento[(a,b)] = metric(a,b)
                    adjacent.append( (self.memento[(a,b)], a, b) )
                    i += 1
                    if not (self.progress is None) and (i % 100 == 0):
                        self.progress.setValue( int(100.0*i/NxN) )
            
        adjacent.sort()
        self.progress.setValue(100)
        return adjacent
