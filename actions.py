#!/usr/bin/env python

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

from PySide import QtCore, QtGui
import preprocess
import analysis
from plotdialog import DataPlot
import modelops


class CuteDotsActions(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        self.dataPlot = DataPlot(self.parent())

    def makeMenus(self):
        self.fileMenu()
        self.operationsMenu()
        self.plotMenu()
        self.helpMenu()

    def fileMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu("&File")

        menu.addAction('&Open motion data file...',
                       self.openDataFile, 'Ctrl+O')
        menu.addAction('&Save',
                       self.parent().saveFile, 'Ctrl+S')

        menu.addSeparator()
        importMenu = menu.addMenu('Import')
        importMenu.addAction('&Import C3D file...',
                             self.importC3D, 'Ctrl+C')
        importMenu.addAction('&Import CSV file (early Motive)...',
                             self.importCSV)
        importMenu.addAction('&Import CSV file (current Motive)...',
                             self.importCSV2)

        exportMenu = menu.addMenu('Export')
        exportMenu.addAction('Save image sequence',
                             self.parent().saveSequence)

        menu.addSeparator()
        menu.addAction('Save and e&xit',
                       self.parent().close, 'Ctrl+Q')
        menu.addAction('Exit without saving',
                       self.parent().exitNoSave)

    def operationsMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu('Operations')

        menu.addAction('Rotate point cloud 90 degrees (around vertical)',
                       self.rotate90)
        menu.addAction('Swap subjects 1 and 2',
                       self.swap)
        menu.addAction('Guess side and subject',
                       self.guessSideAndSubject)
        menu.addAction('Sort trajectories traversal order by X coordinate',
                       self.sortTrajectories)

        menu.addSeparator()
        menu.addAction('Match broken trajectories...',
                       self.matchTrajectories, 'Ctrl+M')
        menu.addAction('Average trajectories with same name into one',
                       self.averageTrajs)
        menu.addAction('Fill gaps in trajectories...',
                       self.fillGaps)

        menu.addSeparator()
        menu.addAction('Remove unassigned trajectories',
                       self.removeUnassigned)
        menu.addAction('Remove short trajectories...',
                       self.removeShort)

        menu.addSeparator()
        menu.addAction('Delete current frame and all the next',
                       self.cutRight)
        menu.addAction('Delete frames before the current one',
                       self.cutLeft)

    def plotMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu('Plot')

        trajMenu = menu.addMenu('Trajectories')
        trajMenu.addAction('Continuity',
                           self.dataPlot.plotContinuity)
        trajMenu.addAction('Length histogram',
                           self.dataPlot.plotLengthHistogram)

        positionMenu = menu.addMenu('Position')
        positionMenu.addAction('Spectrogram',
                               self.dataPlot.plotPositionSpectrogram)

        speedMenu = menu.addMenu('Speed')

        energyMenu = menu.addMenu('Energy')
        energyMenu.addAction('Energy vs Time',
                             self.dataPlot.plotEnergyVsTime)



        # ## Motion
        # plotEnergyAction = self.mkAction(
        #     'Plot energy',
        #     'Make global energy plot',
        #     self.plotEnergy)
        # plotSpeedAction = self.mkAction(
        #     'Plot speed',
        #     'Plots speed for each axis.',
        #     self.plotSpeed)
        # ## PCA
        # pcaBiplotAction = self.mkAction(
        #     'Biplot (subjects as one)',
        #     'Project in first two axes of variance',
        #     self.pcaBiplot)
        # pcaScreeAction = self.mkAction(
        #     'Scree plot (subjects as one)',
        #     'Show eigenvalues',
        #     self.pcaScree)
        # pca3dPlotAction = self.mkAction(
        #     '3D plot (separate PCA fits for subjects)',
        #     'Plot observations projected on first three axes',
        #     self.pca3d, 'Ctrl+P')
        # pca3dPlotTogetherAction = self.mkAction(
        #     '3D plot (same PCA fit for subjects)',
        #     'Plot observations projected on first three axes',
        #     self.pca3dTogether, 'Ctrl+P')
        # pcaDistancePlotAction = self.mkAction(
        #     'PCA space distance between subjects vs time',
        #     'Between-subject euclidean distance of PCA scores vs time',
        #     self.pcaDistancePlot)
        # pcaLoadingsAction = self.mkAction(
        #     'PCA loadings (two subjects in separate variables)',
        #     'PCA loadings',
        #     self.pcaLoadings)
        # xcorrAction = self.mkAction(
        #     'Cross-correlation',
        #     'Produce cross-correlation plot for files in a folder',
        #     self.plotCrossCorrelation)

    def helpMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu("&Help")

        menu.addAction('About', self.parent().displayAboutDlg)


    def warnIfNoDataLoaded(method):
        "Decorator that throws a warning if no data is already loaded."
        def deco(self, *args, **kargs):
            if self.parent().data is None:
                QtGui.QMessageBox.warning(self.parent(), 'Warning', 'No data loaded yet.')
                return
            method(self, *args, **kargs)
        return deco

    def updateDisplay(method):
        "Decorator that updates GL display after calling method."
        def deco(self, *args, **kargs):
            method(self, *args, **kargs)
            self.parent().gl.updateGL()
        return deco

    def updateNumFrames(method):
        def deco(self, *args, **kargs):
            method(self, *args, **kargs)
            self.parent().transport.setNumFrames(self.parent().data.numFrames)
        return deco

    def updateStatus(method):
        "Updates status after calling method."
        def deco(self, *args, **kargs):
            method(self, *args, **kargs)
            self.parent().updateStatus()
        return deco

    def openDataFile(self):
        fn, x = QtGui.QFileDialog.getOpenFileName\
                (None, 'Open a CuteDots motion data file')
        if fn == '':
            return
        self.parent().loadDataFile(fn)

    def importC3D(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a C3D data file')
        if fn == '':
            return
        progress = self.parent().mkProgress("Importing...")
        qtdFn = preprocess.ppC3D(fn, progress)
        self.parent().loadDataFile(qtdFn)

    def importCSV(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a CSV data file')
        if fn == '':
            return
        progress = self.parent().mkProgress("Importing...")
        qtdFn = preprocess.ppCSV(fn, progress)
        self.parent().loadDataFile(qtdFn)

    def importCSV2(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a CSV2 data file')
        if fn == '':
            return
        progress = self.parent().mkProgress("Importing...")
        qtdFn = preprocess.ppCSV2(fn, progress)
        self.parent().loadDataFile(qtdFn)

    @warnIfNoDataLoaded
    @updateDisplay
    def guessSideAndSubject(self):
        modelops.guessSideAndSubject(self.parent().data)

    @warnIfNoDataLoaded
    @updateDisplay
    def rotate90(self):
        progress = self.parent().mkProgress("Rotating 90 degrees...")
        modelops.rotate90Deg(self.parent().data, progress)

    @warnIfNoDataLoaded
    @updateDisplay
    def swap(self):
        progress = self.parent().mkProgress("Swapping subjects...")
        modelops.swapSubjects(self.parent().data, progress)

    @warnIfNoDataLoaded
    @updateDisplay
    def sortTrajectories(self):
        modelops.sortTrajsSlow(self.parent().data)

    @warnIfNoDataLoaded
    @updateDisplay
    def matchTrajectories(self):
        threshold, ok = QtGui.QInputDialog.getInteger(
            self.parent(), "Match trajectories", "Distance threshold (mm)", 20, 0, 1000)
        if not ok: return
        maxGap, ok = QtGui.QInputDialog.getInteger(
            self.parent(), "Match trajectories", "Max. frame gap", 5, -100, 1000)
        if not ok: return
        minGap, ok = QtGui.QInputDialog.getInteger(
            self.parent(), "Match trajectories", "Min. frame gap", 0, -100, 1000)
        if not ok: return
        progress = self.parent().mkProgress("Matching trajectories")
        modelops.matchTrajectories(self.parent().data, threshold, maxGap, progress)

    @warnIfNoDataLoaded
    @updateDisplay
    @updateStatus
    def averageTrajs(self):
        progress = self.parent().mkProgress("Averaging trajectories by name...")
        modelops.averageSameNameTrajectories(self.parent().data, progress)

    @warnIfNoDataLoaded
    @updateStatus
    def fillGaps(self):
        maxGap, ok = QtGui.QInputDialog.getDouble(
            self.parent(), "Fill trajectory gaps",
            "Max. gap to fill (secs.)", 0.2, 0.0, 10.0)
        if not ok: return
        progress = self.parent().mkProgress("Filling small gaps...")
        modelops.fillGaps(self.parent().data, maxGap, maxGap, progress)

    @warnIfNoDataLoaded
    @updateStatus
    def removeUnassigned(self):
        self.parent().model.deleteUnassigned()

    @warnIfNoDataLoaded
    @updateStatus
    def removeShort(self):
        minLength, ok = QtGui.QInputDialog.getInteger(
            self.parent(), "Remove short trajectories", "Minimum length (frames)", 10, 0)
        if not ok:
            return
        self.parent().model.deleteShort(minLength)

    @warnIfNoDataLoaded
    @updateNumFrames
    @updateStatus
    def cutRight(self):
        self.parent().model.cutRight()

    @warnIfNoDataLoaded
    @updateNumFrames
    @updateStatus
    def cutLeft(self):
        self.parent().model.cutLeft()

    @warnIfNoDataLoaded
    def plotContinuity(self):
        self.dataPlot.plotContinuity(self.parent().data)
    @warnIfNoDataLoaded
    def plotLengthHistogram(self):
        self.dataPlot.plotLengthHistogram(self.parent().data)


    @warnIfNoDataLoaded
    def plotEnergy(self):
        analysis.plotEnergy(self.parent().data)
    @warnIfNoDataLoaded
    def plotSpeed(self):
        analysis.plotSpeed(self.parent().data)


    @warnIfNoDataLoaded
    def plotCrossCorrelation(self):
        pass
    @warnIfNoDataLoaded
    def pcaScree(self):
        rstats.pcaScreePlot(self.parent().data)
    @warnIfNoDataLoaded
    def pcaBiplot(self):
        rstats.pcaBiplot(self.parent().data)
    @warnIfNoDataLoaded
    def pca3d(self):
        rstats.pca3dPlot(self.parent().data)
    @warnIfNoDataLoaded
    def pca3dTogether(self):
        rstats.pca3dPlotTogether(self.parent().data)
    @warnIfNoDataLoaded
    def pcaDistancePlot(self):
        rstats.pcaDistancePlot(self.parent().data)
    @warnIfNoDataLoaded
    def pcaLoadings(self):
        rstats.pcaLoadings(self.parent().data)
