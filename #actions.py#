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
from PySide.QtWebKit import QWebView
import preprocess
import transform
import analysis
from plotdialog import DataPlot
import modelops
import pystats
import plots

def displayHtml(parent, title, html):
    win = QtGui.QDialog(parent)
    win.setWindowTitle(title)
    layout = QtGui.QVBoxLayout()
    win.setLayout(layout)
    view = QWebView()
    view.setHtml(html)
    layout.addWidget(view)
    win.show()

class CuteDotsActions(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
#        self.dataPlot = DataPlot(self.parent())


    @property
    def dataPlot(self):
        return self.newDataPlot()

    def newDataPlot(self):
        return DataPlot(self.parent())

    def makeMenus(self):
        self.fileMenu()
        self.operationsMenu()
        self.signalMenu()
        self.analysisMenu()
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
        menu.addAction('Average trajectories by name',
                       self.averageTrajs)
        menu.addAction('Fill gaps in trajectories...',
                       self.fillGaps)

        menu.addSeparator()
        menu.addAction('Remove unassigned trajectories',
                       self.removeUnassigned)
        menu.addAction('Remove short trajectories...',
                       self.removeShort)

        menu.addSeparator()
        menu.addAction('Delete from current frame to end',
                       self.cutRight)
        menu.addAction('Delete frames before the current one',
                       self.cutLeft)

    def signalMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu('Signal')
        
        menu.addAction('Recursive 4-stage low pass filter',
                       self.lpFilter)

    def analysisMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu('Analysis')

        menu.addAction('PCA',
                       self.pcaOutput)
        menu.addAction('PCA varimax',
                       self.pcaOutputVarimax)

    def plotMenu(self):
        bar = self.parent().menuBar()
        menu = bar.addMenu('Plot')

        trajMenu = menu.addMenu('Trajectories')
        trajMenu.addAction('Continuity',
                           self.plotContinuity)
        trajMenu.addAction('Length histogram',
                           self.plotLengthHistogram)

        positionMenu = menu.addMenu('Position')
        positionMenu.addAction('Spectrum density',
                               self.positionFrequencySpectrum)
        positionMenu.addAction('PCA scree plot',
                               self.positionScreePlot)
        positionMenu.addAction('PCA 3D plot',
                               self.positionPca3d)
        positionMenu.addAction('PCA distance vs time',
                               self.positionPcaDistance)
        positionMenu.addAction('PCA correlation',
                               self.positionPcaCorr)

        speedMenu = menu.addMenu('Speed')
        speedMenu.addAction('Spectrum density',
                            self.speedFrequencySpectrum)        
        speedMenu.addAction('PCA scree plot',
                            self.speedScreePlot)
        speedMenu.addAction('PCA 3D plot',
                            self.speedPca3d)
        speedMenu.addAction('PCA distance vs time',
                            self.speedPcaDistance)


        energyMenu = menu.addMenu('Energy')
        energyMenu.addAction('Energy vs Time',
                             self.plotEnergy)



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

    @updateDisplay
    @updateStatus
    def openDataFile(self):
        fn, x = QtGui.QFileDialog.getOpenFileName\
                (None, 'Open a CuteDots motion data file')
        if fn == '':
            return
        self.parent().loadDataFile(fn)

    @updateDisplay
    @updateStatus
    def importC3D(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a C3D data file')
        if fn == '':
            return
        progress = self.parent().mkProgress("Importing...")
        qtdFn = preprocess.ppC3D(fn, progress)
        self.parent().loadDataFile(qtdFn)

    @updateDisplay
    @updateStatus
    def importCSV(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a CSV data file')
        if fn == '':
            return
        progress = self.parent().mkProgress("Importing...")
        qtdFn = preprocess.ppCSV(fn, progress)
        self.parent().loadDataFile(qtdFn)

    @updateDisplay
    @updateStatus
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

# SIGNAL

    @warnIfNoDataLoaded
    @updateDisplay
    @updateStatus
    def lpFilter(self):
        cutOff, ok = QtGui.QInputDialog.getDouble(
            self.parent(), "Low pass filter cutoff frequency",
            "Cutoff (36.8% decay - Hz)", 10.0, 0.0, 1000.0)
        transform.LpFilterTrajData(self.parent().data, cutOff)

# ANALYSIS

    @warnIfNoDataLoaded
    def pcaOutput(self):
        html = pystats.pcaVarimax(self.parent().data, None, None)
        displayHtml(self.parent(), "Principal component analysis", html)

    @warnIfNoDataLoaded
    def pcaOutputVarimax(self):
        html = pystats.pcaVarimax(self.parent().data)
        displayHtml(self.parent(), "Principal component analysis", html)


# PLOTS

    @warnIfNoDataLoaded
    def plotContinuity(self):
        plots.continuity(self.newDataPlot())

    @warnIfNoDataLoaded
    def plotLengthHistogram(self):
        plots.lengthHistogram(self.newDataPlot())


    # Position

    @warnIfNoDataLoaded
    def positionFrequencySpectrum(self):
        plots.positionSpectrum(
            self.newDataPlot(),
            "Spectrum density of marker position")
    @warnIfNoDataLoaded
    def positionScreePlot(self):
        plots.scree(
            self.newDataPlot(),
            "Scree plot of marker position components")
    @warnIfNoDataLoaded
    def positionPca3d(self):
        plots.intPca3d(
            self.newDataPlot(),
            "PCA 3D plot of marker position components",
            None, pystats.varimax)

    def positionPcaDistance(self):
        plots.pcaDistance(
            self.newDataPlot(),
            "Subject distance vs. time in PCA space",
            None, pystats.varimax)

    def positionPcaCorr(self):
        plots.pcaCorr(
            self.newDataPlot(),
            "Correlation of PCA components",
            None, pystats.varimax)

    # Speed

    @warnIfNoDataLoaded
    def speedFrequencySpectrum(self):
        plots.speedSpectrum(
            self.newDataPlot(),
            "Spectrum density of marker speed")
    @warnIfNoDataLoaded
    def speedScreePlot(self):
        data = self.parent().data
        plots.scree(
            self.newDataPlot(),
            "Scree plot of marker speed components",
            analysis.speedFunc(data.framerate))
    @warnIfNoDataLoaded
    def speedPca3d(self):
        data = self.parent().data
        plots.intPca3d(
            self.newDataPlot(),
            "PCA 3D plot of marker speed components",
            analysis.speedFunc(data.framerate), pystats.varimax)

    def speedPcaDistance(self):
        data = self.parent().data
        plots.pcaDistance(
            self.newDataPlot(),
            "Subject distance vs. time in PCA space",
            analysis.speedFunc(data.framerate), pystats.varimax)

    @warnIfNoDataLoaded
    def plotEnergy(self):
        plots.energyVsTime(self.newDataPlot())
