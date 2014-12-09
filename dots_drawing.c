// Copyright 2012 Esteban Hurtado
//
// This file is part of Cutedots.
//
// Cutedots is distributed under the terms of the Reciprocal Public License 1.5.
//
// Cutedots is distributed in the hope that it will be useful, but WITHOUT ANY
// WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
// A PARTICULAR PURPOSE.  See the Reciprocal Public License 1.5 for more details.
//
// You should have received a copy of the Reciprocal Public License along with
// Cutedots. If not, see <http://http://opensource.org/licenses/rpl-1.5>.

#include <GL/gl.h>
#include <GL/glu.h>

#include "dots_drawing.h"

// Setup
////////

void setup_drawing(int width, int height)
{
  float light_pos[] = { 0.0f, 0.0f, 1800.0f, 1.0f };
  float ambient[] = { 0.2f, 0.2f, 0.2f, 1.0f };
  float diffuse[] = { 1.0f, 1.0f, 1.0f, 1.0f };
  float specular[] = { 1.0f, 1.0f, 1.0f, 1.0f };
  float mat_specular[] = { 1.0f, 1.0f, 1.0f };

  // Set model
  glMatrixMode(GL_MODELVIEW);
  glClearColor(0.0, 0.0, 0.0, 0.0);
  glEnable(GL_DEPTH_TEST);

  // Lighting
  glEnable(GL_COLOR_MATERIAL);
  glEnable(GL_LIGHTING);
  glEnable(GL_LIGHT0);
  glLightfv(GL_LIGHT0, GL_POSITION, light_pos);
  glLightfv(GL_LIGHT0, GL_AMBIENT, ambient);
  glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse);
  glLightfv(GL_LIGHT0, GL_SPECULAR, specular);
  glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.00012);
  glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular);
  glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 40.0);

  // Smoothing
  glEnable(GL_LINE_SMOOTH);
  glEnable(GL_POLYGON_SMOOTH);
  glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST);
  glShadeModel(GL_SMOOTH);

  // Transparency
  glEnable(GL_BLEND);
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
}


/// Primitives
//////////////

void drawSolidSphere(double radius, int slices, int stacks)
{
  glBegin(GL_LINE_LOOP);
  GLUquadricObj* quadric = gluNewQuadric();

  gluQuadricDrawStyle(quadric, GLU_FILL);
  gluQuadricNormals(quadric, GLU_SMOOTH);
  gluSphere(quadric, radius, slices, stacks);

  gluDeleteQuadric(quadric);
  glEnd();
}

void drawSolidCube(double size)
{
  double h = size / 2;
  int f, *fver;
  float vertex[8][3] = {
    {-h, -h, -h},    {-h,  h, -h},    { h,  h, -h},    { h, -h, -h},
    {-h, -h,  h},    {-h,  h,  h},    { h,  h,  h},    { h, -h,  h} };
  unsigned int face[6][4] = {
    { 0, 1, 2, 3 },    { 3, 2, 6, 7 },    { 2, 1, 5, 6 },
    { 7, 6, 5, 4 },    { 4, 5, 1, 0 },    { 3, 7, 4, 0 }  };
  float normal[6][3] = {
    {  0.0,  0.0, -1.0 },    {  1.0,  0.0,  0.0 },    {  0.0,  1.0,  0.0 },
    {  0.0,  0.0,  1.0 },    { -1.0,  0.0,  0.0 },    {  0.0, -1.0,  0.0 }  };

  glBegin(GL_QUADS);

  for (f=0; f<6; f++) {
    fver = face[f];
    glNormal3fv(normal[f]);
    glVertex3fv( vertex[fver[0]] );    glVertex3fv( vertex[fver[1]] );
    glVertex3fv( vertex[fver[2]] );    glVertex3fv( vertex[fver[3]] );
  }

  glEnd();
}


/// Environment drawing
///////////////////////

void draw_wall(float width, float height, int hdivs, int vdivs)
{
  float x, y;
  int i, j;
  const float hdiv = width / hdivs;
  const float vdiv = height / vdivs;

  glBegin(GL_LINES);

  glNormal3f(0.0, 0.0, -1.0);

  // draw vertical lines
  for (i=0; i<=hdivs; i++) {
    x = -width/2 + i*hdiv;

    for (j=0; j<vdivs; j++) {
      y = -height/2 + j*vdiv;
      glVertex2f(x, y);
      glVertex2f(x, y+vdiv);
    }
  }

  // draw horizontal lines
  for (j=0; j<=vdivs; j++) {
    y = -height/2 + j*vdiv;

    for (i=0; i<hdivs; i++) {
      x = -width/2 + i*hdiv;
      glVertex2f(x, y);
      glVertex2f(x+hdiv, y);
    }
  }

  glEnd();
}

void draw_side_wall(float tx, float ty, float tz, float rx, float ry, float rz,
		    float w, float h, int hdivs, int vdivs)
{
    glPushMatrix();
    glTranslatef(tx, ty, tz);
    glRotatef(90.0, rx, ry, rz);
    draw_wall(w, h, hdivs, vdivs);
    glPopMatrix();
}

