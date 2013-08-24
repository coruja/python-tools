#!/usr/bin/python
import os
import re
import sys
from PIL import Image, ImageOps
from optparse import OptionParser


def find_desktop_dimensions():
    with os.popen('xdpyinfo') as f:
        output = f.readlines()
    dim_ls = [x for x in output if 'dimensions' in x]
    # ['  dimensions:    1280x800 pixels (338x211 millimeters)\n']
    dimensions_re = re.compile('^\s*dimensions:\s+(\d+x\d+)\s+pixels.*$')
    matched = dimensions_re.match(dim_ls[0])
    if matched:
        dims = matched.group(1).split('x')
        return int(dims[0]), int(dims[1])
    return

def only_crop(img, size, crop_type='top', at=None, verb=False):
    # If height is higher we resize vertically, if not we resize horizontally
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    #The image is scaled/cropped vertically or horizontally depending on the ratio
    box = None
    org_img = img
    if ratio > img_ratio:
        if verb: print "ratio (%s) > img_ratio (%s)" % (ratio, img_ratio)
        # (**) Resize the picture
        box1 = (0, 0, img.size[0], size[1])
        box2 = (0, (img.size[1] - size[1]) / 2, img.size[0], (img.size[1] + size[1]) / 2)
        box3 = (0, img.size[1] - size[1], img.size[0], img.size[1])
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = box1
        elif crop_type == 'middle':
            box = box2
        elif crop_type == 'bottom':
            box = box3
        elif crop_type == 'at' and at is not None:
            # I think the at coordinates must be transformed to match the coordinates
            # after the picture img was resized at **
            y1 = at[1] - size[1] / 2
            if y1 < 0: 
                y1 = 0
            if y1 == 0:
                y2 = size[1]
            else:
                y2 = at[1] + size[1] / 2
            if y2 > img.size[1]:
                y2 = img.size[1]
            box = (0, int(y1), img.size[0], int(y2))
            if verb: print box
        elif crop_type == 'all':
            return img.crop(box1), img.crop(box2), img.crop(box3)
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        return img.crop(box)
    elif ratio < img_ratio:
        if verb: print "ratio (%s) < img_ratio (%s)" % (ratio, img_ratio)
        box1 = (0, 0, size[0], img.size[1])
        box2 = ((img.size[0] - size[0]) / 2, 0, (img.size[0] + size[0]) / 2, img.size[1])
        box3 = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = box1
        elif crop_type == 'middle':
            box = box2
        elif crop_type == 'bottom':
            box = box3
        elif crop_type == 'at' and at is not None:
            x1 = at[0] - size[0] / 2
            if x1 < 0:
                x1 = 0
            if x1 == 0:
                x2 = size[0]
            else:
                x2 = at[0] + size[0] / 2
            if x2 > img.size[0]:
                x2 = img.size[0]
            box = (int(x1), 0, int(x2), img.size[1])
            if verb: print box
        elif crop_type == 'all':
            return img.crop(box1), img.crop(box2), img.crop(box3)
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        return img.crop(box)

def only_resize(img, size, verb=False):
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    if ratio > img_ratio:
        if verb: print "ratio (%s) > img_ratio (%s)" % (ratio, img_ratio)
        # (**) Resize the picture
        img = img.resize((size[0], size[0] * img.size[1] / img.size[0]),
                Image.ANTIALIAS)
    elif ratio < img_ratio:
        if verb: print "ratio (%s) < img_ratio (%s)" % (ratio, img_ratio)
        img = img.resize((size[1] * img.size[0] / img.size[1], size[1]),
                Image.ANTIALIAS)
    else:
        if verb: print "ratio (%s) = img_ratio (%s)" % (ratio, img_ratio)
        # If the scale is the same, we do not need to crop
        img = img.resize((size[0], size[1]), Image.ANTIALIAS)
    return img

