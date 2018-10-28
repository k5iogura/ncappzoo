import numpy as np

import video_processor
import queue
import cv2
import time

Q = queue.Queue(10)

file_name = "../video_objects/police_car_6095_shortened_960x540.mp4"
vp = video_processor.video_processor(Q,file_name)
vp.start_processing()

while True:
    if Q.qsize()>0:
        cv2.imshow("video", Q.get())
    else:
        if vp.finished():break
        time.sleep(0.1)
    cv2.waitKey(20)

