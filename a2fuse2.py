
#!/usr/bin/env python

from __future__ import print_function, absolute_import, division

import logging
from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time
import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from passthrough import Passthrough
from memory import Memory

if not hasattr(__builtins__, 'bytes'):
    bytes = str
#Fuse calls A2Fuse1 function
class A2Fuse2(LoggingMixIn, Passthrough): 
    def __init__(self, root1, root2):
        self.root1 = root1
        self.root2 = root2
        self.files = {}
        self.data = defaultdict(bytes)
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)
        self.fd = 0
        self.boolean = True
        

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        if(self.boolean):
            path = os.path.join(self.root1, partial)
            if(os.path.exists(path)):
                pass
            else:
                path = os.path.join(self.root2, partial)
            return path
        elif(self.boolean != True):
            path2 = os.path.join(self.root2, partial)
            if(os.path.exists(path2)):
                pass
            else:
                path2 = os.path.join(self.root1, partial)
            return path2



    def readdir(self, path, fh):
        if path in self.files and (len(self.files) >= 2):
            dirents = ['.', '..'] + [x[1:] for x in self.files if x != '/']
        else:
            dirents = ['.', '..']   
        for x in range(2):
            full_path = self._full_path(path) #passes "/" returned source1/
            self.boolean = False
            if os.path.isdir(full_path):
                dirents.extend(os.listdir(full_path))
        self.boolean = True
        return dirents
      
        
    def open(self, path, flags):
        if path in self.files:
            self.fd += 1
            return self.fd
        else:
            return super(A2Fuse2,self).open(path,flags)

    def read(self, path, size, offset, fh):
        if path in self.files:
            return self.data[path][offset:offset + size]
        else:
            return super(A2Fuse2,self).read(path,size,offset,fh)

        
    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                                st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time())
        self.fd += 1
        return self.fd
    
    def getattr(self, path, fh=None):
        if path in self.files:
            return self.files[path]
        else:
            return super(A2Fuse2,self).getattr(path,fh)

    def access(self, path, mode):
        if path in self.files:
            #print("path in file")
            return None
        
        else:
            return super(A2Fuse2,self).access(path,mode)

    def flush(self, path, fh):
        if path in self.files:
            return None
        else:
            return super(A2Fuse2,self).flush(path,fh)

    def release(self,path, fh):
        if path in self.files:
            return None
        else:
            return super(A2Fuse2,self).release(path,fh)
        
    def write(self, path, data, offset, fh):
        if path in self.files:
            self.data[path] = self.data[path][:offset] + data
            self.files[path]['st_size'] = len(self.data[path])
            return len(data)
        else:
            return super(A2Fuse2,self).write(path,data,offset,fh)


    def unlink(self, path):
        self.files.pop(path)

        
def main(mountpoint, root1, root2):
    FUSE(A2Fuse2(root1,root2), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    mountpoint = sys.argv[3]
    root1 = sys.argv[1]
    root2 = sys.argv[2]
    main(mountpoint, root1, root2)
