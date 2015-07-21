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
import dotsio as dio
import os
import transform

class Segmentation:
    def __init__(self, minTime=20.0):
        self.minTime = minTime
        self.trajBreaks = 0
        self.unmatchedTrajs = 0
        self.speakerChanges = 0
        self.discardedSegments = 0

    def cut(self, td, breaks):
        breakTimes = np.array(breaks)/td.framerate
        print("\tBreaks:", " ".join(["%.2f"% x for x in breakTimes]))
        newTdList = []
        idx = 0
        print("\tActual segments:", end="")
        for begin, end in zip(breaks[:-1], breaks[1:]):
            if (float(end-begin) / td.framerate) >= self.minTime:
                print(" %.2f-%.2f" % (begin/td.framerate, end/td.framerate), end="")
                newtd = td.newFromFrameRange(begin, end)
                newtd.addIdxToFilename(idx)
                newTdList.append(newtd)
                idx += 1
        print("")
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
        return set(zeroCrossings[0]).difference(ignore).union([0, td.maxFrame])        
        

def segmentFolder(infolder, outfolder, minTime, maxInterrupt):
    for dirpath, dirnames, filenames in os.walk(infolder):
        for fn in filenames:
            if fn.endswith(".qtd"):
                fullfn = os.path.join(dirpath, fn)
                print("Reading '%s'" % fullfn)
                td = dio.trajDataFromH5(fullfn)

                # Continuity segmentation
                sg = SegContinuousTrajs(minTime)
                tdList = sg([td])

                # Low pass filtering
                for td in tdList:
                    print("\tLow pass filtering '%s'" % str(td.filename))
                    transform.LpFilterTrajData(td, 10.0)

                # Speaker segmentation
                sg = SegSpeakers(minTime, maxInterrupt)
                tdList = sg(tdList)

                # Write
                print("\tWriting")
                for td in tdList:
                    relativeFn = td.filename[len(dirpath):].lstrip(os.path.sep)
                    td.filename = os.path.join(outfolder, relativeFn)
                    print("\t%s" % td.filename)

                    if not os.path.exists(os.path.dirname(td.filename)):
                        os.makedirs(os.path.dirname(td.filename))

                    dio.trajDataSaveH5(td)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--infolder', required=True)
    parser.add_argument('--outfolder', required=True)
    parser.add_argument('--mintime', default=20.0, type=float,
                        help="Segments shorter than this are discarded (seconds)")
    parser.add_argument('--maxinterrupt', default=4.0, type=float,
                        help="Speaker changes lasting less than this are ignored")
    args = parser.parse_args()

    segmentFolder(args.infolder, args.outfolder, args.mintime, args.maxinterrupt)

