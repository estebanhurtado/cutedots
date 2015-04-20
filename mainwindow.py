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


import os

from PySide import QtGui, QtOpenGL, QtCore
from PySide.QtCore import Qt
import dotsio
import modelops
#import rstats
import actions
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
        self.cdActions = actions.CuteDotsActions(self)
        self.initUI()


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

    def mkProgress(self, task_descript, total=100, cancelbtn=""):
        progress = QtGui.QProgressDialog(
            task_descript, cancelbtn, 0, total, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Cutedots")
        if cancelbtn == "":
            progress.setCancelButton(None)
        return progress

    def initMenu(self):
        self.statusBar()
        self.cdActions.makeMenus()

    # Actions
    #########

    def displayAboutDlg(self):
        QtGui.QMessageBox.about(self, 'About', about_text)
 
    @updateStatus
    @updateNumFrames
    def loadDataFile(self, fn):
        if self.askSave():
            self.saveFile()
        progress = self.mkProgress("Loading C3D...", 100, "Cancel")
        self.gl.dots.loadData(fn, progress)
        progress.close()
        progress.destroy()
        del progress
        modelops.sortTrajs(self.data)
        self.setWindowTitle("Cute dots - " + fn)


    @ifDataLoaded
    def saveFile(self):
        if self.data.changed:
            progress = self.mkProgress("Saving...", 100, "Cancel")
            dotsio.trajDataSaveH5(self.data, progress)
            self.data.changed = False

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

    def askSave(self):
        if self.data is not None and self.data.changed:
            answer = QtGui.QMessageBox.question(
                self, "Exit", "Data modified. Save to disk?",
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            return answer == QtGui.QMessageBox.Yes
        return False

    def closeEvent(self, event):
        if self.askSave():
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

        if self.model.frame >= self.data.numFrames:
            self.model.frame = self.data.numFrames - 1
        if self.model.traj >= len(self.data.trajs):
            self.model.traj = len(self.data.trajs) - 1
        msg = "Frame: %d   |   Num. points: %d   |  traj: [%s] %d of %d   |   " % (
            self.model.frame,
            self.data.numPoints(self.model.frame),
            self.model.data.trajs[self.model.traj],
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
