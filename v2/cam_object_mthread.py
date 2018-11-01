#! /usr/bin/env python3

# Copyright(c) 2017 Intel Corporation. 
# License: MIT See LICENSE file in root directory.


from mvnc import mvncapi as mvnc
import sys
import numpy
import cv2
import time
import csv
import os
import argparse
import sys
from sys import argv
#import video_processor
import queue

# name of the opencv window
cv_window_name = "SSD Mobilenet"

# labels AKA classes.  The class IDs returned
# are the indices into this list
labels = ('background',
          'aeroplane', 'bicycle', 'bird', 'boat',
          'bottle', 'bus', 'car', 'cat', 'chair',
          'cow', 'diningtable', 'dog', 'horse',
          'motorbike', 'person', 'pottedplant',
          'sheep', 'sofa', 'train', 'tvmonitor')

# the ssd mobilenet image width and height
NETWORK_IMAGE_WIDTH = 300
NETWORK_IMAGE_HEIGHT = 300

# the minimal score for a box to be shown
min_score_percent = 60

# the resize_window arg will modify these if its specified on the commandline
resize_output = False
resize_output_width = 0
resize_output_height = 0

# read video files from this directory
input_video_path = '.'

# create a preprocessed image from the source image that complies to the
# network expectations and return it
def preprocess_image(source_image):
    resized_image = cv2.resize(source_image, (NETWORK_IMAGE_WIDTH, NETWORK_IMAGE_HEIGHT))
    
    # trasnform values from range 0-255 to range -1.0 - 1.0
    resized_image = resized_image - 127.5
    resized_image = resized_image * 0.007843
    return resized_image

# handles key presses by adjusting global thresholds etc.
# raw_key is the return value from cv2.waitkey
# returns False if program should end, or True if should continue
def handle_keys(raw_key):
    global min_score_percent
    ascii_code = raw_key & 0xFF
    if ((ascii_code == ord('q')) or (ascii_code == ord('Q'))):
        return False
    elif (ascii_code == ord('B')):
        min_score_percent += 5
        print('New minimum box percentage: ' + str(min_score_percent) + '%')
    elif (ascii_code == ord('b')):
        min_score_percent -= 5
        print('New minimum box percentage: ' + str(min_score_percent) + '%')

    return True


