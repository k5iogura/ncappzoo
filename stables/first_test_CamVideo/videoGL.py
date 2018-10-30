import sys
import cv2
import numpy as np
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

imgsrc_file = "police_car_6095_shortened_960x540.mp4" 
imgsrc = cv2.VideoCapture(imgsrc_file)
def imaging():
    ret, img = imgsrc.read()
    if ret:
        img  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        img  = cv2.flip(img,0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1.0, 1.0, 1.0)

        glDrawPixels(w, h, GL_RGB, GL_UNSIGNED_BYTE, img)

        glFlush();
        glutSwapBuffers()
    else:
        sys.exit(1)

def reshape(w,h):
    pass

def idle():
    pass
    glutPostRedisplay()

glutInit(sys.argv)
glutInitDisplayMode( GLUT_RGBA | GLUT_DOUBLE )
glutInitWindowSize(640,480)
glutInitWindowPosition(0,0)
glutCreateWindow("DEMO")
#glutFullScreen()
#init()
glClearColor(0.7, 0.7, 0.7, 0.7)
glutDisplayFunc(imaging)
glutReshapeFunc(reshape)
glutIdleFunc(idle)

glutMainLoop()
