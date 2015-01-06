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

# Display size
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 600


from PySide import QtGui, QtOpenGL, QtCore
from PySide.QtCore import Qt
import dotsdisplay as dots
import time

class GLWidget(QtOpenGL.QGLWidget):
    "Qt Widget for showing OpenGL graphics"

    def __init__(self, parent):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.parentWindow = parent
        self.setMinimumSize(640, 480)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateGL)
        self.timer.timeout.connect(self.parent().updateFrame)
        self.timer.timeout.connect(self.parent().updateStatus)
        self.setFocusPolicy(Qt.StrongFocus)
        self.dots = dots.DotsDisplay(self.getTextRenderFunc())
        

    def getTextRenderFunc(self):
        return lambda s: self.renderText(0.0, 0.0, 0.0, s)

    def paintGL(self)        : self.dots.display()
    def resizeGL(self, w, h) : self.dots.reshape(w, h)
    def initializeGL(self)   : self.dots.setupViewport(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    def togglePlay(self):
        self.parentWindow.transport.togglePlay()
 
    def keyPressEvent(self, e):
        key = e.key()
        model = self.dots.model
        # Change frame
        if key == Qt.Key_Right:    model.frame = min(model.frame+1, model.data.numFrames-1)
        elif key == Qt.Key_Left:   model.frame = max(model.frame-1, 0)
        # Rotation
        elif   key == Qt.Key_A:    model.cam.rotation -= 4
        elif key == Qt.Key_D:      model.cam.rotation += 4
        # Zoom
        elif key == Qt.Key_S:      model.cam.py -= 50  
        elif key == Qt.Key_W:      model.cam.py += 50
        # Curve selection
        elif key == Qt.Key_R:      model.selPrevUnlabTraj()
        elif key == Qt.Key_T:      model.selNextUnlabTraj()
        elif key == Qt.Key_F:      model.selPrevTraj()
        elif key == Qt.Key_G:      model.selNextTraj()
        elif key == Qt.Key_B:      model.selNextBreak()
        # Anaglyph
        elif key == Qt.Key_3:      model.anaglyph3d=not model.anaglyph3d
        # Cam reset
        elif key == Qt.Key_0:      model.cam.reset()
        # Curve labeling
        elif key == Qt.Key_1:      model.labelSubject(1)
        elif key == Qt.Key_2:      model.labelSubject(2)
        elif key == Qt.Key_N:      model.labelSide('L')
        elif key == Qt.Key_M:      model.labelSide('R')
        elif key == Qt.Key_Comma:  model.labelPartPrev()
        elif key == Qt.Key_Period: model.labelPartNext()
        # Curve splitting (cut)
        elif key == Qt.Key_C:      model.data.splitTraj(model.currentTraj(), model.frame) 
       # Curve deletion
        elif key == Qt.Key_Z:      model.deleteCurrent()
        elif key == Qt.Key_U:      model.undelete()
#        elif key == Qt.Key_K:      model.deleteUnassigned()
        elif key == Qt.Key_Space:  self.togglePlay()
        self.updateGL()
        self.parentWindow.updateStatus()
        self.parentWindow.updateFrame()

class FrameSpin(QtGui.QSpinBox):
    def __init__(self, parent):
        QtGui.QSpinBox.__init__(self, parent)
        self.setWrapping(True)
        self.setAccelerated(True)

    def textFromValue(self, val):
        mins = val / 6000
        secs = (val / 100) % 60
        frames = val % 100
        return "%02d':%02d\".%02d" % (mins, secs, frames)


class TransportBar(QtGui.QWidget):
    def __init__(self, parent, glwidget):
        QtGui.QWidget.__init__(self, parent)
        self.mainWindow = parent
        self.gl = glwidget
        self.playing = False
        self.refFrame = 0
        self.refTime = 0.0
        self.playSpeed = 1.0
        self.initUI()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.playButton.released.connect(self.togglePlay)

    def initUI(self):
        # Get play/pause icons
        standardIcon = QtGui.qApp.style().standardIcon
        self.iconPlay = standardIcon(QtGui.QStyle.SP_MediaPlay)
        self.iconPause = standardIcon(QtGui.QStyle.SP_MediaPause)
        # Widgets
        self.playButton = QtGui.QPushButton(self.iconPlay, '', self)
        s1 = self.speed1xButton = QtGui.QToolButton(self)
        s1.setText('1x')
        s2 = self.speed4xButton = QtGui.QToolButton(self)
        s2.setText('4x')
        s3 = self.speed16xButton = QtGui.QToolButton(self)
        s3.setText('16x')
        self.frameSpin = FrameSpin(self)
        self.frameSlider = QtGui.QSlider(Qt.Horizontal, self)
        self.labelTotal = QtGui.QLabel(self)
        # Button group
        buttonGroup = QtGui.QButtonGroup(self)
        for button in [s1, s2, s3]:
            button.setCheckable(True)
            buttonGroup.addButton(button)
        s1.setChecked(True)
        # Layouts
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.playButton)
        layout.addWidget(self.speed1xButton)
        layout.addWidget(self.speed4xButton)
        layout.addWidget(self.speed16xButton)
        layout.addWidget(self.frameSpin)
        layout.addWidget(self.frameSlider)
        layout.addWidget(self.labelTotal)
        # Signals
        self.frameSpin.valueChanged.connect(self.frameSlider.setValue)
        self.frameSpin.valueChanged.connect(self.parent().setFrame)
        self.frameSlider.valueChanged.connect(self.frameSpin.setValue)
        self.speed1xButton.clicked.connect(self.setSpeed)
        self.speed4xButton.clicked.connect(self.setSpeed)
        self.speed16xButton.clicked.connect(self.setSpeed)

    def setReference(method):
        def deco(self, *args, **kargs):
            self.refFrame = self.gl.dots.model.frame
            self.refTime = time.time()
            method(self, *args, **kargs)
        return deco

    @setReference
    def play(self):
        self.playing = True
        self.playButton.setIcon(self.iconPause)
        self.timer.start(25)

    @setReference
    def setSpeed(self):
        if self.speed1xButton.isChecked():
            self.playSpeed = 1.0
        elif self.speed4xButton.isChecked():
            self.playSpeed = 4.0
        elif self.speed16xButton.isChecked():
            self.playSpeed = 16.0

    def stop(self):
        self.timer.stop()
        self.playing = False
        self.playButton.setIcon(self.iconPlay)

    def togglePlay(self):
        if self.playing: self.stop()
        else:            self.play()

    def update(self):
        t = time.time()
        model = self.gl.dots.model
        if model.data.empty:
            return
        fr = model.data.frameRate * self.playSpeed
        model.frame = int(self.refFrame + (t - self.refTime) * fr) % model.data.numFrames
        self.gl.updateGL()
        self.mainWindow.updateFrame()
        self.mainWindow.updateStatus()

    def setNumFrames(self, numFrames):
        self.frameSpin.setRange(0, numFrames-1)
        self.frameSlider.setRange(0, numFrames-1)
        self.labelTotal.setText(self.frameSpin.textFromValue(numFrames-1))

    def setFrame(self, numFrame):
        spinBlocked = self.frameSpin.blockSignals(True)
        sliderBlocked = self.frameSlider.blockSignals(True)
        self.frameSpin.setValue(numFrame)
        self.frameSlider.setValue(numFrame)
        self.frameSpin.blockSignals(spinBlocked)
        self.frameSlider.blockSignals(sliderBlocked)
