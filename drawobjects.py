from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np

FLOOR_COLOR = tuple(np.array([69., 78., 178., 1.0]) / (255.))


def drawWall(width, height, hdivs, vdivs):
  hdiv = float(width) / float(hdivs)
  vdiv = float(height) / float(vdivs)
  glColor(1., 1., 1., .2)
  glBegin(GL_LINES)
  glNormal3f(0.0, 0.0, -1.0)
  # draw vertical lines
  for i in range(hdivs+1):
      x = -width/2. + i*hdiv
      for j in range(vdivs):
          y = -height/2. + j*vdiv
          glVertex2f(x, y)
          glVertex2f(x, y+vdiv)
  # draw horizontal lines
  for j in range(vdivs+1):
      y = -height/2. + j*vdiv
      for i in range(hdivs):
          x = -width/2. + i*hdiv
          glVertex2f(x, y)
          glVertex2f(x+hdiv, y)
  glEnd()

def drawFloor():
    glLineWidth(1)
    glColor4f(0.067647058823529407, 0.076470588235294124, 0.17450980392156862,1.0)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.0,0.0,0.0,1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 0.0)
    glBegin(GL_QUADS)
    glVertex(2500, 2500)
    glVertex(2500, -2500)
    glVertex(-2500, -2500)
    glVertex(-2500, 2500)
    glEnd()

def drawSideWall(tx, ty, tz, rx, ry, rz, w, h, hdivs, vdivs):
    glPushMatrix()
    glTranslatef(tx, ty, tz)
    glRotatef(90.0, rx, ry, rz)
    drawWall(w, h, hdivs, vdivs)
    glPopMatrix()

def drawWalls():
    glLineWidth(1)
    drawSideWall(0.0, 2500.0, 1250.0, 1.0, 0.0, 0.0, 5000.0, 2500.0, 20, 10)
    drawSideWall(0.0, -2500.0, 1250.0, -1.0, 0.0, 0.0, 5000.0, 2500.0, 20, 10)
    drawSideWall(2500.0, 0.0, 1250.0, 0.0, -1.0, 0.0, 2500.0, 5000.0, 10, 20)
    drawSideWall(-2500.0,0.0, 1250.0, 0.0, 1.0, 0.0, 2500.0, 5000.0, 10, 20)

def drawChairs():
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.2,0.2,0.2,1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 100.0)
    glPushMatrix()
    glColor4f(0.06, 0.06, 0.06, 1.0)
    glTranslatef(-700, 0, 225)
    glutSolidCube(450)
    glTranslatef(1400, 0, 0)
    glutSolidCube(450)
    glPopMatrix()

def setupDrawing(width, height):

    # Set model
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.4, 0.2, 0.15, 1.0)
    glEnable(GL_DEPTH_TEST)

    # Lighting
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_LIGHT2)
    glEnable(GL_LIGHT3)

    light_pos = ( 0.0, 0.0, 1800.0, 1.0 )
    ambient = ( 0.3, 0.3, 0.3, 1.0 )
    diffuse = ( 1.0, 1.0, 1.0, 1.0 )
    specular = ( 1.0, 1.0, 1.0, 1.0 )

    def light(id, position):
      glLightfv(id, GL_POSITION, position)
      glLightfv(id, GL_AMBIENT, ambient)
      glLightfv(id, GL_DIFFUSE, diffuse)
      glLightfv(id, GL_SPECULAR, specular)
    #    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.00012)

    light(GL_LIGHT0, (2500,2500,2500))
    light(GL_LIGHT1, (2500,2500,-2500))
    light(GL_LIGHT2, (-2500,2500,-2500))
    light(GL_LIGHT3, (-2500,2500,2500))

    # Smoothing
    glEnable(GL_LINE_SMOOTH)
#    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
    glShadeModel(GL_SMOOTH)

    # Transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Polygons
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

def drawSingleHead(x1, y1, z1, x2, y2, z2, x3, y3, z3):
    a = np.array([x3 - x1, y3 - y1, z3 - z1])
    b = np.array([x2 - x1, y2 - y1, z2 - z1])
    totaln = np.crossprod(a, b)
    n = totaln / np.linalg.norm(totaln)
    if (x1 * n[0]):
        n = n * (-1, -1, -1)
    xm = (x1 + x2 + x3) / 3.
    ym = (y1 + y2 + y3) / 3.
    zm = (z1 + z2 + z3) / 3.
    vm = np.array([xm, ym, zm])
    p = vm + 80 * n
    glPushMatrix()
    glTranslatef(p)
    glutSolidSphere(100, 20, 20)
    glPopMatrix()

def drawTorso(xa, ya, za, xb, yb, zb, xc, yc, zc, xd, yd, zd):
    pass
