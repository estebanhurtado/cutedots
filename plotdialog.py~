# Copyright 2014 Esteban Hurtado
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
# Cutedots. If not, see &lt;http://opensource.org/licenses/rpl-1.5&gt;.

import os
os.environ['QT_API'] = 'pyside' 
from PySide import QtGui
import matplotlib.pyplot as pl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as PLCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as PLToolbar
import matplotlib as mpl
import modelstate
import analysis
import numpy as np

mpl.rcParams['backend.qt4'] = 'PySide'

class PlotDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(PlotDialog, self).__init__(parent)

        self.figure = pl.figure()
        self.canvas = PLCanvas(self.figure)
        self.toolbar = PLToolbar(self.canvas, self)


        # layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    def display(self):
        self.canvas.draw()
        self.show()


class DataPlot(PlotDialog):
    def __init__(self, parent=None):
        super(DataPlot, self).__init__(parent)

    def clear(self):
        self.figure.clear()

    def subplot(self, rows=1, cols=1, num=1):
        return self.figure.add_subplot(rows, cols, num)

    def warnIfNoDataLoaded(method):
        "Decorator that throws a warning if no data is already loaded."
        def deco(self, *args, **kargs):
            if self.parent().data is None:
                QtGui.QMessageBox.warning(self.parent(), 'Warning', 'No data loaded yet.')
                return
            method(self, *args, **kargs)
        return deco


    def plotSubjectFunc(self, func, subplot=True):
        "Makes a plot of a time function by subject"

        data = self.parent().data
        trajs = analysis.trajsBySubj(data.trajs)
        numSubjs = len(trajs)
        subjNum = 1
        self.clear()
        if not subplot:
            ax = self.subplot()

        for subject, trajList in trajs.items():
            f = func(trajList)
            t = np.arange(len(f)) / data.framerate
            if subplot:
                ax = self.subplot(numSubjs, 1, subjNum)
                ax.set_ylabel("Subject %s" % subject)
                subjNum += 1
                ax.plot(t, f)



    @warnIfNoDataLoaded
    def plotContinuity(self):
        data = self.parent().data

        # Organize curves by label
        trajectories = dict()
        for traj in data.trajs:
            trajectories.setdefault(traj.name, []).append(traj)
        # Plot
        y = 0
        ticksy = []
        ticksn = []
        self.clear()
        ax = self.subplot()
        colors = ['b','r']
        trajectories = trajectories.items()

        def key(traj):
            try:
                x = traj[0]
                subj = ord(x[3]) << 24
                side = ord(x[2]) << 16
                part = modelstate.ordbpnum[x[:2]]
                return subj + side + part
            except:
                return traj

        trajectories.sort(key=key)

        for name, trajs in trajectories:
            N = len(trajs)
            y -= max(10, 2*N+2)
            ticksy.append(y)
            ticksn.append("%s (%d)" % (name, len(trajs)))
            i = 0
            for t in trajs:
                t0 = t.beginFrame / data.framerate
                t1 = (t.endFrame-1) / data.framerate
                off = 2*(i-(N/2))
                ax.plot([t0, t1], [y+off, y+off], colors[i%2], linewidth=3)
                i += 1
        ax.set_yticks(ticksy)
        ax.set_yticklabels(ticksn)
        self.display()


    @warnIfNoDataLoaded
    def plotLengthHistogram(self):
        data = self.parent().data
        self.clear()
        ax = self.subplot()
        ax.hist([t.numFrames / data.framerate for t in data.trajs])
        ax.set_xlabel('length (secs)')
        self.display()

    @warnIfNoDataLoaded
    def plotPositionSpectrogram(self):
        self.clear()
#        ax = self.subplot(2,
        self.plotSubjectFunc(analysis.averagePos)
        self.display()

    @warnIfNoDataLoaded
    def plotEnergyVsTime(self):
        self.plotSubjectFunc(analysis.energy)
        self.display()
