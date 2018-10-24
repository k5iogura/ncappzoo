import cv2
import numpy as np
import time

cam=cv2.VideoCapture("LA.mp4")
fourcc = cv2.VideoWriter_fourcc(*'XVID')
vwt = cv2.VideoWriter('LA_VGA.avi',fourcc,20.0,(640,480))

cv2.namedWindow("video")

fno=0
while(1):
    start = time.time()
    (ret, img) = cam.read()
    vwt.write(img)
    if ret==False:
        break
    cv2.imshow("video",img)
    cv2.waitKey(10)
    end   = time.time()
    print('%d %5.3f\b\b\b\b\b'%(fno,1./(end-start)))
