# Copyright 2012 Esteban Hurtado
#
# This file is part of Cutedots.
#
# Cutedots is distributed under the terms of the Reciprocal Public License 1.5.
#
# Cutedots is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the Reciprocal Public License 1.5 for more details.
#
# You should have received a copy of the Reciprocal Public License along with
# Cutedots. If not, see <http://opensource.org/licenses/rpl-1.5>.

import c3dformat
from numpy import size
import sys
import numpy as np
import numpy.ma as ma
import scipy as sp
import scipy.spatial.distance as spDistance
from sys import float_info
import os
import errors

# body part codes
bpname = [ 'UB', 'LB', 'Kn', 'Ft', 'El', 'Hn', 'tr', 'Hd' ]

def log(msg, lf=True):
    "Log a message"
    print(msg)
    sys.stdout.flush()

    
### RAW data storage
####################

class RawFrame:
    "Non-trajectorized frame"

    def __init__(self, arr):
        # Copy valid data
        self.data = arr[arr[:,3] >= 0][:,:3]

    def getSinglePoint(self, index):
        return self.data[index,:]

    def joinClosePoints(self, maxDist=1):
        if self.numPoints == 0:
            return
        # Initially all points are marked unique
        uniquePoint = [True] * self.numPoints
        sqDistance = spDistance.squareform(spDistance.pdist(self.data))
        for i in range(self.numPoints):
            for j in range(i+1, self.numPoints):
                if sqDistance[i,j] < maxDist:
                    uniquePoint[j] = False
        # Rebuild frame data
        self.data = self.data[np.array(uniquePoint),:]

    @property
    def numPoints(self):
        return self.data.shape[0]

    def __getitem__(self, index):
        return self.data[index,:]


class RawDataReadError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return 'Raw data read error: ' + self.msg

class RawData:
    "Array of raw frames"

    @property
    def numFrames(self):
        return len(self.frames)

    def __init__(self):
        self.frames = []
        self.filename = None
        self.frameRate = 100.0

    def joinClosePoints(self, progress):
        i = 0
        for frame in self.frames:
            if i % 1000 == 0:
                progress.setValue( int(100.0*i / self.numFrames) )
                if progress.wasCanceled():
                    return                
            frame.joinClosePoints()
            i += 1
        progress.setValue(100)

    def __getitem__(self, index):
        return self.frames[index]


### Trajectories
################