# overlays the boxes and labels onto the display image.
# display_image is the image on which to overlay the boxes/labels
# object_info is a list of 7 values as returned from the network
#     These 7 values describe the object found and they are:
#         0: image_id (always 0 for myriad)
#         1: class_id (this is an index into labels)
#         2: score (this is the probability for the class)
#         3: box left location within image as number between 0.0 and 1.0
#         4: box top location within image as number between 0.0 and 1.0
#         5: box right location within image as number between 0.0 and 1.0
#         6: box bottom location within image as number between 0.0 and 1.0
# returns None
def overlay_on_image(display_image, object_info):
    source_image_width = display_image.shape[1]
    source_image_height = display_image.shape[0]

    base_index = 0
    class_id = object_info[base_index + 1]
    percentage = int(object_info[base_index + 2] * 100)
    if (percentage <= min_score_percent):
        return

    label_text = labels[int(class_id)] + " (" + str(percentage) + "%)"
    box_left = int(object_info[base_index + 3] * source_image_width)
    box_top = int(object_info[base_index + 4] * source_image_height)
    box_right = int(object_info[base_index + 5] * source_image_width)
    box_bottom = int(object_info[base_index + 6] * source_image_height)

    box_color = (255, 128, 0)  # box color
    box_thickness = 2
    cv2.rectangle(display_image, (box_left, box_top), (box_right, box_bottom), box_color, box_thickness)

    scale_max = (100.0 - min_score_percent)
    scaled_prob = (percentage - min_score_percent)
    scale = scaled_prob / scale_max

    # draw the classification label string just above and to the left of the rectangle
    #label_background_color = (70, 120, 70)  # greyish green background for text
    label_background_color = (0, int(scale * 175), 75)
    label_text_color = (255, 255, 255)  # white text

    label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
    label_left = box_left
    label_top = box_top - label_size[1]
    if (label_top < 1):
        label_top = 1
    label_right = label_left + label_size[0]
    label_bottom = label_top + label_size[1]
    cv2.rectangle(display_image, (label_left - 1, label_top - 1), (label_right + 1, label_bottom + 1),
                  label_background_color, -1)

    # label text above the box
    cv2.putText(display_image, label_text, (label_left, label_bottom), cv2.FONT_HERSHEY_SIMPLEX, 0.5, label_text_color, 1)

    # display text to let user know how to quit
    cv2.rectangle(display_image,(0, 0),(100, 15), (128, 128, 128), -1)
    cv2.putText(display_image, "Q to Quit", (10, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)


#return False if found invalid args or True if processed ok
def handle_args():
    global resize_output, resize_output_width, resize_output_height
    for an_arg in argv:
        if (an_arg == argv[0]):
            continue

        elif (str(an_arg).lower() == 'help'):
            return False

        elif (str(an_arg).startswith('resize_window=')):
            try:
                arg, val = str(an_arg).split('=', 1)
                width_height = str(val).split('x', 1)
                resize_output_width = int(width_height[0])
                resize_output_height = int(width_height[1])
                resize_output = True
                print ('GUI window resize now on: \n  width = ' +
                       str(resize_output_width) +
                       '\n  height = ' + str(resize_output_height))
            except:
                print('Error with resize_window argument: "' + an_arg + '"')
                return False
        else:
            return False

    return True


class detector:
    def __init__(self):
        self.initiated = False
        self.output    = None

        # configure the NCS
        mvnc.global_set_option(mvnc.GlobalOption.RW_LOG_LEVEL, mvnc.LogLevel.DEBUG)

        # Get a list of ALL the sticks that are plugged in
        self.devices = mvnc.enumerate_devices()
        if len(self.devices) == 0:
            print('No devices found')
            quit()

        # Pick the first stick to run the network
        self.device = mvnc.Device(self.devices[0])

        # Open the NCS
        self.device.open()

        graph_filename = 'graph'

        # Load graph file to memory buffer
        self.graph_data = None
        with open(graph_filename, mode='rb') as f:
            self.graph_data = f.read()

        self.ssd_mobilenet_graph = mvnc.Graph('graph1')

        self.input_fifo, self.output_fifo = self.ssd_mobilenet_graph.allocate_with_fifos(
            self.device,
            self.graph_data
        )

        # Run an inference on the passed image
        # image_to_classify is the image on which an inference will be performed
        #    upon successful return this image will be overlayed with boxes
        #    and labels identifying the found objects within the image.
        # ssd_mobilenet_graph is the Graph object from the NCAPI which will
        #    be used to peform the inference.

    def run_inference(self,image_to_classify):

        start = time.time()
        self.loadTensor(image_to_classify)
        t1 = time.time() - start

        cv2.waitKey(150)
        start = time.time()
        output = self.getResult()
        t2 = time.time() - start

        start = time.time()
        self.overlay(image_to_classify, output)
        t3 = time.time() - start

        print("load/getResult/overlay= %f\t%f\t%f"%(t1,t2,t3))

    def initiate(self, image_to_classify):
        self.initiated = True
        # preprocess the image to meet nework expectations
        resized_image = preprocess_image(image_to_classify)

        # Send the image to the NCS as 16 bit floats
        self.ssd_mobilenet_graph.queue_inference_with_fifo_elem(
            self.input_fifo,
            self.output_fifo,
            resized_image.astype(numpy.float32),
            resized_image
        )

    def finish(self, image_source=None):
        copy_image = None
        if self.initiated:
            output, _ = self.output_fifo.read_elem()
            if image_source is not None:
                copy_image = image_source.copy()
                self.overlay(copy_image, output)
            self.output = output
            self.initiated = False
        elif image_source is not None:
            copy_image = image_source.copy()
            self.overlay(copy_image, self.output)

        return copy_image

    def getResult(self):
        # Get the result from the NCS
        output, _ = self.output_fifo.read_elem()
        #  output
        #   a.	First fp16 value holds the number of valid detections = num_valid.
        #   b.	The next 6 values are unused.
        #   c.	The next (7 * num_valid) values contain the valid detections data
        #       Each group of 7 values will describe an object/box These 7 values in order.
        #       The values are:
        #         0: image_id (always 0)
        #         1: class_id (this is an index into labels)
        #         2: score (this is the probability for the class)
        #         3: box left location within image as number between 0.0 and 1.0
        #         4: box top location within image as number between 0.0 and 1.0
        #         5: box right location within image as number between 0.0 and 1.0
        #         6: box bottom location within image as number between 0.0 and 1.0
        return output

    def overlay(self, image_to_classify, output):
        # number of boxes returned
        num_valid_boxes = int(output[0])

        for box_index in range(num_valid_boxes):
                base_index = 7+ box_index * 7
                if (not numpy.isfinite(output[base_index]) or
                        not numpy.isfinite(output[base_index + 1]) or
                        not numpy.isfinite(output[base_index + 2]) or
                        not numpy.isfinite(output[base_index + 3]) or
                        not numpy.isfinite(output[base_index + 4]) or
                        not numpy.isfinite(output[base_index + 5]) or
                        not numpy.isfinite(output[base_index + 6])):
                    # boxes with non finite (inf, nan, etc) numbers must be ignored
                    continue

                x1 = max(int(output[base_index + 3] * image_to_classify.shape[0]), 0)
                y1 = max(int(output[base_index + 4] * image_to_classify.shape[1]), 0)
                x2 = min(int(output[base_index + 5] * image_to_classify.shape[0]), image_to_classify.shape[0]-1)
                y2 = min((output[base_index + 6] * image_to_classify.shape[1]), image_to_classify.shape[1]-1)

                # overlay boxes and labels on to the image
                overlay_on_image(image_to_classify, output[base_index:base_index + 7])

    def close(self):
        # Clean up the graph and the device
        self.input_fifo.destroy()
        self.output_fifo.destroy()
        self.ssd_mobilenet_graph.destroy()
        self.device.close()
        self.device.destroy()

# prints usage information
def print_usage():
    print('\nusage: ')
    print('python3 run_video.py [help][resize_window=<width>x<height>]')
    print('')
    print('options:')
    print('  help - prints this message')
    print('  resize_window - resizes the GUI window to specified dimensions')
    print('                  must be formated similar to resize_window=1280x720')
    print('')
    print('Example: ')
    print('python3 run_video.py resize_window=1920x1080')


# This function is called from the entry point to do
# all the work.

def draw_img(display_image):
    global resize_output, resize_output_width, resize_output_height
    if (resize_output):
        display_image = cv2.resize(display_image,
                                   (resize_output_width, resize_output_height),
                                   cv2.INTER_LINEAR)
    cv2.imshow(cv_window_name, display_image)
    raw_key = cv2.waitKey(1)
    return raw_key

def main():
    global resize_output, resize_output_width, resize_output_height

#    if (not handle_args()):
#        print_usage()
#        return 1

    Detector = detector()

    # get list of all the .mp4 files in the image directory
#    input_video_filename_list = os.listdir(input_video_path)
#    input_video_filename_list = [i for i in input_video_filename_list if i.endswith('.mp4')]
#    input_video_filename_list = ["police_car_6095_shortened_960x540.mp4"]

#    if (len(input_video_filename_list) < 1):
#        # no images to show
#        print('No video (.mp4) files found')
#        return 1

    cv2.namedWindow(cv_window_name)
    cv2.moveWindow(cv_window_name, 10,  10)

    exit_app = False
    restart  = True
    buffsize = 3
    display_image=[None for i in range(0,buffsize)]
    for jj in range(0,2):
        cam = cv2.VideoCapture(0)
        frame_count = 0
        end_time = start_time = time.time()
        ret,img = cam.read()
        Detector.initiate(img)
        while(True):
            for i in range(0, buffsize):
                try:
                    ret,display_image[i] = cam.read()
                    if i >= 0: image_overlapped = Detector.finish(display_image[i])
                    if i == 0: Detector.initiate(display_image[i])
                    raw_key = draw_img(image_overlapped)
                    if (raw_key != -1):
                        print(raw_key)
                        if (handle_keys(raw_key) == False):
                            Detector.finish(None)
                            end_time = time.time()
                            exit_app = True
                            break
                    frame_count += 1
                except Exception as e:
                    print("Any Exception found:",e.args)
                    exit_app = True
                    break
            if exit_app:
                break
        if exit_app:
            break
        if restart:
            try:
                Detector.close()
                time.sleep(1.0)
                Detector = detector()
                Detector.initiate(display_image[0])
                cam.release()
            except Exception as e:
                print("NCS: Restart not work-01",e.args)
                restart = False
            if not restart:
                print("NCS: Restart not work-02")
                break
            else:
                print("NCS: Restarted OK")
        frames_per_second = frame_count / (end_time - start_time)
        print('Frames per Second: ' + str(frames_per_second))

    # Clean up the graph and the device
    try:
        Detector.close()
        cv2.destroyAllWindows()
    except Exception as e:
        print("all finalizeing faild",e.args)
        sys.exit(1)
    print("finalizing OK")

# main entry point for program. we'll call main() to do what needs to be done.
if __name__ == "__main__":

    args = argparse.ArgumentParser()
    args.add_argument("--resize",       action="store_true",     help="resize video window")
    args.add_argument("-w", "--width" , type=int, default=640,   help="video width")
    args.add_argument("-t", "--height", type=int, default=480,   help="video height")
    args.add_argument("-c", "--cam",    type=int, default=0,     help="camera index")
    args = args.parse_args()
    if args.resize: resize_output=True
    resize_output_width = args.width
    resize_output_height= args.height

    sys.exit(main())

