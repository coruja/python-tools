#!/usr/bin/python
import pyexiv2
import sys

if __name__ == "__main__":
    metadata = pyexiv2.ImageMetadata(sys.argv[1])
    metadata.read()
    for i in metadata.exif_keys:
        print i, metadata[i]
