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

import numpy as np
import scipy.signal as sig

def filter(signal, Fc):
    h = np.exp(-2.0 * np.pi * Fc)
    a0 = 1.0 - h
    b1 = h
    y = [signal[0]]
    for x in signal:
        y.append( a0*x + b1*y[-1] )
    return y[1:]

def LpFilterComponent(data, Fc):
    s = data[:]
    for i in range(4):
        s = filter(s, Fc)
    return s

def LpFilterTraj(traj, Fc):
    data = np.array(traj.pointData)
    for i in range(3):
        data[:,i] = LpFilterComponent(data[:,i], Fc)
    traj.pointData = [np.array(x) for x in data.tolist()]


def LpFilterTrajData(trajdata, freq):
    Fc = float(freq) / float(trajdata.framerate)
    for traj in trajdata.trajs:
        LpFilterTraj(traj, Fc)
    trajdata.changed = True
