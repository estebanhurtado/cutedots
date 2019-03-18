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
import sys
#from numba import jit

def speedFunc(samplerate):
    def func(data):
        return (data[1:,...] - data[:-1,...])*samplerate
    return func

def separateComponents(d):
    return np.transpose(np.concatenate(d,1))


def markerSpeeds(d):
    compSpeeds = d[:, :-1, :] - d[:, 1:, :]
    return np.sqrt(np.sum(compSpeeds**2, 2))

def preprocessPosition(trajdata, flattenFunc=separateComponents, xyzNames=True):
    data, names = trajdata.posBySubj()
    if names[0] != names[1]:
        n0 = set(names[0])
        n1 = set(names[1])
        nameSet = n0.intersection(n1)
        newTd = trajdata.clone(True)
        newTd.trajs = [x for x in trajdata.trajs if x.name[:3] in nameSet]
        print("\t*** Warning: name mismatch. Preserved %d common trajectories of %d to fix" \
                  % (len(newTd.trajs), len(trajdata.trajs)))
        print(newTd.trajs)
        data, names = newTd.posBySubj()
    data = [flattenFunc(d) for d in data]
    if xyzNames:
        newNames = [n + d for n in names[0] for d in ['X', 'Y', 'Z']]
    else:
        newNames = names[0]
    return data, newNames


def plotContinuity(data):
    # Organize curves by label
    trajectories = dict()
    for traj in data.trajs:
        trajectories.setdefault(traj.name, []).append(traj)
    # Plot
    y = 0
    ticksy = []
    ticksn = []
    for name, trajs in trajectories.items():
        y -= 10
        ticksy.append(y)
        ticksn.append(name)
        for t in trajs:
            t0, t1 = t.beginFrame / data.framerate, (t.endFrame-1) / data.framerate
            pl.plot([t0, t1], [y, y])
    pl.yticks(ticksy, ticksn)
    pl.show()


def energy(trajectories, transform=lambda x: x):
    "Returns aggregated energy signal for all markers"

    maxFrame = max([t.endFrame for t in trajectories])
    energy = np.zeros(maxFrame-1) # Speed results
    for t in trajectories:
        if t.numFrames >= 2 \
        and t.name[:2] != 'Kn' \
        and t.name[:2] != 'Ft' \
        and t.name[:2] != 'Hn':
            trajSpeed = np.subtract(100*np.array(t.pointData[1:]),
                                    100*np.array(t.pointData[:-1]))  # find speed
            trajEnergy = np.sum(trajSpeed**2,1)
            energy[t.beginFrame:t.endFrame-1] += trajEnergy     # store energy
    return transform(energy)

def logEnergy(trajectories):
    return energy(trajectories, np.log)


def energyPairFromTrajData(td, transform=lambda x:x):
    subj1 = [t for t in td.trajs if t.subject == 1]
    subj2 = [t for t in td.trajs if t.subject == 2]
    e1 = energy(subj1, transform)
    e2 = energy(subj2, transform)
    return e1, e2

#@jit
def logFunc(x):
    return np.log(x+0.001)

#@jit
def logEnergyPairFromTrajData(td):
    return energyPairFromTrajData(td, logFunc)

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