def get_face_coordinates(img_name, verb=False):
    import cv
    DEF_CASCADE = "./haarcascade_frontalface_alt.xml"
    SCALE = 2

    def detectObjects(grayscale, scale_factor, cascade_file=None):
        """Prints the locations of any faces found in given greyscale image"""
        storage = cv.CreateMemStorage(0)
        cv.EqualizeHist(grayscale, grayscale)
        cascade = cv.Load(cascade_file)
        faces = cv.HaarDetectObjects(grayscale, cascade, storage, 1.2, 2,
                                     cv.CV_HAAR_DO_CANNY_PRUNING, (50,50))
        # The function returns a list of tuples, (rect, neighbors),
        # where rect is a CvRect specifying the object's extents and neighbors
        # is a number of neighbors.
        s = scale_factor
        centers = []
        faces_coords = []
        if faces:
            for (x,y,w,h), n in faces:
                faces_coords.append(((x*s,y*s,w*s,h*s), n))
                c = int(x*s + w*s/2), int(y*s + h*s/2)
                centers.append(c)
        return faces_coords, centers

    # Load the image and convert to grayscale
    grayscale = cv.LoadImageM(img_name, cv.CV_LOAD_IMAGE_GRAYSCALE)
    # Create a thumbnail version of the original image to speed up detection
    thumbnail = cv.CreateMat( int(grayscale.rows/SCALE), int(grayscale.cols/SCALE), grayscale.type)
    cv.Resize(grayscale, thumbnail)
    # Detect objects on the thumbnail version
    faces, centers = detectObjects(thumbnail, SCALE, DEF_CASCADE)
    if faces and centers:
        ccx, ccy = 0, 0
        if verb: print "Found %d face(s) in %s" % (len(faces), os.path.basename(img_name))
        for i, ((x,y,w,h), n) in enumerate(faces):
            if verb: print("%d: w:%d, h:%d coord:[(%d,%d) -> (%d,%d)], "
                            "center: %s, neighbors:%d" %
                                (i, w, h, x, y, x+w, y+h, centers[i], n))
            cv.Rectangle(grayscale, (x,y), (x+w,y+h), 255, 2)
            cx, cy = centers[i]
            ccx += cx
            ccy += cy
        ccx, ccy = ccx/len(faces), ccy/len(faces)
        cv.Rectangle(grayscale, (ccx-5,ccy-5), (ccx+5,ccy+5), 255, 5)
        cv.SaveImage(img_name, grayscale)
        if verb: print "Average center coordinates: %s, %s" % (ccx, ccy)
        return (ccx, ccy)
    return None

def main():
    usage = "usage: %prog [options] <jpg file to resize>"
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--size", type="string", dest="size",
                      action="store", help="Dimensions (w x h)")
    parser.add_option("-v", "--verb", dest="verb", default=False,
                      action="store_true", help="Verbosity")
    parser.add_option("-f", "--with-face-detect", dest="face", default=False,
                      action="store_true", help="Use face detection")
    (options, args) = parser.parse_args()
    if len(args) != 1:  # The number of remaining of arguments
        parser.error("incorrect number of arguments")
        return 1
    src = args[0]
    verb = options.verb
    if not options.size:
        dimensions = find_desktop_dimensions()
    else:
        dims = options.size.split('x')
        dimensions = int(dims[0]), int(dims[1])
    base = os.path.basename(src)
    im = Image.open(src)
    if verb: print "source:%s (jpg %s)" % (src, im.size)
    # Trick to also detect jpg and JPG case insensitive
    case_insensitive_re = re.compile(re.escape('.jpg'), re.IGNORECASE)
    dest = case_insensitive_re.sub('.png', base)
    basenm, ext = os.path.splitext(dest)

    crop_type='all'
    at=None

    im = only_resize(im, dimensions, verb=verb)
    if options.face:
        im.save("tmp.jpg")
        crop_type = 'at'
        at = get_face_coordinates("tmp.jpg", verb)
        if at is None:
            raise ValueError('ERROR: could not find face coordinate(s)')
    ims = only_crop(im, dimensions, crop_type=crop_type, at=at, verb=verb)

    if isinstance(ims, tuple):
        for i, im in enumerate(ims):
            dest_ = basenm + '_%d' % i + ext
            if verb: print "dest  :%s (png, %s)" % (dest_, im.size)
            if not os.path.exists(dest_):
                im.save(dest_)
                print dest_
            else:
                raise Exception("Destination %s already exists, please rename it!"
                                 % dest_)
    else:
        if not os.path.exists(dest):
            if verb: print "dest  :%s (png, %s)" % (dest, ims.size)
            ims.save(dest)
            print dest
        else:
            dest_ = basenm + '_0' + ext
            if verb: print "dest  :%s (png, %s)" % (dest_, ims.size)
            ims.save(dest_)
            print dest_

    return 0

if __name__ == "__main__":
    sys.exit(main())
