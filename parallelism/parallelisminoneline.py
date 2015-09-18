#!/usr/bin/python3
"""
From: http://chriskiehl.com/article/parallelism-in-one-line/

(I just changed the code to make it work in Python3)

Never heard of the threading clone of multiprocessing library called dummy? 
It has all of ONE sentence devoted to it in the multiprocessing documentation page.
And that sentence pretty much boils down to BTW this thing exists...

multiprocessing.dummy is an exact clone of the multiprocessing module.
The only difference is that, whereas multiprocessing works with processes,
the dummy module uses threads (which come with all the usual Python limitations).
"""
import urllib.request, urllib.error, urllib.parse
from multiprocessing.dummy import Pool as ThreadPool 

urls = [
  'http://www.python.org', 
  'http://www.python.org/about/',
  'http://www.onlamp.com/pub/a/python/2003/04/17/metaclasses.html',
  'http://www.python.org/doc/',
  'http://www.python.org/download/',
  'http://www.python.org/getit/',
  'http://www.python.org/community/',
  'https://wiki.python.org/moin/',
  'http://planet.python.org/',
  'https://wiki.python.org/moin/LocalUserGroups',
  'http://www.python.org/psf/',
  'http://docs.python.org/devguide/',
  'http://www.python.org/community/awards/'
  # etc.. 
  ]

# Make the Pool of workers
pool = ThreadPool(4) 
# Open the urls in their own threads
# and return the results
requests = map(urllib.request.Request, urls)
results = pool.map(urllib.request.urlopen, requests)
#close the pool and wait for the work to finish 
pool.close() 
pool.join() 
