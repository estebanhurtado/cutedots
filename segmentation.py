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

from __future__ import print_function
import scipy.signal as sig
import analysis as an
import numpy as np

class Segmentation:
    def __init__(self, minTime=20.0):
        self.minTime = minTime
        self.trajBreaks = 0
        self.unmatchedTrajs = 0
        self.speakerChanges = 0
        self.discardedSegments = 0

    def cut(self, td, breaks):
        print(breaks)
        newTdList = []
        idx = 0
        for begin, end in zip(breaks[:-1], breaks[1:]):
            print("***", begin, end)
            if (float(end-begin) / td.framerate) >= self.minTime:
                newtd = td.newFromFrameRange(begin, end)
                newtd.addIdxToFilename(idx)
                newTdList.append(newtd)
                idx += 1
        return newTdList

    def __call__(self, tdList):
        newTdList = []

        for td in tdList:
            breaks = self.findBreaks(td)
            segments = self.cut(td, sorted(list(breaks)))
            newTdList.extend(segments)
            print("\t[%d segments]\t%s" % (len(segments), str(td.filename)))
        
        return newTdList


class SegContinuousTrajs(Segmentation):
    def __init__(self, minTime=20.0):
        Segmentation.__init__(self, minTime)

    def findBreaks(self, td):
        print("Continuity segmentation")
        beginFr = set([x.beginFrame for x in td.trajs])
        endFr = set([x.endFrame for x in td.trajs])
        return beginFr.union(endFr)

class SegSpeakers(Segmentation):
    def __init__(self, minTime=20.0, maxInterrupt=4.0):
        Segmentation.__init__(self, minTime)
        self.maxInterrupt = maxInterrupt

    def findBreaks(self, td):
        print("Speaker segmentation")

        # Extract filtered energy
        N = int(td.framerate)
        kernelSize = N if (N % 2) == 1 else N+1
        kernel = np.ones(kernelSize) / float(kernelSize)
        def transform(s):
            return sig.fftconvolve(s, kernel, mode='same')
        e1, e2 = an.energyPairFromTrajData(td, transform)

        # Find speaker changes
        sign = np.sign(e1 - e2)
        sign[np.where(sign == 0)] = 1
        zeroCrossings = np.where(sign[:-1] * sign[1:] < 0)

        # Ignore fast changes
        ignore = set()
        maxIntFrames = int(self.maxInterrupt * td.framerate + 0.5)
        pairs = zip(zeroCrossings[:-1], zeroCrossings[1:])
        for i in range(len(zeroCrossings)-1):
            x0, x1 = pairs[i]
            if (x1 - x0) > maxIntFrames:
                ignore.update([x0, x1])
                i+=1
        
        # Breaks
        return set(zeroCrossings[0]).difference(ignore)        
        


