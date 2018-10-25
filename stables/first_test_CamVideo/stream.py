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
        self.Q      = Queue(256)
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


class DStream:
    def __init__(self, win):
        self.win=win
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
            if self.more():
                frame = self.read()
                cv2.imshow(self.win, frame)
                if cv2.waitKey(1)==27:
                    sys.exit(1)
    def put(self,frame):
        if not self.Q.full():
            self.Q.put(frame)
    def read(self):
        return self.Q.get()
    def more(self):
        return self.Q.qsize() > 0
    def stop(self):
        self.stopped=True


fsv = FStream("1mb2.mp4").start()
dsv = DStream("video").start()
time.sleep(1.0)

while True:
    frame = fsv.read()
    start = time.time()
    for i in range(0,100000):pass   # instead of Main Process
    print("%.5f"%(time.time()-start))
    dsv.put(frame)
    if not fsv.more() and fsv.stopped:
        break
