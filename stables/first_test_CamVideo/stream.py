import numpy
import cv2
from   threading import Thread
import sys
import time

if sys.version_info >= (3, 0):
    from queue import Queue
else:
    from Queue import Queue

class FStream:
    def __init__(self, path):
        self.stream = cv2.VideoCapture(path)
        self.stopped= False
        self.Q      = Queue(128)
    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self
    def update(self):
        while True:
            if self.stopped:
                return
            if not self.Q.full():
                (ret,frame) = self.stream.read()
                if not ret:
                    self.stop()
                    return
                self.Q.put(frame)
    def read(self):
        return self.Q.get()
    def more(self):
        return self.Q.qsize() > 0
    def stop(self):
        self.stopped=True


#fsv = FStream("LA_VGA.mp4").start()
fsv = FStream("1mb2.mp4").start()
time.sleep(1.0)

while fsv.more():
        frame = fsv.read()
#        frame = cv2.resize(frame,(640,480))
        cv2.imshow("Frame",frame)
        cv2.waitKey(10)

