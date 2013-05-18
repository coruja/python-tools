#!/usr/bin/python

# face_detect.py

# Face Detection using OpenCV. Based on sample code from:
# http://opencv.willowgarage.com/documentation/python/cascade_classification.html?highlight=haar

# Usage: python face_detect.py <image_file>

import sys, os
# Ubuntu 12.04: apt-get install python-opencv python-numpy
#from opencv.cv import *
import cv
#from opencv.highgui import *
from optparse import OptionParser

def detectObjects(grayscale, cascade_file):
    """Prints the locations of any faces found in given greyscale image"""
    storage = cv.CreateMemStorage(0)
    cv.EqualizeHist(grayscale, grayscale)
    cascade = cv.Load(cascade_file)
    faces = cv.HaarDetectObjects(grayscale, cascade, storage, 1.2, 2,
                                 cv.CV_HAAR_DO_CANNY_PRUNING, (50,50))
    #faces = cv.HaarDetectObjects(grayscale, cascade, storage, 1.2, 10)
    # The function returns a list of tuples, (rect, neighbors),
    # where rect is a CvRect specifying the object's extents and neighbors 
    # is a number of neighbors.
    if faces:
        print "Found %d face(s)" % len(faces)
        for i, ((x,y,w,h), n) in enumerate(faces):
            print("%d: w:%d, h:%d coord:[(%d,%d) -> (%d,%d)], neighbors:%d" % (i, w, h, x, y, x+w, y+h, n))
    return faces

def main():
    usage = "usage: %prog [options] <file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--cascade", type="string", dest="cascade_file",
                      action="store",
                      help="The location of the XML cascade classifier file,"
                      "for example: haarcascade_frontalface_alt.xml"
                     )
    (options, args) = parser.parse_args()
    if len(args) != 1:  # The number of remaining of arguments
        parser.error("incorrect number of arguments")
        return 1
    img_name = args[0]
    img_name_base = os.path.splitext(img_name)[0]
    grayscale = cv.LoadImageM(img_name, cv.CV_LOAD_IMAGE_GRAYSCALE);
    faces = detectObjects(grayscale, options.cascade_file)
    # To write a rectangle around the objects found:
    if faces:
        org_img = cv.LoadImage(img_name, 0)
        for (x,y,w,h), _ in faces:
            cv.Rectangle(org_img, (x,y), (x+w,y+h), 255)
        cv.SaveImage("detected.jpg", org_img)

if __name__ == "__main__":
    main()