class Traj:
    "Same point at different frames."

    nameCounter = 0

    def __init__(self, beginFrame, name=None):
        self.name = ("tr_%d" % self.newCounter) if name is None else name
        self.pointData = []
        self.beginFrame = beginFrame

    def newFromFrameRange(self, begin, end):
        newTraj = Traj(0, self.name)
        newTraj.pointData = self.pointData[begin-self.beginFrame:end-self.beginFrame]
        return newTraj

    @property
    def endFrame(self): return self.beginFrame + len(self.pointData)
    @property
    def numFrames(self): return len(self.pointData)
    @property
    def isHead(self): return self.part == 'Hd'


    @property
    def newCounter(self):
        c = Traj.nameCounter
        Traj.nameCounter += 1
        return c

    @property
    def subject(self):
        try: return int(self.name[3])
        except: return 0

    @property
    def part(self):
        try: return self.name[:2]
        except: return None

    @property
    def side(self):
        try:
            if self.part != "Hd":
                return self.name[2]
        except:
            pass
        return None

    def setSubject(self, subject):
        self.name = "%s%d" % (self.name[:3], subject)

    def switchSubject(self):
        self.setSubject(3 - self.subject)

    @property
    def isUnlabeled(self):
        if self.part != 'Hd':
            return not self.part in bpname[:6] \
                or not self.side in ['L', 'R'] \
                or not self.subject in [1, 2]
        else:
            return not self.subject in [1, 2]

    def __str__(self):
        return "Traj %s: %d - %d" % (self.name, self.beginFrame, self.endFrame)

    @property
    def closestPointTo(self, frame):
        if self.hasFrame(frame):
            return self.getFrame()
        elif self.beginFrame > frame:
            return self.pointData[0]
        else:
            return self.pointData[-1]

    @staticmethod
    def newFromPoint(point, frameNum):
        newTraj = Traj(frameNum)
        newTraj.addPoint(point)
        return newTraj

    def addPoint(self, point):
        self.pointData.append(point)

    def average(self):
        return np.mean(self.pointData,0)

    def averageX(self):
        return float(np.mean([x[0] for x in self.pointData]))

    def hasFrame(self, framenum):
        """Returns True if given frame is included in trajectory's range"""
        return (framenum >= self.beginFrame) and (framenum < self.endFrame)

    def getFrame(self, framenum):
        """Returns absolute frame"""
        return self.pointData[framenum - self.beginFrame]

    def split(self, framenum):
        splitIdx = framenum - self.beginFrame
        t1 = Traj(self.beginFrame, self.name)
        t1.pointData = self.pointData[:splitIdx]
        t2 = Traj(framenum, self.name)
        t2.pointData = self.pointData[splitIdx:]
        return (t1, t2)

    def trimRight(self, framenum):
        relFrame = self.getFrame(framenum)
        if relFrame <= 0:
            return None
        elif relFrame >= self.numFrames:
            return self
        else:
            t = Traj(self.beginFrame, self.name)
            t.pointData = self.pointData[:relFrame]
            return t

    def trimLeft(self, framenum):
        relFrame = self.getFrame(framenum)
        if relFrame >= self.numFrames:
            return None
        elif relFrame <= 0:
            return self
        else:
            t = Traj(self.framenum, self.name)
            t.pointData = self.pointData[relFrame:]
            return t

    def predict(self, idx=0.0):
        numpts = self.numFrames
        if numpts == 0:     # No data, no predicton
            return None
        elif numpts == 1:   # One point, predict with itself
            return self.pointData[0]
        elif numpts in [2, 3]:  # Average
            return np.mean(self.pointData, 0)
        elif numpts > 3:   # Fit a polynomial
            degree = 1 if numpts < 5 else 2
            p = self.pointData[-10:]
            n = len(p)
            t = range(-n, 0)
            fit = np.polyfit(t,p,degree)
            return np.polyval(fit, idx)

    def backPredict(self, idx=0):
        numpts = self.numFrames
        if numpts == 0:     # No data, no predicton
            return None
        elif numpts == 1:   # One point, predict with itself
            return self.pointData[0]
        elif numpts in [2, 3]:  # Average
            return np.mean(self.pointData, 0)
        elif numpts > 3:   # Fit a polynomial
            degree = 1 if numpts < 5 else 2
            p = self.pointData[:10]
            n = len(p)
            t = range(n)
            fit = np.polyfit(t,p,degree)
            return np.polyval(fit, idx)

    def overlaps(self, other):
        "Returns true if there's a non empty intersection between frame ranges."
        return other.hasFrame(self.beginFrame) or other.hasFrame(self.endFrame)

    def contains(self, other):
        "Returns true if all frames of other are frames of self."
        return self.hasFrame(other.beginFrame) and self.hasFrame(other.endFrame-1)

    def __getitem__(self, index):
        return self.pointData[index]

### Trajectorized data
######################

