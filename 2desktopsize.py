#!/usr/bin/python
import os
import re
import sys
from PIL import Image, ImageOps
from optparse import OptionParser

DEBUG = False

def resize(img, box):
    '''Downsample the image.
    @param img: Image -  an Image-object
    @param box: tuple(x, y) - the bounding box of the result image
    @param fit: boolean - crop the image to fill the box
    '''
    fit = False
    xbox, ybox = box
    x1 = y1 = 0
    x2, y2 = img.size
    if DEBUG:
        print "bounding box (wxh): %d, %d" % (xbox, ybox)
        print "img.size[0] = %d , img.size[1] = %d" % (x2, y2)
    if x2 / y2 != xbox / ybox:
        # The aspect ratio do not match, do fit
        fit = True
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while (x2 / factor) > (2 * xbox) and (y2 * 2) / factor > (2 * ybox):
        factor *=2
    if DEBUG:
        print "do fit ? %s" % ('y' if fit else 'n')
        print "resize factor: %d" % factor
    if factor > 1:
        img.thumbnail((x2 / factor, y2 / factor), Image.NEAREST)
    #calculate the cropping box and get the cropped part
    if fit:
        wRatio = 1.0 * x2/xbox # x=width
        hRatio = 1.0 * y2/ybox # y=height
        if DEBUG:
            print "hRatio: %f, wRatio: %f" % (hRatio, wRatio)
        if hRatio > wRatio:
            y1 = y2/2-ybox*wRatio/2
            y2 = y2/2+ybox*wRatio/2
        else:
            x1 = x2/2-xbox*hRatio/2
            x2 = x2/2+xbox*hRatio/2
        img = img.crop((int(x1),int(y1),int(x2),int(y2)))
        if DEBUG:
            print "crop coordinates: %d,%d,%d,%d" % (int(x1),int(y1),int(x2),int(y2))
    #Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Image.ANTIALIAS)
    img2 = Image.new("RGB", box, "black")
    img2.paste(img, (0,0))
    return img2

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

def main():
    usage = "usage: %prog [options] <jpg file to resize>"
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--size", type="string", dest="size",
                      action="store", help="Dimensions (w x h)")
    parser.add_option("-v", "--verb", dest="verb", default=False,
                      action="store_false", help="Verbosity")
    parser.add_option("-f", "--with-face-detect", dest="face", default=False,
                      action="store_false", help="Use face detection")
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
    case_insensitive_re = re.compile(re.escape('jpg'), re.IGNORECASE)
    dest = case_insensitive_re.sub('png', base)
    if verb: print "dest  :%s (png, %s)" % (dest, dimensions)
    resized_im = resize(im, dimensions)
    resized_im.save(dest)
    print dest
    return 0

if __name__ == "__main__":
    sys.exit(main())
