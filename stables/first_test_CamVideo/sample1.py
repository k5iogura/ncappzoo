from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import cv2
import numpy as np

# USB camera setup
vfile = "police_car_6095_shortened_960x540.mp4"
cap = cv2.VideoCapture(vfile)
if cap.isOpened() is False:
    raise("IO Error")
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

widowWidth = 720
windowHeight = 480

def draw():
    ret, img = cap.read() #read camera image
    #img = cv2.imread('image.png') # if use the image file
    img = cv2.flip(img, 0)
    img= cv2.cvtColor(img,cv2.COLOR_BGR2RGB) #BGR-->RGB

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)

    glDrawPixels(img.shape[1], img.shape[0], GL_RGB,GL_UNSIGNED_BYTE, img)

    glFlush();
    glutSwapBuffers()

def init():
    glClearColor(0.7, 0.7, 0.7, 0.7)

def idle():
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glLoadIdentity()
    #Make the display area proportional to the size of the view
    glOrtho(-w / widowWidth, w / widowWidth, -h / windowHeight, h / windowHeight, -1.0, 1.0)

def keyboard(key, x, y):
    # convert byte to str
    key = key.decode('utf-8')
    # press q to exit
    if key == 'q':
        print('exit')
        sys.exit()

if __name__ == "__main__":

    glutInitWindowPosition(0, 0);
    glutInitWindowSize(widowWidth, windowHeight);
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE )
    glutCreateWindow("Display")
    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    init()
    glutIdleFunc(idle)
    glutMainLoop()