void drawFloor(void)
{
  glLineWidth(1);
  glColor3f(0.7,0.7,0.7);
  draw_wall(5000, 5000, 20, 20);
}

void drawWalls(void)
{
  glLineWidth(1);
  draw_side_wall(0.0, 2500.0, 1250.0, 1.0, 0.0, 0.0, 5000.0, 2500.0, 20, 10);
  draw_side_wall(0.0, -2500.0, 1250.0, -1.0, 0.0, 0.0, 5000.0, 2500.0, 20, 10);
  draw_side_wall(2500.0, 0.0, 1250.0, 0.0, -1.0, 0.0, 2500.0, 5000.0, 10, 20);
  draw_side_wall(-2500.0,0.0, 1250.0, 0.0, 1.0, 0.0, 2500.0, 5000.0, 10, 20);
}

void drawChairs(void)
{
  glPushMatrix();
  glColor4f(0.1, 0.1, 0.1, 1.0);
  glTranslatef(-700, 0, 225);
  drawSolidCube(450);
  glTranslatef(1400, 0, 0);
  drawSolidCube(450);
  glPopMatrix();
}


/// Body parts drawing
//////////////////////

void cross_prod(float *x, float *y, float *z,
		float a1, float a2, float a3,
		float b1, float b2, float b3)
{
  *x = a2*b3-a3*b2;  *y = a3*b1-a1*b3;  *z = a1*b2-a2*b1;
}

void draw_single_head(float x1, float y1, float z1,
		      float x2, float y2, float z2,
		      float x3, float y3, float z3)
{
  float x,y,z,norm, xm,ym,zm, xp,yp,zp;

  cross_prod(&x, &y, &z, x3-x1,y3-y1,z3-z1, x2-x1, y2-y1, z2-z1);
  norm = sqrt(x*x + y*y + z*z);
  x /= norm;   y /= norm;   z /= norm;

  if ((x1*x) > 0.0)
    { x = -x;  y = -y;  z = -z; }

  xm = (x1+x2+x3) / 3.;
  ym = (y1+y2+y3) / 3.;
  zm = (z1+z2+z3) / 3.;

  xp = xm + 80.*x;
  yp = ym + 80.*y;
  zp = zm + 80.*z;

  glPushMatrix();
  glTranslatef(xp, yp, zp);
  drawSolidSphere(100.0F, 20, 20);
  glPopMatrix();
}


inline void torsoVertex(float x, float y, float z, float mx, float my, float mz)
{
  float nx = x-mx, ny = y-my, nz = z-mz;
//  glNormal3f(nx, ny, nz);
  glVertex3f(x, y, z);
}

void draw_torso(float xa, float ya, float za,
		float xb, float yb, float zb,
		float xc, float yc, float zc,
		float xd, float yd, float zd)
{
#define top_thick 50
#define bottom_thick 40

  glBegin(GL_QUADS);

  za += 20;
  zb += 20;

  // torso mean
  float mx = (xa + xb + xc + xd) / 4;
  float my = (ya + yb + yc + yd) / 4;
  float mz = (za + zb + zc + zd) / 4;

//  glEnable(GL_NORMALIZE);

#define TORSO_VERTEX(x,y,z) torsoVertex(x,y,z,mx,my,mz)
  
  TORSO_VERTEX(xa+top_thick,ya,za);
  TORSO_VERTEX(xb+top_thick,yb,zb);
  TORSO_VERTEX(xc+bottom_thick,yc,zc);
  TORSO_VERTEX(xd+bottom_thick,yd,zd);

  TORSO_VERTEX(xa-top_thick,ya,za);
  TORSO_VERTEX(xb-top_thick,yb,zb);
  TORSO_VERTEX(xc-bottom_thick,yc,zc);
  TORSO_VERTEX(xd-bottom_thick,yd,zd);

  TORSO_VERTEX(xc-bottom_thick,yc,zc);
  TORSO_VERTEX(xd-bottom_thick,yd,zd);
  TORSO_VERTEX(xd+bottom_thick,yd,zd);
  TORSO_VERTEX(xc+bottom_thick,yc,zc);

  TORSO_VERTEX(xa-top_thick,ya,za);
  TORSO_VERTEX(xb-top_thick,yb,zb);
  TORSO_VERTEX(xb+top_thick,yb,zb);
  TORSO_VERTEX(xa+top_thick,ya,za);
  
  TORSO_VERTEX(xa-top_thick,ya,za);
  TORSO_VERTEX(xd-bottom_thick,yd,zd);
  TORSO_VERTEX(xd+bottom_thick,yd,zd);
  TORSO_VERTEX(xa+top_thick,ya,za);

  TORSO_VERTEX(xb-top_thick,yb,zb);
  TORSO_VERTEX(xc-bottom_thick,yc,zc);
  TORSO_VERTEX(xc+bottom_thick,yc,zc);
  TORSO_VERTEX(xb+top_thick,yb,zb);

#undef TORSO_VERTEX

  glDisable(GL_NORMALIZE);
  glEnd();
}
