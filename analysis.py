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

import pylab as pl
import numpy as np
import scipy as sp
import numpy.ma as ma

def energy(trajectories):
    "Returns aggregated energy signal for all markers"

    maxFrame = max([t.endFrame for t in trajectories])
    energy = np.zeros(maxFrame-1) # Speed results
    for t in trajectories:
        if t.numFrames >= 2:
            trajSpeed = np.subtract(100*np.array(t.pointData[1:]),
                                    100*np.array(t.pointData[:-1]))  # find speed
            trajEnergy = np.sum(trajSpeed**2,1)
            energy[t.beginFrame:t.endFrame-1] += trajEnergy     # store energy
    return energy


def trajsToMaskedPosition(trajs):
    numFrames = max([t.endFrame for t in trajs])
    position = ma.zeros((len(trajs), numFrames, 3))
    i = 0
    for t in data.trajs:
        position.mask[...] = True
        position[i, t.beginFrame:t.endFrame, :] = t.pointData
        position.mask[i, t.beginFrame:t.endFrame, :] = False
        i+=1
    return position


def averagePos(data):
    "Returns modulus of average position"

    pos = trajsToMaskedPosition(data)
    return ma.sum(ma.mean(pos,0)**2, 1)**0.5

def trajsBySubj(trajectories):
    # classify trajectories by subject
    trajs = {}
    for t in trajectories:
        trajs.setdefault(t.name[3], []).append(t)
    return trajs


def plotEnergy(data):
    plotSubjectFunc(data, energy)
    pl.show()

def ortoSpeeds(trajectories):
    "Returns aggregation of speeds for each axis."

    maxFrame = max([t.endFrame for t in trajectories])
    speed = np.zeros((maxFrame-1,3)) # Speed results
    for t in trajectories:
        if t.numFrames >= 2:
            trajSpeed = np.subtract(t.pointData[1:], t.pointData[:-1])  # find speed
            speed[t.beginFrame:t.endFrame-1] += trajSpeed  # add traj. speed to global
    return speed

def plotSpeed(data):
    # classify trajectories by subject
    trajs = trajsBySubj(data.trajs)

    axes = [ ('horizontal', 0), ('sides', 1), ('vertical', 2) ]
    plotNum = 1
    subjSpeeds = [ (subj, ortoSpeeds(trajs)) for (subj,trajs) in trajs.items() ]
    numPlots = len(axes)

    for title, axis in axes:
        pl.subplot(numPlots,1,plotNum)
        plotNum += 1
        for subj, speed in subjSpeeds:
            t = np.arange(len(speed)) / data.framerate
            pl.plot(t, speed[:,axis])
            pl.ylabel(title)
    pl.show()


def projectedSpeed(trajectories, direction):
    "Returns aggregation of projected speeds onto the given (unitary) direction"

    maxFrame = max([t.endFrame for t in trajectories])
    speed = np.zeros(maxFrame-1) # Speed results
    for t in trajectories:
        if t.numFrames >= 2:
            trajSpeed = np.subtract(t.pointData[1:], t.pointData[:-1])  # find speed
            projSpeed = np.sum(trajSpeed * direction, 1)
            speed[t.beginFrame:t.endFrame-1] += projSpeed  # store energy
    return speed

