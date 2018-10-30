import sys
import numpy as np
from mvnc import mvncapi as mvnc
import threading
import queue
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import cv2

# for movidius
labels = ('background',
          'aeroplane', 'bicycle', 'bird', 'boat',
          'bottle', 'bus', 'car', 'cat', 'chair',
          'cow', 'diningtable', 'dog', 'horse',
          'motorbike', 'person', 'pottedplant',
          'sheep', 'sofa', 'train', 'tvmonitor')
min_score_percent = 60
# the resize_window arg will modify these if its specified on the commandline
resize_output = False
resize_output_width = 0
resize_output_height = 0

# create a preprocessed image from the source image that complies to the
# network expectations and return it
def preprocess_image(source_image):
    resized_image = source_image
    #resized_image = cv2.resize(source_image, (NETWORK_IMAGE_WIDTH, NETWORK_IMAGE_HEIGHT))
    
    # trasnform values from range 0-255 to range -1.0 - 1.0
    resized_image = resized_image - 127.5
    resized_image = resized_image * 0.007843
    return resized_image

def run_inference(image_source, ssd_mobilenet_graph, result_queue):
    # preprocess the image to meet nework expectations
    prepared_image = preprocess_image(image_source)
    # Send the image to the NCS as 16 bit floats
    ssd_mobilenet_graph.LoadTensor(prepared_image.astype(numpy.float16), None)
    # Get the result from the NCS
    output, _ = ssd_mobilenet_graph.GetResult()

    # Queuing for OpenGL
    result_queue.put(output)
    return output

def init_movidius():
    mvnc.SetGlobalOption(mvnc.GlobalOption.LOG_LEVEL, 2)
    devices = mvnc.EnumerateDevices()
    if len(devices) == 0:
        print('No devices found')
        quit()
    device = mvnc.Device(devices[0])
    device.OpenDevice()
    graph_filename = 'graph'
    with open(graph_filename, mode='rb') as f:
        graph_data = f.read()
    return device.AllocateGraph(graph_data)

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

class maxstack:
    def __init__(self, max_stack=10):
        self._max_stack = max_stack
        self._stack = []
        self.condition = threading.Condition()
    def push(self,obj):
        with self.condition:
            if self._max_stack <= len(self._stack):
                self._stack.pop(0)
            self._stack.append(obj)
    def pop(self):
        if len(self._stack)>0:
            with self.condition:
                return self._stack[-1]

class safequeue:
    def __init__(self, max_queue=128):
        self._safequeue = queue.Queue(max_queue)
    def put(self, obj):
        if not self._safequeue.full():
            self._safequeue.put(obj)
    def get(self):
        if not self._safequeue.empty():
            return self._safequeue.get()
        return None

def draw_image():
    ret, img = cap.read()

    # for Movidius
    global imgstack, mostrcnt, resqueue
    imgstack.push(cv2.resize(img,(300,300)))

    result = resqueue.get()
    if result is not None:
        mostrcnt = result

    if mostrcnt is None:
        # show with no prediction
        pass
    else:
        # show overlayed image with current or most recent prediction
        pass

    # for PyOpenGL
    img = cv2.flip(img, 0)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

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
    key = key.decode('utf-8')
    if key == 'q':
        print('exit')
        sys.exit()

if __name__ == "__main__":

    # For OpenGL
    glutInitWindowPosition(0, 0);
    glutInitWindowSize(widowWidth, windowHeight);
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE )
    glutCreateWindow("Display")
    glutDisplayFunc(draw_image)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    init()
    glutIdleFunc(idle)

    # I/F OpenGL and Movidius
    imgstack = maxstack()
    resqueue = safequeue()
    mostrcnt = None

    # For Movidius
    ssd_mobilenet_graph = init_movidius()

    glutMainLoop()
