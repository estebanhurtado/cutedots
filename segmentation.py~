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

class Segmentation:
    def __init__(self, minSeconds=20.0):
        self.minSeconds = minSeconds
        self.trajBreaks = 0
        self.unmatchedTrajs = 0
        self.speakerChanges = 0
        self.discardedSegments = 0

    def cut(self, td, cutFrames):
        

    def findBreaks(self, td):
        beginFr = set([x.beginFrame for x in td.trajs])
        endFr = set([x.endFrame for x in td.trajs])
        return beginFr.union(endFr)

    def __call__(self, trajdata):
        breaks = findBreaks(trajdata)
        
        spkChange = findSpkChanges(trajdata)
