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
# Cutedots. If not, see <http://http://opensource.org/licenses/rpl-1.5>.

from time import time
import cPickle as pickle
from trajdata import TrajData
from camstate import CamState

# Body part coding
##################

class Part:
    shortLabel = ['..', 'Hd', 'UB', 'El', 'Hn', 'LB', 'Kn', 'Ft']
    longLabel = ['unlabeled', 'head', 'upper back', 'elbow', 'hand', 'lower back', 'knee', 'foot']
    shortNum = dict([ (shortLabel[i],i) for i in range(len(shortLabel)) ])
    longNum = dict([ (longLabel[i],i) for i in range(len(longLabel)) ])
    default = 0
    headNum = shortNum['Hd']

    def __init__(self, part=0):
        self.part = Part.default
        if isinstance(part, int):
            self.part = part % self.N
        elif isinstance(part, str):
            if part in Part.shortLabel:
                self.part = Part.shortNum[part]
            elif part in Part.longLabel:
                self.part = Part.longNum[part]

    @property
    def unlabeled(self):
        return self.part == Part.default

    @property
    def N(self):
        return len(Part.shortLabel)
    
    def setNext(self):
        self.part = (self.part + 1) % self.N

    def setPrevious(self):
        self.part = (self.N + self.part - 1) % self.N

    @property
    def short(self):
        return Part.shortLabel[self.part % self.N]

    @property
    def long(self):
        return Part.longLabel[self.part % self.N]

    @property
    def num(self):
        return self.part % self.N

    def __repr__(self):
        return 'Part(%s)' % self.short

    def __str__(self):
        return self.long

    @property
    def isHead(self):
        return self.part == Part.head

class PartVar:
    alternatives = ['L', 'R', '.']
    longLabel = {'L':'left', 'R':'right', '.':''}
    altnum = {'L':1, 'R':2, '.':0}
    default = '.'

    def __init__(self, var='.'):
        self.var = var
        if not isinstance(var, int) and not self.var in PartVar.alternatives:
            self.var = '.'

    @property
    def unlabeled(self):
        return self.var == PartVar.default

    @property
    def short(self):
        if isinstance(self.var,int):
            return str(self.var)
        elif self.var in PartVar.alternatives:
            return self.var
        return PartVar.default

    @property
    def long(self):
        if isinstance(self.var,int):
            return str(self.var)
        elif self.var in PartVar.alternatives:
            return PartVar.longLabel[self.var]
        return ''

    @property
    def num(self):
        if isinstance(self.var, int):
            return self.var
        elif self.var in PartVar.alternatives:
            return PartVar.altnum[self.var]
        else:
            return 0

class BodyPart:
    def __init__(self, part=Part(), var=PartVar(), subj=0):
        self.part = part
        self.var = var
        self.subj = subj

    @property
    def unlabeled(self):
        return self.part.unlabeled or self.var.unlabeled or subj == 0

    @staticmethod
    def fromShortLabel(label):
        try: partvar, subj = label.split('-')
        except: return BodyPart()

        try: part = Part(partvar[:2])
        except: part = Part()

        try: var = PartVar(partvar[2])
        except: var = PartVar()

        try: subjnum = int(subj)
        except: subjnum = 0

        return BodyPart(part, var, subjnum)

    @property
    def short(self):
        return self.part.short + self.var.short + '-' + str(self.subj)

    def __repr__(self):
        return 'BodyPart(%s)' % self.short

    def __str__(self):
        if self.part.isHead or self.var.short == '.':
            return '%s of %d' % (self.var.long, self.subj)
        else:
            return '%s %s of %d' % (self.part.long, self.var.long, subj)

    @property
    def isHead(self):
        return self.part.isHead

    def setNextPart(self):
        self.part.setNext()

    def setPreviousPart(self):
        self.part.setPrevious()
        
    def key(self):
        return (self.part.num << 24) + ((self.var.num << 16)%256) + (self.subj % 65536)


class ModelState:
    def __init__(self, data=None):
        self.data = data
        self.frameNum = 0
        self.trajNum = 0
        self.cam = CamState()
        self.anaglyph3d = 0
        self.bodyTrans = 0.7
        self.width = -1    # Reshape callback must set these
        self.height = -1
        self.aspect = -1.0

        if not self.data is None and self.data.numTrajs > 0:
            if not self.data.trajs[self.traj].hasFrame(self.frame):
                self.selNextTraj()
        self.trajMap = {}

    @property
    def currentTraj(self):
        if self.data is None or self.data.numTrajs == 0:
            return None
        if self.trajNum >= self.data.numTrajs:
            self.trajNum = self.data.numTrajs - 1
        if self.trajNum < 0:
            self.trajNum = 0
        return self.data.trajs[self.trajNum]

    # Transport
    def transBack(self, amount):
        self.frameNum = max(0, self.frameNum - amount)
    def transFwd(self, amount):
        self.frameNum = min(self.numFrames-1, self.frameNum + amount)
    def transStart(self):
        self.frameNum = 0
    def transEnd(self):
        self.frameNum = self.numFrames-1

    # Labeling
    def renameHeads(self):
        counter = 1
        for traj in self.data.trajs:
            if traj.bodyPart.isHead:
                traj.bodyPart.var = counter
                counter += 1

    def labelSubject(self, subj):
        self.currentTraj.bodyPart.subj = subj

    def labelSide(self, side):
        self.currentTraj.bodyPart.var = side

    def labelPartPrev(self):
        self.currentTraj.bodyPart.setPreviousPart()

    def labelPartNext(self):
        self.currentTraj.bodyPart.setNextPart()

    # Label parts
