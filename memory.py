#!/usr/bin/env python

import logging

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

import redis
import pprint
if not hasattr(__builtins__, 'bytes'):
    bytes = str

def log(cb):
    def func(self, *a, **b):
        print "\n\033[92m{}\033[0m {} {}".format(cb.__code__.co_name.upper(),a,b)
        try:
            ret = cb(self, *a, **b)
            pprint.pprint(ret)
            return ret
        except Exception as e:
            pprint.pprint(str(e))
            raise
    return func

def dataKey(path):
    return "data:" + path

def statKey(path):
    return "stat:" + path

class SnailFS(Operations):
    def __init__(self):
        print("INIT")
        self.client = redis.StrictRedis(host='localhost', port=6379, db=12)
        self.client.flushdb()
        self.mkdir("/", 0755)
        pass

    @log
    def readdir(self, path, fh):
        return []

    @log
    def getattr(self, path, fh=None):
        stat = statKey(path)

        if not self.client.exists(stat):
            raise FuseOSError(ENOENT)

        s = self.client.hgetall(stat)
        return {k:int(v) for k,v in s.items()}

    @log
    def mkdir(self, path, mode):
        stat = path + ":stat"

        t = int(time())
        self.client.hmset(stat, dict(
                    st_mode=(S_IFDIR | 0755),
                    st_nlink=2,
                    st_size=0,
                    st_ctime=t,
                    st_mtime=t,
                    st_atime=t))


class SnailFS(Operations):

    #@log
    #def listxattr(self, path):
    #    attrs = self.files[path].get('attrs', {})
    #    return attrs.keys()

    #@log
    #def chmod(self, path, mode):
    #    self.files[path]['st_mode'] &= 0770000
    #    self.files[path]['st_mode'] |= mode
    #    return 0

    #@log
    #def chown(self, path, uid, gid):
    #    self.files[path]['st_uid'] = uid
    #    self.files[path]['st_gid'] = gid

    #@log
    #def getxattr(self, path, name, position=0):
    #    attrs = self.files[path].get('attrs', {})
    #
    #    try:
    #        return attrs[name]
    #    except KeyError:
    #        return ''       # Should return ENOATTR

    def __init__(self):
        self.client = redis.StrictRedis(host='localhost', port=6379, db=12)
        self.client.flushdb()

        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        self.mkdir('/', 0755)

    @log
    def mkdir(self, path, mode):
        key = statKey(path)
        t = int(time())
        self.client.hmset(key, dict(
                st_mode=(S_IFDIR | mode),
                st_nlink=2,
                st_size=0,
                st_ctime=t,
                st_mtime=t,
                st_atime=t))
        self.client.sadd(dataKey(path), ".", "..")
        parent, name = path.rsplit("/",1)
        print((parent,name))
        if name:
            if not parent:
                parent = "/"

            self.client.sadd(dataKey(parent), name)
            print("Added {} to {}".format(name, dataKey(parent)))

    @log
    def getattr(self, path, fh=None):
        stat = statKey(path)

        if not self.client.exists(stat):
            raise FuseOSError(ENOENT)

        s = self.client.hgetall(stat)
        return {k:int(v) for k,v in s.items()}

    @log
    def create(self, path, mode):
        parent, name = path.rsplit("/",1)
        print("create: {} {}".format(parent, name))
        if not parent:
            parent = "/"
        self.client.sadd(dataKey(parent), name)

        #self.client.hincrby(
        t = int(time())
        self.client.hmset(statKey(path), dict(
                st_mode=(S_IFREG | mode),
                st_nlink=1,
                st_size=0,
                st_ctime=t,
                st_mtime=t,
                st_atime=t))

        self.fd += 1
        return self.fd

    @log
    def write(self, path, data, offset, fh):
        key = dataKey(path)
        l = self.client.setrange(key, offset, data)
        self.client.hset(statKey(path), 'st_size', l)
        return l-offset

    @log
    def open(self, path, flags):
        self.fd += 1
        return self.fd

    @log
    def read(self, path, size, offset, fh):
        return self.client.getrange(dataKey(path),
            offset, size)

    @log
    def readdir(self, path, fh):
        return self.client.smembers(dataKey(path))
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']

    @log
    def readlink(self, path):
        return self.data[path]

    @log
    def removexattr(self, path, name):
        attrs = self.files[path].get('attrs', {})

        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR

    @log
    def rename(self, old, new):
        self.files[new] = self.files.pop(old)

    @log
    def rmdir(self, path):
        self.files.pop(path)
        self.files['/']['st_nlink'] -= 1

    @log
    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value

    @log
    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    @log
    def symlink(self, target, source):
        self.files[target] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
                                  st_size=len(source))

        self.data[target] = source

    @log
    def truncate(self, path, length, fh=None):
        self.data[path] = self.data[path][:length]
        self.files[path]['st_size'] = length

    @log
    def unlink(self, path):
        self.files.pop(path)

    @log
    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)


    fuse = FUSE(SnailFS(), argv[1], foreground=True)
    #fuse = FUSE(Memory(), argv[1], foreground=True)
