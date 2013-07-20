#!/usr/bin/env python
from optparse import OptionParser
import glob
import os
import pyexiv2
import shutil
import hashlib

EXIF_DATE_KEY = 'Exif.Photo.DateTimeOriginal'
EXTENSIONS = ['.jpeg', '.JPEG', '.jpg', '.JPG']

def md5_incomplete_ck(file_path):
    m = hashlib.md5()
    with open(file_path, 'rb') as fh:
        data = fh.read(8192)
        if not data:
            return None
        m.update(data)
    return m.hexdigest()

def find_case_insensitve(dirname, extensions):
    files = []
    for filename in glob.glob(dirname):
        base, ext = os.path.splitext(filename)
        if ext.lower() in extensions:
            files.append(filename)
    return files

def main():
    parser = OptionParser(usage='Usage: %prog [OPTIONS] PATH')
    parser.add_option('--dry-run', action='store_true', default=False, dest='dry_run', help='display the actions that will be undertaken without actually executing them')
    parser.add_option('--recursive', action='store_true', default=False, dest='recursive', help='traverse subdirectories recursively')
    parser.add_option('--move', action='store_true', default=False, dest='move', help='move the files instead of doing a copy')
    (options, args) = parser.parse_args()
    # Use the current directory if none has been specified
    if len(args) != 1:
        directory = os.getcwdu()
    else:
        directory = args[0]
    if not os.path.isdir(directory):
        parser.error("the files' directory specified is invalid.")
    # Get the absolute path and normalize its case
    directory = os.path.realpath(os.path.normcase(directory))
    # Get the current working dir
    cwdir = os.getcwdu()
    run(cwdir, directory, options.dry_run, options.recursive, options.move)

def do_copy(src, dest, dry_run=False, domove=False):
    # Move the photo into the directory
    do_copy = True
    source_ck = md5_incomplete_ck(src)
    moving_msg = '%s -> %s ...' % (src, dest)
    if os.path.exists(dest):
        target_ck = md5_incomplete_ck(dest)
        if source_ck == target_ck:
            moving_msg = "SKIP - destination file already exists: %s, md5:%s..." % (dest, target_ck[:6])
            do_copy = False
    if do_copy and not dry_run:
        print moving_msg,
        if not domove:
            shutil.copy(src, dest)
        else:
            shutil.move(src,dest)
    elif not do_copy and not dry_run:
        print moving_msg,
    elif dry_run:
        print "[dry-run]", moving_msg,
    print "Done."

def run(cwdir, directory, dry_run, recursive, domove):
    files = []
    if not recursive:
        files = find_case_insensitve(os.path.join(directory, '*'), EXTENSIONS)
    else:
        import fnmatch
        files = [os.path.join(dirpath, f)
                 for dirpath, dirnames, files in os.walk(directory)
                 for ext in EXTENSIONS
                 for f in fnmatch.filter(files, '*' + ext)]
    files.sort()

    for f in files:
        # Read EXIF metadata and extract the date the photo was taken
        metadata = pyexiv2.ImageMetadata(f)
        metadata.read()

        if not metadata:
            print "No EXIF metadata found in %s" % f
            continue

        for i in metadata.exif_keys:
            if EXIF_DATE_KEY in i:
                break
        else:
            print EXIF_DATE_KEY, "not found in %s" % f
            continue

        file_name = os.path.basename(f)
        date = metadata[EXIF_DATE_KEY].value
        date_directory_name = os.path.join(str(date.year), "%02d" % (date.month))
        # Create the directory
        date_directory_path = os.path.join(cwdir, date_directory_name)
        if not os.path.exists(date_directory_path):
            directory_msg = "Creating directory '%s'..." % date_directory_path
            if not dry_run:
                print directory_msg,
                os.makedirs(date_directory_path)
            else:
                print '[dry-run]', directory_msg,
            print 'Done.'
        moved_file_path = os.path.join(date_directory_path, file_name)
        do_copy(f, moved_file_path, dry_run, domove)

if __name__ == "__main__":
    main()