#     def bodyPart(self):
#         return self.currentTraj().name[:2]

#     def side(self):
#         return self.currentTraj().name[2]

#     def subject(self):
#         return self.currentTraj().name[3]

#     # Info about labels
#     def bodyPartNum(self):
#         return bpnum[ self.bodyPart() ]

    def humanReadPart(self):
        return str(self.currentTraj.bodyPart)

    # Body part mapping
    def map(self, bodyPart, px, py, pz):
        """Maps body parts to positions.
        Also corrects for typical marker offsets just
        for visualization
        """

        x,y,z = px,py,pz

        part = bodyPart.part.short
        subj = bodyPart.subj
        side = bodyPart.var

        # rise
        if part in ['Kn','UB']: z += 50                        # move back
        if part in ['Kn','Ft']: x = x-50 if subj % 2 else x+50 # move forward
        if part in ['UB']: x = x+100 if subj % 2 else x-100    # LB

        if part == 'LB': 
            # move inside
            if subj % 2: y = y-80 if side == 'L' else y+80
            else: y = y+80 if side == 'L' else y-80
            z -= 100                            # lower
            x = x+20 if subj=='1' else x-20     # move forward

        # UB
        if part == 'UB':
            # Move outside
            if subj % 2: y = y+70 if side == 'L' else y-70
            else: y = y-70 if side == 'L' else y+70

        self.trajMap[bodyPart] = (x, y, z)

    def selNextTraj(self):
        if self.data is None:
            return
        start = self.trajNum
        self.trajNum = (self.trajNum+1) % self.data.numTrajs
        while self.traj != start:
            if self.currentTraj.hasFrame(self.frameNum):
                break
            self.trajNum = (self.trajNum+1) % self.data.numTrajs

    def selPrevTraj(self):
        if self.data is None:
            return
        start = self.trajNum
        self.trajNum = (self.data.numTrajs + self.trajNum - 1) % self.data.numTrajs
        while self.trajNum != start:
            if self.currentTraj.hasFrame(self.frameNum):
                break
            self.trajNum = (self.data.numTrajs+self.trajNum-1) % self.data.numTrajs

    def selNextUnlabTraj(self):
        if self.data is None:
            return
        start = self.trajNum
        self.trajNum = (self.trajNum+1) % self.data.numTrajs
        while self.trajNum != start:
            if self.currentTraj.bodyPart.unlabeled:
                self.frame = self.currentTraj.beginFrame
                break
            self.trajNum = (self.trajNum+1) % self.data.numTrajs

    def selPrevUnlabTraj(self):
        if self.data is None:
            return
        start = self.trajNum
        self.trajNum = (self.data.numTrajs+self.traj-1) % self.data.numTrajs
        while self.trajNum != start:
            if self.currentTraj.bodyPart.unlabeled:
                self.frame = self.currentTraj.beginFrame
                break
            self.trajNum = (self.data.numTrajs+self.trajNum-1) % self.data.numTrajs

    def selNextBreak(self):
        if self.data is None:
            return
        currentTrajs = [x for x in self.data.trajs if x.hasFrame(self.frame)]
        if len(currentTrajs) > 0:
            byEndFrame = sorted(currentTrajs, key=lambda x: x.endFrame)
            self.frame = byEndFrame[0].endFrame

    def deleteCurrent(self):
        if self.data is None:
            return
        self.data.delete( self.currentTraj )
        self.trajNum = self.trajNum % self.data.numTrajs

    def undelete(self):
        if self.data is None:
            return
        self.data.undelete()

    def deleteUnassigned(self):
        if self.data is None:
            return
        deleteList = [t for t in self.data.trajs if t.bodyPart.unlabeled]
        if len(deleteList) > 0:
            for traj in deleteList:
                self.data.trajs.remove(traj)
            self.data.changed = True

    def cutRight(self):
        if self.frame > 0:
            self.data.cutRight(self.frameNum)
            self.frameNum = self.data.numFrames - 1
        else:
            self.data = None
            self.traj = 0

    def cutLeft(self):
        if self.frameNum < self.data.numFrames:
            self.data.cutLeft(self.frameNum)
            self.frameNum = 0
        else:
            self.data = None
            self.traj = 0
