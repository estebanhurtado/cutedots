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

from PySide import QtGui, QtOpenGL, QtCore
from PySide.QtCore import Qt

import modelops
import dotsio
import analysis
import preprocess
import os
import rstats

from plotdialog import DataPlot
from widgets import *

about_text = """
Copyright 2012 Esteban Hurtado

Cutedots is distributed under the terms of the Reciprocal Public License 1.5.

Cutedots is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the Reciprocal Public License 1.5 for more details.

You should have received a copy of the Reciprocal Public License along with Cutedots. If not, see <http://opensource.org/licenses/rpl-1.5>.
"""

keybindings = [
    ('Navigate frames', [
            ('next/prev. frame', 'arrows'),
            ]),
    ('View', [
            ('rotate','a d'),
            ('zoom', 's w'),
            ('reset view', '0'),
            ]),
    ('Curve selection', [
            ('select prev, next', 'f g'),
            ('unlabeled prev, next', 'r t'),
            ('select next break', 'b'),
            ]),
    ('Labeling', [
            ('subject', '1 2'),
            ('left, right', 'n m'),
            ('part prev, next', ', .'),
            ]),
    ('Modify', [
            ('split trajectory (cut)', 'c'),
            ('delete trajectory', 'z'),
            ('undelete trajectory', 'u'),
#            ('delete unassigned', 'k'),
            ]),
    ('Other', [
            ('super cool anaglyph :)', '3'),
            ])
]


def helptext():
    text = "<table>\n"
    for title, bindings in keybindings:
        text += '  <tr><th colspan="4" align="left">%s</th></tr>\n' % title
        for b in bindings:
            text += ('  <tr><td width="20px"></td><th align="left">%s</th>' + \
                         '<td width="20px"></td><td>%s</td></tr>\n') % b
        text += '<tr><td colspan=4></td></tr>\n'
    text += '</table>\n'
    return text