class TrajData(object):
    """Contains trajectories.

    Keeps a list of trajectories.
    Constructor can trajectorize from preprocessed RawData.

    """

    def __init__(self):
        self.trajs = []
        self.filename = None
        self.framerate = 100.0
        self.changed = False
        self.trash = []
        self.framePointCount = None

    def newFromFrameRange(self, begin, end):
        newtd = TrajData()
        newtd.trajs = [t.newFromFrameRange(begin, end) for t in self.trajs
                       if t.hasFrame(begin) and t.hasFrame(end-1)]
        newtd.filename = self.filename
        newtd.framerate = self.framerate
        newtd.changed = True
        return newtd

    def addIdxToFilename(self, idx):
        root, ext = os.path.splitext(self.filename)
        self.filename = root + ("_%d" % idx) + ext

    def clone(self, empty=False):
        newTd = TrajData()
        newTd.trajs = [] if empty else self.trajs[:]
        newTd.framerate = self.framerate
        newTd.changed = True
        return newTd

    def asMaskedArray(self):
        minFr = self.minFrame
        numFr = self.numFrames
        dataList = []
        for t in self.trajs:
            data = ma.array(np.zeros((numFr,3)), mask=[(True,True,True)]*numFr)
            data[t.beginFrame-minFr:t.endFrame-minFr] = ma.array(t.pointData)
            dataList.append(data)
        return ma.array(dataList)

    def switchSubjects(self):
        for t in self.trajs:
            t.switchSubject()

    @property
    def continuous(self):
        if len(self.trajs) == 1:
            return True
        N = self.trajs[0].numFrames
        b = self.trajs[0].beginFrame
        for t in self.trajs[1:]:
            if t.numFrames != N or t.beginFrame != b:
                return False
        return True

    @property
    def numFrames(self):
        if len(self.trajs) == 0:
            return 0
        return \
            max([t.endFrame for t in self.trajs]) - \
            min([t.beginFrame for t in self.trajs])

    @property
    def maxFrame(self):
        return max([t.endFrame for t in self.trajs])

    @property
    def minFrame(self):
        return min([t.beginFrame for t in self.trajs])

    @property
    def numTrajs(self):
        return len(self.trajs)

    @property
    def empty(self):
        return self.numFrames == 0

    def countPoints(self):
        count = np.zeros(self.numFrames, dtype=int)
        for t in self.trajs:
            count[t.beginFrame:t.endFrame] += 1
        self.framePointCount = count

    def numPoints(self, numFrame):
        if self.framePointCount is None or self.changed:
            self.countPoints()
        return self.framePointCount[numFrame]

    def rename(self):
        for i in range(len(self.trajs)):
            self.trajs[i].name = "tr_%d" % (i+1)

    def delete(self, traj):
        if traj in self.trajs:
            self.trash.append(traj)
            self.trajs.remove(traj)
        self.changed = True

    def undelete(self):
        if len(self.trash) > 0:
            self.trajs.append( self.trash.pop() )

    def splitTraj(self, traj, framenum):
        if traj in self.trajs:
            t1,t2 = traj.split(framenum)
            self.trajs.remove(traj)
            self.trajs.extend([t1, t2])
        self.changed = True


    def cutRight(self, cutFrame):
        "Remove frames higher or equal than cutFrame"
        # Only keep trajectories that start before cutFrame
        self.trajs = [t for t in self.trajs if t.beginFrame < cutFrame ]
        # Cut trajectories that extend beyond numFram
        for t in self.trajs:
            if t.endFrame > cutFrame:
                newNumFrames = cutFrame - t.beginFrame
                t.pointData = t.pointData[:newNumFrames]
        self.changed = True

    def cutLeft(self, cutFrame):
        "Remove frames smaller than cutFrame"
        # Remove trajectories that end at cutFrame or before
        self.trajs = [t for t in self.trajs if t.endFrame >= cutFrame ]
        # Cut trajectories that start before cutFrame
        for t in self.trajs:
            if t.beginFrame < cutFrame:
                relFrame = cutFrame - t.beginFrame
                t.pointData = t.pointData[relFrame:]
                t.beginFrame = cutFrame
        # Make all trajectories start at cutFrame
        for t in self.trajs:
            t.beginFrame -= cutFrame
        self.changed = True

    class ContinuityError(errors.Warning):
        def __str__(self):
            return "Could not extract continuous data. " + \
                   "Please check that all trajectories " + \
                   "are the same length and start at the same frame"

    def checkContinuity(self):
        "Check all trajs have same length and starting frame"

        if not self.empty:
            first = self.trajs[0]
            numFrames = first.numFrames
            beginFrame = first.beginFrame
            for traj in self.trajs[1:]:
                difNum = numFrames != traj.numFrames
                difBegin = beginFrame != traj.beginFrame
                if not traj.isHead and (difNum or difBegin):
                    raise TrajData.ContinuityError()

    def toArray(self):
        self.checkContinuity()
        return np.array([t.pointData for t in self.trajs])

    def posBySubj(self):
        self.checkContinuity()
        trajs = sorted(self.trajs, key=lambda t: t.name)

        alldata = []
        allnames = []
        
        for s in [1,2]:
            data = [t for t in trajs if t.subject == s]
            head = [t.pointData for t in data if t.part == 'Hd']
            rest = [t for t in data if t.part != 'Hd']
            restNum = np.array([t.pointData for t in rest])
            if len(head) > 0:
                minHeadLen = min([np.shape(d)[0] for d in head])
                head = [d[:minHeadLen] for d in head]
                headNum = np.mean(np.array(head), 0)
                allnames.append(['Hd'] + [t.part + t.side for t in rest])
                headShape = headNum.shape
                headNum = headNum.reshape((1,headShape[0], headShape[1]))
                alldata.append(np.concatenate((headNum, restNum),0))
            else:
                allnames.append([t.part + t.size for t in rest])
                alldata.append(restNum)

        return alldata, allnames

    def labels(self):
        return [t.name for t in self.trajs]
