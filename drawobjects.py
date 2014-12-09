from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

def drawWall(width, height, hdivs, vdivs):
  hdiv = width / hdivs
  vdiv = height / vdivs
  glBegin(GL_LINES)
  glNormal3f(0.0, 0.0, -1.0)
  # draw vertical lines
  for i in range(hdivs+1):
      x = -width/2 + i*hdiv
      for j in range(vdivs):
          y = -height/2 + j*vdiv
          glVertex2f(x, y)
          glVertex2f(x, y+vdiv)
  # draw horizontal lines
  for i in range(vdivs+1):
      y = -height/2 + j*vdiv
      for i in range(hdivs):
          x = -width/2 + i*hdiv
          glVertex2f(x, y)
          glVertex2f(x+hdiv, y)
  glEnd()

def drawFloor():
    glLineWidth(1)
    glColor3f(0.7,0.7,0.7)
    drawWall(5000, 5000, 20, 20)

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
    glPushMatrix()
    glColor4f(0.1, 0.1, 0.1, 1.0)
    glTranslatef(-700, 0, 225)
    glutSolidCube(450)
    glTranslatef(1400, 0, 0)
    glutSolidCube(450)
    glPopMatrix()

def setupDrawing(width, height):
    light_pos = ( 0.0, 0.0, 1800.0, 1.0 )
    ambient = ( 0.2, 0.2, 0.2, 1.0 )
    diffuse = ( 1.0, 1.0, 1.0, 1.0 )
    specular = ( 1.0, 1.0, 1.0, 1.0 )
    mat_specular = ( 1.0, 1.0, 1.0 )

    # Set model
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glEnable(GL_DEPTH_TEST)

    # Lighting
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.00012)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 40.0)

    # Smoothing
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
    glShadeModel(GL_SMOOTH)

    # Transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def drawSingleHead(x1, y1, z1, x2, y2, z2, x3, y3, z3):
    pass

def drawTorso(xa, ya, za, xb, yb, zb, xc, yc, zc, xd, yd, zd):
    pass
