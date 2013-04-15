#!/usr/bin/python
import os
import re
import sys
from PIL import Image

def resize(img, box, fit):
    '''Downsample the image.
    @param img: Image -  an Image-object
    @param box: tuple(x, y) - the bounding box of the result image
    @param fix: boolean - crop the image to fill the box
    '''
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *=2
    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)
    #calculate the cropping box and get the cropped part
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = 1.0 * x2/box[0]
        hRatio = 1.0 * y2/box[1]
        if hRatio > wRatio:
            y1 = y2/2-box[1]*wRatio/2
            y2 = y2/2+box[1]*wRatio/2
        else:
            x1 = x2/2-box[0]*hRatio/2
            x2 = x2/2+box[0]*hRatio/2
        img = img.crop((int(x1),int(y1),int(x2),int(y2)))
    #Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Image.ANTIALIAS)
    return img


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

def main(args=None):
    

src = sys.argv[1]
im = Image.open(src)
#print "source:%s (jpg %s)" % (src, im.size)

dimensions = find_desktop_dimensions()

base = os.path.basename(src)

# Trick to also detect jpg and JPG case insensitive
case_insensitive_re = re.compile(re.escape('jpg'), re.IGNORECASE)
#dest = base.rstrip('jpg') + 'png'
dest = case_insensitive_re.sub('png', base)
#print "dest  :%s (png, %s)" % (dest, dimensions)

resized_im = resize(im, dimensions, True)
resized_im.save(dest)
print dest

if __name__ == "__main__":
    sys.exit(main())
