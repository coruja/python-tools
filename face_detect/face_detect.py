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

DEF_CASCADE = "./haarcascade_frontalface_alt.xml"

def detectObjects(grayscale, cascade_file=None):
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
    centers = []
    if faces:
        for (x,y,w,h), _ in faces:
            c = int(x + w/2), int(y + h/2)
            centers.append(c)
    return faces, centers

def main():
    usage = "usage: %prog [options] <file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--cascade", type="string", dest="cascade_file",
                      action="store", default=None,
                      help="The location of the XML cascade classifier file,"
                      "for example: haarcascade_frontalface_alt.xml"
                     )
    parser.add_option("-w", "--write-detected", type="string", dest="dest_file",
                        action="store", default=None,
                        help="The destination file to write detected faces")
    (options, args) = parser.parse_args()
    if len(args) != 1:  # The number of remaining of arguments
        parser.error("incorrect number of arguments")
        return 1
    img_name = args[0]
    img_name_base = os.path.splitext(img_name)[0]

    # Basic input validation
    if not options.cascade_file and not os.path.isfile(DEF_CASCADE):
        print "ERROR: Could not find default file %s" % DEF_CASCADE
        return 1
    elif options.cascade_file and not os.path.isfile(options.cascade_file):
        print "ERROR: Could not find file %s" % options.cascade_file
        return 1

    dest_file = options.dest_file or (img_name_base + "_detected_faces.jpg")

    grayscale = cv.LoadImageM(img_name, cv.CV_LOAD_IMAGE_GRAYSCALE)
    faces, centers = detectObjects(grayscale, options.cascade_file or DEF_CASCADE)
    # To write a rectangle around the objects found:
    if faces and centers:
        ccx, ccy = 0, 0
        print "Found %d face(s) in %s" % (len(faces), os.path.basename(img_name))
        org_img = cv.LoadImage(img_name)
        for i, ((x,y,w,h), n) in enumerate(faces):
            print("%d: w:%d, h:%d coord:[(%d,%d) -> (%d,%d)], "
            "center: %s, neighbors:%d" % (i, w, h, x, y, x+w, y+h, centers[i], n))
            cv.Rectangle(org_img, (x,y), (x+w,y+h), 255, 2)
            cx, cy = centers[i]
            ccx += cx
            ccy += cy
            cv.Rectangle(org_img, (cx-1,cy-1), (cx+1,cy+1), 255, 2)
        ccx, ccy = ccx/len(faces), ccy/len(faces)
        print "Average center coordinates: %s, %s" % (ccx, ccy)
        cv.Rectangle(org_img, (ccx-5,ccy-5), (ccx+5,ccy+5), 255, 5)
        cv.SaveImage(dest_file, org_img)

if __name__ == "__main__":
    main()
