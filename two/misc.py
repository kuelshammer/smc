"""
Miscellaneous functions.
"""

import os, tempfile, socket
from StringIO import StringIO
import urllib, urllib2

import gc, requests

from urllib2 import URLError

# this exception is used by client code
ConnectionError = requests.ConnectionError
Timeout = requests.Timeout

def get_using_requests(url, data=None, timeout=10):
    """
    GET the url with optional parameters as specified by the data
    variable.

    INPUT:
    
    - ``url`` -- string
    - ``data`` -- dict or None (defaults to empty dict); GET vars
    - ``timeout`` -- (default: 1) time in seconds to attempt to
      complete the GET before raising the ConnectionError exception.

    OUTPUT:

    - string

    EXAMPLES::

    We test the timeout option::
    
        >>> get('http://cnn.com',timeout=1e-3)
        Traceback (most recent call last):
        ...
        Timeout: Request timed out.

    We pass data to a server, which happens to respond with some text
    in JSON format::
    
        >>> import subprocess_server; r = subprocess_server.Daemon(5000)
        >>> s = get('http://localhost:5000/popen', data={'command':'python'})
        >>> print s
        {
          "status": "ok", 
          "pid": ..., 
          "execpath": "...tmp..."
        }
    """
    if data is None: data = {}
    t = requests.get(url, params=data, timeout=timeout).text
    # This "gc.collect()" is absolutely required, or requests
    # leaves open connection. See https://github.com/kennethreitz/requests/issues/239
    gc.collect()
    return t

def get(url, data=None, timeout=10):
    # todo: rewrite using with
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        if data is not None:
            url = url + '?' + urllib.urlencode(data)
        return urllib2.urlopen(url).read()
    finally:
        socket.setdefaulttimeout(old_timeout)

def post_using_requests(url, data=None, files=None, timeout=10):
    """
    POST the dictionary of data to the url, and return the response
    from the server.

    INPUT:

    - ``url`` -- string
    - ``data`` -- dict or None (defaults to empty dict); POST vars
    - ``files`` -- dict or None (defaults to empty dict); keys are
      file names and values are the contents
    - ``timeout`` -- (default: 10) time in seconds to attempt to
      complete the POST before raising the ConnectionError exception.

    OUTPUT:

    - string

    EXAMPLES::

        >>> from client import TestClient; c = TestClient(5000)
        >>> a = get('http://localhost:5000/new_session'); c.wait(0)
        >>> print post('http://localhost:5000/execute/0', {'code':'print(2+3)'})
        {
          "status": "ok", 
          "cell_status": "running", 
          "cell_id": 0
        }
        >>> c.quit()
    """
    if files is None:
        files = {}
    else:
        files = dict([(k,StringIO(v)) if isinstance(v, basestring) else (k,v)
                      for k,v in files.iteritems()])
    if data is None: data = {}
    # This function with files!={} is easy because of "requests".
    t = requests.post(url, data=data, timeout=timeout, files=files).text
    gc.collect()
    return t

def post(url, data=None, files=None, timeout=10):
    if files is not None:
        return post_using_requests(url, data, files, timeout)
    # todo: rewrite using with
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        if data is None: data = {}
        data = urllib.urlencode(data)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)        
        return response.read()
    finally:
        socket.setdefaulttimeout(old_timeout)
    

def all_files(path):
    """
    Return a sorted list of the names of all files in the given path, and in
    all subdirectories.  Empty directories are ignored.

    INPUT:

    - ``path`` -- string

    EXAMPLES::

    We create 3 files: a, xyz.abc, and m/n/k/foo.  We also create a
    directory x/y/z, which is empty::

        >>> import tempfile
        >>> d = tempfile.mkdtemp()
        >>> o = open(os.path.join(d,'a'),'w')
        >>> o = open(os.path.join(d,'xyz.abc'),'w')
        >>> os.makedirs(os.path.join(d, 'x', 'y', 'z'))
        >>> os.makedirs(os.path.join(d, 'm', 'n', 'k'))
        >>> o = open(os.path.join(d,'m', 'n', 'k', 'foo'),'w')

    This all_files function returns a list of the 3 files, but
    completely ignores the empty directory::
    
        >>> all_files(d)       # ... = / on unix but \\ windows
        ['a', 'm...n...k...foo', 'xyz.abc']
    """
    all = []
    n = len(path)
    for root, dirs, files in os.walk(path):
        for fname in files:
            all.append(os.path.join(root[n+1:], fname))
    all.sort()
    return all


_temp_prefix = None
def is_temp_directory(path):
    """
    Return True if the given path is likely to have been
    generated by the tempfile.mktemp function.

    EXAMPLES::

        >>> import tempfile
        >>> is_temp_directory(tempfile.mktemp())
        True
        >>> is_temp_directory(tempfile.mktemp() + '../..')
        False
    """
    global _temp_prefix
    if _temp_prefix is None:
        _temp_prefix = os.path.split(tempfile.mktemp())[0]
    path = os.path.split(os.path.abspath(path))[0]
    return os.path.samefile(_temp_prefix, path)

def fake_get(*args, **kwds):
    """
    This is used internally only for testing.
    
    EXAMPLES::

        >>> fake_get('http://localhost:8000', data={'foo':5}, timeout=2)
        GET: ('http://localhost:8000',) [('data', {'foo': 5}), ('timeout', 2)]
    """
    print 'GET: %s %s'%(args, list(sorted(kwds.iteritems())))
    
def fake_post(*args, **kwds):
    """
    This is used internally only for testing.
    
    EXAMPLES::

        >>> fake_post('http://localhost:8000', data={'foo':5}, timeout=2)
        POST: ('http://localhost:8000',) [('data', {'foo': 5}), ('timeout', 2)]
    """
    print 'POST: %s %s'%(args, list(sorted(kwds.iteritems())))


######################################################################

def randint_set(i, j, n):
    """
    Return a set of n distinct randomly chosen integers in the closed
    interval [i,j].

    EXAMPLES::
    
        >>> sage: random.seed(0)
        >>> misc.randint_set(5, 10, 3)
        set([9, 10, 7])
        >>> misc.randint_set(5, 10, 6)
        [5, 6, 7, 8, 9, 10]
        >>> misc.randint_set(5, 10, 7)
        Traceback (most recent call last):
        ...
        ValueError: there is no such set    
    """
    import random
    if j-i+1 == n:
        return set(range(i,j+1))
    if j-i+1 < n:
        raise ValueError, "there is no such set"
    v = set([random.randint(i,j)])
    while len(v) < n:
        v.add(random.randint(i,j))
    return v