class CuteDotsMainWindow(QtGui.QMainWindow):
    "Qt object for Cutedots main window."

    @property
    def model(self):
        return self.gl.dots.model

    @property
    def data(self):
        return self.gl.dots.model.data

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.initUI()
        self.dataPlot = DataPlot(self)

    def initUI(self):
        self.initMenu()
        # Widgets
        self.mainWidget = QtGui.QWidget(self)        # Main widget
        self.gl = GLWidget(self)                     # 3D view
        self.transport = TransportBar(self, self.gl) # TransportBar
        self.help = QtGui.QLabel(helptext(), self)   # Keyboard help text
        # Layout
        self.setCentralWidget(self.mainWidget)
        self.mainLayout = QtGui.QVBoxLayout(self.mainWidget)
        self.hwidget = QtGui.QWidget(self)
        self.hlayout = QtGui.QHBoxLayout(self.hwidget)
        self.hlayout.addWidget(self.gl, 1)
        self.hlayout.addWidget(self.help)
        self.mainLayout.addWidget(self.hwidget, 1)
        self.mainLayout.addWidget(self.transport)
        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle("Cute dots")
        self.updateStatus()

    # Decorators
    ############

    def ifDataLoaded(method):
        "Decorator that executes method only if data is loaded"
        def deco(self, *args, **kargs):
            if self.data is None or self.data.empty:
                return
            method(self, *args, **kargs)
        return deco

    def ifFileOpened(method):
        "Decorator that executes method only if file was opened (but data could be empty)"
        def deco(self, *args, **kargs):
            if self.data is None:
                return
            method(self, *args, **kargs)
        return deco

    def warnIfNoDataLoaded(method):
        "Decorator that throws a warning if no data is already loaded."
        def deco(self, *args, **kargs):
            if self.data is None:
                QtGui.QMessageBox.warning(self, 'Error', 'No data loaded yet.')
                return
            method(self, *args, **kargs)
        return deco

    def updateDisplay(method):
        "Decorator that updates GL display after calling method."
        def deco(self, *args, **kargs):
            method(self, *args, **kargs)
            self.gl.updateGL()
        return deco

    def updateStatus(method):
        "Updates status after calling method."
        def deco(self, *args, **kargs):
            method(self, *args, **kargs)
            self.updateStatus()
        return deco

    def updateNumFrames(method):
        def deco(self, *args, **kargs):
            method(self, *args, **kargs)
            self.transport.setNumFrames(self.data.numFrames)
        return deco
        

    # End decorators #


    def mkMenu(self, menubar, name, elements):
        menu = menubar.addMenu(name)
        for element in elements:
            if element is None:
                menu.addSeparator()
            elif isinstance(element, QtGui.QMenu):
                menu.addMenu(element)
            else:
                menu.addAction(element)

    def subMenu(self, name, elements):
        menu = QtGui.QMenu(name)
        for element in elements:
            if element is None:
                menu.addSeparator()
            else:
                menu.addAction(element)
        return menu

    def mkProgress(self, task_descript, total=100, cancelbtn=""):
        progress = QtGui.QProgressDialog(
            task_descript, cancelbtn, 0, total, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Cutedots")
        if cancelbtn == "":
            progress.setCancelButton(None)
        return progress

    def mkAction(self, text, tip, handler, shortCut=None):
        act = QtGui.QAction(text, self)
        if not shortCut is None:
            act.setShortcut(shortCut)
        act.setStatusTip(tip)
        act.triggered.connect(handler)
        return act


    def initMenu(self):
        self.statusBar()
        # File
        loadAction = self.mkAction(
            '&Open motion data file...',
            'Open pickled trajectory data or import C3D file',
            self.openDataFile, 'Ctrl+O')
        importC3DAction = self.mkAction(
            '&Import C3D file...',
            'Read and trajectorize data from C3D file ' + \
            '(creates new CuteDots file on disk)',
            self.importC3D, 'Ctrl+I')
        importCSVAction = self.mkAction(
            '&Import CSV file...',
            'Read and trajectorize data from CSV file ' + \
            '(creates new CuteDots file on disk)',
            self.importCSV)
        importCSV2Action = self.mkAction('&Import CSV2 file...',
            'Read from CSV file using Motive <1.7', self.importCSV2)
        saveAction = self.mkAction(
            '&Save',
            'Save to HDF5 file (.qtd).',
            self.saveFile, 'Ctrl+S')
        saveAsAction = self.mkAction(
            'Save &as...',
            'Save to a different file',
            self.saveFileAs)
        saveSeqAction = self.mkAction(
            'Save image &sequence',
            'Save frame to frame image sequence of realtime motion' + \
            'from current view',
            self.saveSequence)
        exitAction = self.mkAction(
            'Save and e&xit',
            'Save and exit program',
            self.close, 'Ctrl+Q')
        # Operations
        ## Op utility
        guessAction = self.mkAction(
            'Guess side and subject',
            'Label side and subject based on horizontal quadrant',
            self.guessSideAndSubject)
        rotateAction = self.mkAction(
            'Rotate 90 degrees',
            'Rotate points 90 degrees in horizontal plane',
            self.rotate)
        swapAction = self.mkAction(
            'Swap subjects',
            'Exchange subjects 1 and 2',
            self.swap)
        sortAction = self.mkAction(
            'Sort trajectories by X coordinate',
            'Improves traject. traversal order for labeling',
            self.slowSort)
        ## Op fixes
        matchTrajsAction = self.mkAction(
            'Match trajectories',
            'Apply further trajectory matching',
            self.matchTrajectories, 'Ctrl+M')
        averageTrajsAction = self.mkAction(
            'Average same name trajectories',
            'Makes sure only one point exists at each frame for each trajectory name',
            self.averageTrajs)
        fillSmallGapsAction = self.mkAction(
            'Fill small gaps in trajectories',
            'Interpolates up to 0.2 seconds of missing frames in a trajectory.',
            self.fillSmallGaps)
        fillAllGapsAction = self.mkAction(
            'Fill all gaps in trajectories',
            'Interpolates all missing frames in trajectories.',
            self.fillAllGaps)
        ## Op remove trajectories
        removeUnassignedAction = self.mkAction(
            'Remove unassigned trajectories.',
            'Removes trajectories that are not completeley assigned.',
            self.removeUnassigned)
        removeShortAction = self.mkAction(
            'Remove short trajectories',
            'Removes trajectories shorter than specified threshold',
            self.removeShort)
        ## Op cut frames
        cutRightAction = self.mkAction(
            'Cut from this frame', '',
            self.cutRight)
        cutLeftAction = self.mkAction(
            'Cut before this frame', '',
            self.cutLeft)

        # Plot
        ## Trajectories
        plotContAction = self.mkAction(
            'Plot continuity',
            'Plot frame span of each trajectory',
            self.plotContinuity)
        lengthHistAction = self.mkAction(
            'Plot histogram of trajectory lengths', '',
            self.plotLengthHistogram)
        ## Motion
        plotEnergyAction = self.mkAction(
            'Plot energy',
            'Make global energy plot',
            self.plotEnergy)
        plotSpeedAction = self.mkAction(
            'Plot speed',
            'Plots speed for each axis.',
            self.plotSpeed)
        ## PCA
        pcaBiplotAction = self.mkAction(
            'Biplot (subjects as one)',
            'Project in first two axes of variance',
            self.pcaBiplot)
        pcaScreeAction = self.mkAction(
            'Scree plot (subjects as one)',
            'Show eigenvalues',
            self.pcaScree)
        pca3dPlotAction = self.mkAction(
            '3D plot (separate PCA fits for subjects)',
            'Plot observations projected on first three axes',
            self.pca3d, 'Ctrl+P')
        pca3dPlotTogetherAction = self.mkAction(
            '3D plot (same PCA fit for subjects)',
            'Plot observations projected on first three axes',
            self.pca3dTogether, 'Ctrl+P')
        pcaDistancePlotAction = self.mkAction(
            'PCA space distance between subjects vs time',
            'Between-subject euclidean distance of PCA scores vs time',
            self.pcaDistancePlot)
        pcaLoadingsAction = self.mkAction(
            'PCA loadings (two subjects in separate variables)',
            'PCA loadings',
            self.pcaLoadings)
        xcorrAction = self.mkAction(
            'Cross-correlation',
            'Produce cross-correlation plot for files in a folder',
            self.plotCrossCorrelation)
        # Other
        exitNoSaveAction = self.mkAction(
            'Exit without saving', 'Exit the program', self.exitNoSave)
        # Help
        aboutAction = self.mkAction('&About', 'About', self.displayAboutDlg)
        # Menu bar
        menubar = self.menuBar()
        self.mkMenu(menubar, '&File',
                    [loadAction, importC3DAction, importCSVAction, importCSV2Action, None,
                     saveAction, saveAsAction, saveSeqAction, None,
                     exitAction, exitNoSaveAction])
        self.mkMenu(menubar, '&Operations',
                    [rotateAction, swapAction, guessAction, sortAction, None,
                     matchTrajsAction, averageTrajsAction, fillSmallGapsAction,
                     fillAllGapsAction, None,
                     removeUnassignedAction, removeShortAction, None,
                     cutRightAction, cutLeftAction])
        self.mkMenu(menubar, '&Plot', [
            self.subMenu("Trajectory lengths", [plotContAction, lengthHistAction]),
            self.subMenu("Motion", [plotEnergyAction, plotSpeedAction]),
            self.subMenu("Principal component analysis",
                         [pcaScreeAction, pcaBiplotAction, pca3dPlotAction,
                          pca3dPlotTogetherAction, pcaDistancePlotAction,
                          pcaLoadingsAction])])
        self.mkMenu(menubar, '&Help', [aboutAction])

    # Actions
    #########

    def displayAboutDlg(self):
        QtGui.QMessageBox.about(self, 'About', about_text)

    def openDataFile(self):
        fn, x = QtGui.QFileDialog.getOpenFileName\
                (None, 'Open a CuteDots motion data file')
        time.sleep(0.2)
        if fn == '':
            return
        self.loadDataFile(fn)

    @updateStatus
    @updateNumFrames
    def loadDataFile(self, fn):
        if self.data is not None and self.data.changed:
            self.saveFile()
        progress = self.mkProgress("Loading C3D...", 100, "Cancel")
        self.gl.dots.loadData(fn, progress)
        progress.close()
        progress.destroy()
        del progress
        modelops.sortTrajs(self.data)
        self.setWindowTitle("Cute dots - " + fn)

    def importC3D(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a C3D data file')
        if fn == '':
            return
        progress = self.mkProgress("Importing...")
        qtdFn = preprocess.ppC3D(fn, progress)
        progress.close()
        progress.destroy()
        del progress
        self.loadDataFile(qtdFn)

    def importCSV(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a CSV data file')
        if fn == '':
            return
        progress = self.mkProgress("Importing...")
        qtdFn = preprocess.ppCSV(fn, progress)
        progress.close()
        progress.destroy()
        del progress
        self.loadDataFile(qtdFn)

    def importCSV2(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Import a CSV2 data file')
        if fn == '':
            return
        progress = self.mkProgress("Importing...")
        qtdFn = preprocess.ppCSV2(fn, progress)
        progress.close()
        del progress
        self.loadDataFile(qtdFn)

    @ifDataLoaded
    def saveFile(self):
        if self.data.changed:
            progress = self.mkProgress("Saving...", 100, "Cancel")
            dotsio.trajDataSaveH5(self.data, progress)
            self.data.changed = False
            progress.close()
            progress.destroy()
            del progress

    @ifDataLoaded
    def saveFileAs(self):
        fn,x = QtGui.QFileDialog.getOpenFileName(None, 'Save motion data file')
        if fn == '':
            return
        self.data.changed = True
        self.data.filename = fn 
        self.saveFile()


    @warnIfNoDataLoaded
    def saveSequence(self):
        folder = QtGui.QFileDialog.getExistingDirectory(
            self, 'Choose a folder to save image files for the video sequence')
        if folder == '':
            return
        progress = self.mkProgress(
            "Generating images...", self.data.numFrames, "Stop")
        period = 100. / 30.
        step = 0
        frameNum = 0
        while frameNum < 6000:
            self.model.frame = frameNum
            self.gl.updateGL()
            self.updateStatus()
            self.gl.grabFrameBuffer().save(
                os.path.join(folder,'frame%06d.jpg' % step), None, 90)
            step += 1
            frameNum = int(step * period)
            if progress.wasCanceled():
                break
            progress.setValue(frameNum)
        progress.setValue(self.model.numFrames)
        progress.close()
        progress.destroy()
        del progress

    @warnIfNoDataLoaded
    @updateDisplay
    def guessSideAndSubject(self):
        modelops.guessSideAndSubject(self.data)

    @warnIfNoDataLoaded
    @updateDisplay
    def matchTrajectories(self):
        threshold, ok = QtGui.QInputDialog.getInteger(
            self, "Match trajectories", "Distance threshold (mm)", 20, 0, 1000)
        if not ok:
            return
        maxGap, ok = QtGui.QInputDialog.getInteger(
            self, "Match trajectories", "Max. frame gap", 5, -100, 1000)
        if not ok:
            return
        minGap, ok = QtGui.QInputDialog.getInteger(
            self, "Match trajectories", "Min. frame gap", 0, -100, 1000)
        if not ok:
            return

        progress = self.mkProgress("Matching trajectories")
        modelops.matchTrajectories(self.data, threshold, maxGap, progress)

    @warnIfNoDataLoaded
    @updateDisplay
    def rotate(self):
        progress = self.mkProgress("Rotating 90 degrees...")
        modelops.rotate90Deg(self.data, progress)
        progress.close()
        progress.destroy()
        del progress

    @warnIfNoDataLoaded
    @updateDisplay
    def swap(self):
        progress = self.mkProgress("Swapping subjects...")
        modelops.swapSubjects(self.data, progress)
        progress.close()
        progress.destroy()
        del progress

    @warnIfNoDataLoaded
    @updateDisplay
    @updateStatus
    def averageTrajs(self):
        progress = self.mkProgress("Averaging same name trajectories...")
        modelops.averageSameNameTrajectories(self.data, progress)
        progress.close()
        progress.destroy()
        del progress

    @warnIfNoDataLoaded
    @updateDisplay
    def sort(self):
        modelops.sortTrajs(self.data)

    @warnIfNoDataLoaded
    @updateDisplay
    def slowSort(self):
        modelops.sortTrajsSlow(self.data)

    @warnIfNoDataLoaded
    def plotContinuity(self):
        self.dataPlot.plotContinuity(self.data)
    @warnIfNoDataLoaded
    def plotEnergy(self):
        analysis.plotEnergy(self.data)
    @warnIfNoDataLoaded
    def plotSpeed(self):
        analysis.plotSpeed(self.data)
    @warnIfNoDataLoaded
    def plotLengthHistogram(self):
        analysis.plotLengthHistAll(self.data)

    @warnIfNoDataLoaded
    def plotCrossCorrelation(self):
        pass

    @warnIfNoDataLoaded
    def pcaScree(self):
        rstats.pcaScreePlot(self.data)
    @warnIfNoDataLoaded
    def pcaBiplot(self):
        rstats.pcaBiplot(self.data)
    @warnIfNoDataLoaded
    def pca3d(self):
        rstats.pca3dPlot(self.data)
    @warnIfNoDataLoaded
    def pca3dTogether(self):
        rstats.pca3dPlotTogether(self.data)
    @warnIfNoDataLoaded
    def pcaDistancePlot(self):
        rstats.pcaDistancePlot(self.data)
    @warnIfNoDataLoaded
    def pcaLoadings(self):
        rstats.pcaLoadings(self.data)

    @warnIfNoDataLoaded
    @updateStatus
    def fillSmallGaps(self):
        progress = self.mkProgress("Filling small gaps...")
        modelops.fillGaps(self.data, 0.2, 0.2, progress)
        progress.close()
        progress.destroy()
        del progress
    @warnIfNoDataLoaded
    @updateStatus
    def fillAllGaps(self):
        progress = self.mkProgress("Filling all gaps...")
        modelops.fillGaps(self.data, self.data.numFrames / self.data.framerate,
                          0.2, progress)
        progress.close()
        progress.destroy()
        del progress

    @warnIfNoDataLoaded
    @updateNumFrames
    @updateStatus
    def cutRight(self):
        self.model.cutRight()

    @warnIfNoDataLoaded
    @updateNumFrames
    @updateStatus
    def cutLeft(self):
        self.model.cutLeft()

    @warnIfNoDataLoaded
    @updateStatus
    def removeUnassigned(self):
        self.model.deleteUnassigned()

    @warnIfNoDataLoaded
    @updateStatus
    def removeShort(self):
        minLength, ok = QtGui.QInputDialog.getInteger(
            self, "Remove short trajectories", "Minimum length (frames)", 10, 0)
        if not ok:
            return
        self.model.deleteShort(minLength)

    # End actions #

    def exitNoSave(self):
        if self.data is not None:
            changed = self.data.changed
            if changed:
                reply = QtGui.QMessageBox.question(
                    self, 'Message', "Are you sure you want to lose unsaved data?", 
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                    QtGui.QMessageBox.Cancel)
                if reply == QtGui.QMessageBox.Cancel:
                    return
            self.data.changed = False
        self.close()
        if self.data is not None:
            self.data.changed = changed

    def closeEvent(self, event):
        self.saveFile()
        event.accept()

    def keyPressEvent(self, e):
        self.gl.keyPressEvent(e)

    @updateDisplay
    @updateStatus
    def setFrame(self, numFrame):
        self.model.frame = numFrame

    def updateFrame(self):
        self.transport.setFrame(self.model.frame)

    @ifFileOpened
    def updateStatus(self):
        if self.model.data.empty:
            msg = "No data loaded from file"
            self.statusBar().showMessage(msg)
            return
        msg = "Frame: %d   |   Num. points: %d   |  traj: %d of %d   |   " % (
            self.model.frame,
            self.data.numPoints(self.model.frame),
            self.model.traj,
            self.data.numTrajs)
        msg += self.model.humanReadPart()
        traj = self.model.currentTraj()
        frame = self.model.frame
        if (traj.hasFrame(frame)):
            point = traj.getFrame(frame)
            msg += " at (%.0f, %.0f, %.0f)" % tuple(point)
            self.statusBar().showMessage(msg)
        else:
            msg += " (not in this frame)"
            self.statusBar().showMessage(msg)
