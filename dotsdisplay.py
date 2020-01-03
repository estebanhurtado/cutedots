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

import modelstate
import camstate
from trajdata import TrajData
import modelops
import dotsio
import sys
import os
import drawobjects as drObj

import OpenGL
OpenGL.ERROR_CHECKING = False

from OpenGL.GL import *
from OpenGL.GLU import *
#from OpenGL.GLUT import *

class OpenFileEx(Exception):
    def __init__(self, filename, msg='Unknown error.'):
        Exception.__init__(self, "Could not read motion data from file '%s': %s" % \
                               (filename, msg))


class DotsDisplay:

    def __init__(self, textRenderFunc=lambda s: None):
        self.model = modelstate.ModelState()
        self.textRenderFunc = textRenderFunc
        self.renderText = True

    def drawText(self, s):
        glDisable(GL_DEPTH_TEST);
        self.textRenderFunc(s)
        glEnable(GL_DEPTH_TEST);

    def subjColor(self, subj, alpha):
        "Enable color for specified subject."
        if   subj == '1':  glColor4f(0.9, 0.9, 0.4, alpha)
        elif subj == '2':  glColor4f(0.6, 0.3, 1.0, alpha)
        else:              glColor4f(0.5, 0.5, 0.5, alpha)

    def drawElement(self, traj):
        "Draw marker for given trajectory."
        n = traj.name
        side, subj = n[2], n[3]
        self.subjColor(subj, 1.0)
        if   side == 'L':  drObj.drawSolidSphere(18, 20, 20)
        elif side == 'R':  drObj.drawSolidCube(30)
        else:              drObj.drawSolidSphere(8, 20, 20)

    def drawElements(self, frame):
        "Draw all markers."
        self.model.trajMap = {}
        for traj in self.model.data.trajs:
            if traj.hasFrame(frame):
                glPushMatrix()
                px, py, pz = traj.getFrame(frame)
                self.model.map(traj.name, px, py, pz)
                glTranslatef(px,py,pz)
                self.drawElement(traj)
                glPopMatrix()

    def drawHeads(self, frame):
        "Draw heads."
        for subj in ['1', '2']:
            trajs = [t for t in self.model.data.trajs 
                     if t.name[:2] == 'Hd'
                     and t.name[3] == subj
                     and t.hasFrame(frame)]
            if len(trajs) >= 3:
                p1 = trajs[0].getFrame(frame)
                p2 = trajs[1].getFrame(frame)
                p3 = trajs[2].getFrame(frame)
                x1,y1,z1 = p1
                x2,y2,z2 = p2
                x3,y3,z3 = p3
                self.subjColor(subj, self.model.bodyTrans)
                drObj.drawSingleHead(x1, y1, z1, x2, y2, z2, x3, y3, z3)

    def drawSelSquare(self, frame):
        "Draw selection square and write label."
        if self.model.data.empty:
           return
        traj = self.model.currentTraj()
        if traj.hasFrame(frame):
            glPushMatrix()
            px, py, pz = traj.getFrame(frame)
            glTranslatef(px,py,pz)
            glLineWidth(1)
            # Square
            glDisable(GL_LIGHTING)
            glBegin(GL_LINE_LOOP)
            glColor3f(1,1,1)
            glVertex3f(-30, 0, -30)
            glVertex3f(-30, 0, 30)
            glVertex3f(30, 0, 30)
            glVertex3f(30, 0, -30)
            glEnd()
            # Text
            glTranslatef(0, 0, 120)
            if self.renderText:
                self.drawText(self.model.humanReadPart())
            glEnable(GL_LIGHTING)
            glPopMatrix()

    def drawLine(self, tr1, tr2):
        "Draw a line between points with given labels."
        tmap = self.model.trajMap
        if tr1 in tmap and tr2 in tmap:
            x1,y1,z1 = tmap[tr1]
            x2,y2,z2 = tmap[tr2]
            glBegin(GL_LINE_STRIP)
            glVertex3f(x1,y1,z1)
            glVertex3f(x2,y2,z2)
            glEnd()

    def drawLines(self):
        "Draw lines between body parts for arms and legs."
        model = self.model
        tmap = model.trajMap

        for subj in ['1','2']:
            self.subjColor(subj, model.bodyTrans)
            for side in ['L','R']:
                glLineWidth(15)
                self.drawLine('UB'+side+subj, 'El'+side+subj) # arms
                self.drawLine('El'+side+subj, 'Hn'+side+subj)
                glLineWidth(25)
                self.drawLine('LB'+side+subj, 'Kn'+side+subj) # legs
                self.drawLine('Kn'+side+subj, 'Ft'+side+subj)
            a, b, c, d = 'UBL'+subj, 'UBR'+subj, 'LBR'+subj, 'LBL'+subj
            if a in tmap and b in tmap and c in tmap and d in tmap:
                xa,ya,za = model.trajMap[a];
                xb,yb,zb = model.trajMap[b];
                xc,yc,zc = model.trajMap[c];
                xd,yd,zd = model.trajMap[d];
                drObj.drawTorso(xa,ya,za, xb,yb,zb, xc,yc,zc, xd,yd,zd);

    def locateCamera(self, cam):
        "Set projection; cam=0: normal,-1: left eye, 1:right eye"
        c = self.model.cam
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(c.px + cam * c.half_eye_sep, c.py, c.pz, c.rx, c.ry, c.rz, 0,0,1)

    def rotateScene(self):
        "Rotate scene."
        glRotatef(self.model.cam.rotation, 0, 0, 1)

    def draw(self):
        "Draw everything for current frame."
        frame = self.model.frame
        glPushMatrix()
        self.rotateScene()
        glColor3f(0.2, 0.2, 0.4)
        drObj.drawFloor()
        drObj.drawWalls()
        drObj.drawChairs()
        glColor3f(.8, .8, .8)
        if self.model.data is not None:
            self.drawElements(frame)
            self.drawHeads(frame)
            self.drawLines()
            self.drawSelSquare(frame)
        glPopMatrix()

    def display(self):
        "Display func"
        glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glPushMatrix()
        # Draw scene first time
        if self.model.anaglyph3d:
            glColorMask(GL_TRUE,GL_FALSE,GL_FALSE,GL_TRUE)
            self.locateCamera(-1)
            self.renderText = False
        else:
            self.locateCamera(0)
        self.draw()
        self.renderText = True
        # Draw second time
        if self.model.anaglyph3d:
            glClear(GL_DEPTH_BUFFER_BIT)
            glColorMask(GL_FALSE,GL_TRUE,GL_TRUE,GL_TRUE)
            self.locateCamera(1)
            self.draw()
        glPopMatrix()

    def loadData(self, datafilename, progress):
        "Load data from HDF5 file."
        if sys.version < '3':
            datafilename = datafilename.encode('utf-8', 'ignore')
        datafilename = str(datafilename)
        if datafilename is None or datafilename == '':
            return
        # Check that file exists
        if not os.path.isfile(datafilename):
            raise OpenFileEx(datafilename, 'File not found.')
        # Load
        progress.setLabelText("Loading motion data")
        data = dotsio.trajDataFromH5(datafilename, progress)
        self.model = modelstate.ModelState(data)
        modelops.sortTrajs(self.model.data)

    def setupViewport(self, width, height):
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        gluPerspective(60.0, float(width)/height, 10.0, 10000.0);
        drObj.setupDrawing(width, height)

    def reshape(self, w, h):
        self.model.width = w
        self.model.height = h
        self.model.aspect = float(w) / h
        glViewport(0, 0, w, h)
        self.setupViewport(w, h)
