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

    def trajectorize(self):
        print("Trajectorization")
        print("- Distance based trajectorization...")
        self.distanceTraj()
        print("- Matching adjacent trajectories...")
        self.matchAdjacentTrajs(0)
        print("- Matching 1 frame gap trajectories...")
        self.matchAdjacentTrajs(1)
        print("- Matching 2 frame gap trajectories...")
        self.matchAdjacentTrajs(2)
        print("Done")

    def distanceTraj(self):
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
        print("  matching %d trajectories") % len(self.trajs)
        while True:
            adj = self.findAdjacentTrajs(gap)
            if len(adj) == 0:
                break

            errorList = []
            for pair in adj:
                a, b = pair
                pa = a.predict( (-1.+gap)/2 )
                pb = b.backPredict( (-1.-gap)/2 )
                dev = float(np.sum((pb-pa)**2)**0.5)
                errorList.append((dev,pair))

            errorList.sort()

            mindev, pair = errorList[0]
            if mindev > 2*self.distanceThreshold:
                break

            a, b = pair
            affectedPairs = [pair for pair in adj if pair[0] == a or pair[1] == b]
            for p in affectedPairs:
                adj.remove(p)
            self.trajs.remove(b)
            a.pointData.extend(b.pointData)

    def findAdjacentTrajs(self, gap):
        adjacent = []
        for a in self.trajs:
            for b in self.trajs:
                if (a != b) and ((b.beginFrame - a.endFrame) == gap):
                    adjacent.append((a,b))
        return adjacent
