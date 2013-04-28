#!/usr/bin/python
"""
Just fetch an APOD picture and print the url
This can be combined with wget/curl to download
Example:
% f=$(python get_apod_data.py) && wget $f
NOTE: The caption for the picture is also saved in a .txt file
"""
import sys
import os
import re
import urllib2
from BeautifulSoup import BeautifulSoup

APOD_BASE_URL = 'http://apod.nasa.gov/apod'
IMAGE_DIR = 'image/'
APOD_HTML = '/astropix.html'
BLANK_SPACES = re.compile('\s+')
STRIP_TAGS = re.compile(r'</?\S([^=>]*=(\s*"[^"]*"|\s*\'[^\']*\'|\S*)|[^>])*?>', re.IGNORECASE)

def split_lines(text):
    """ Split lines longer than 80 characters """
    lines = text.split(os.linesep)
    regex = re.compile(r'.{1,80}(?:\s+|$)')
    ret = []
    for line in lines:
        for s in regex.findall(line):
            sentence = re.sub(BLANK_SPACES, ' ', s)
            ret.append(sentence)
    return '\n'.join(ret)

def main(args):
    """ The main function """
    if len(args) >= 2:
        url = args[1]
    else:    
        url = APOD_BASE_URL + APOD_HTML

    page = urllib2.urlopen(url)
    page_as_ls = page.readlines()
    doc = ''.join(page_as_ls)
    soup = BeautifulSoup(doc)
    res = [x['href'] for x in soup.findAll('a', href=True) if image_root in x['href']]
    if not res:
        sys.exit("Could not find %s at %s" % (image_root, url))
    img_file_url = url_root + '/' + res[0]
    print img_file_url

    explanation = []
    found = False
    for i in page_as_ls:
        if 'Explanation:' in i:
            found = True
            continue
        if found and 'Videos & Discussion' in i:
            break
        if found and "Tomorrow's picture:" in i:
            break
        if found:
            sentence = re.sub(BLANK_SPACES, ' ', i.replace(os.linesep,' '))
            explanation.append(sentence)

    # Trick to also detect jpg and JPG case insensitive
    case_insensitive_re = re.compile(re.escape('jpg'), re.IGNORECASE)
    explanation_fn = case_insensitive_re.sub('txt', os.path.basename(img_file_url))
    html = ''.join(explanation)    
    text = STRIP_TAGS.sub('', html).lstrip()
    f = open(explanation_fn, 'w')
    f.write(split_lines(text))
    f.close()

if __name__ == "__main__":
    main(sys.argv[1:])


