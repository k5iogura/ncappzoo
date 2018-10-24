import cv2
import numpy as np
import time

cam=cv2.VideoCapture("1mb.mp4")

cv2.namedWindow("video")

while(1):
    start = time.time()
    (ret, img) = cam.read()
    if ret==False:
        break
    cv2.imshow("video",img)
    cv2.waitKey(5)
    end   = time.time()
    print('%5.3f\b\b\b\b\b'%(1./(end-start)))
