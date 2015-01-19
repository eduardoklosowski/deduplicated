# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from __future__ import unicode_literals

from glob import glob
from hashlib import sha1
import os
import sqlite3

# workaround for Python 2
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


# Global Vars

CACHE_DIR = os.path.join(os.path.expanduser('~'), '.deduplicated')


# Utils

def sha1_file(filename):
    with open(filename, 'rb') as fp:
        s = sha1()
        block = True
        while block:
            block = fp.read(2 ** 10)
            s.update(block)
        return s.hexdigest()


def str_size(size):
    if size < 2 ** 10:
        return '%d B' % size
    if size < 2 ** 20:
        return '%.2f KB' % (size / (2 ** 10))
    if size < 2 ** 30:
        return '%.2f MB' % (size / (2 ** 20))
    if size < 2 ** 40:
        return '%.2f GB' % (size / (2 ** 30))
    return '%.2f TB' % (size / (2 ** 40))


# Directory

def directory_delete(hashcache):
    for filename in glob(os.path.join(CACHE_DIR, hashcache + '.*')):
        os.remove(filename)


def directory_get(hashcache):
    config = ConfigParser()
    if not config.read([os.path.join(CACHE_DIR, hashcache + '.meta')]):
        raise IOError('hash directory not found')
    return Directory(config.get('META', 'path'))


def directory_list():
    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith('.meta'):
            continue
        meta = ConfigParser()
        meta.read([os.path.join(CACHE_DIR, filename)])
        yield filename[:-5], meta.get('META', 'path')


class Directory(object):
    def __init__(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise IOError('%s is not valid directory' % path)

        self._path = path
        self._hashfile = os.path.join(
            CACHE_DIR,
            self.get_hash(),
        )

        self._meta = ConfigParser()
        if os.path.exists(self.get_metafilename()):
            self._meta.read([self.get_metafilename()])
        if not self._meta.has_section('META'):
            self._meta.add_section('META')
            self._meta.set('META', 'path', path)
            self.save_meta()

        self._conn = sqlite3.connect(self.get_dbfilename())
        self._db = self._conn.cursor()
        self._db.execute('CREATE TABLE IF NOT EXISTS files '
                         '(filename TEXT PRIMARY KEY, mtime FLOAT, size INT, '
                         'hash TEXT, exist INT)')

    def __str__(self):
        return self._path

    def get_hash(self):
        return sha1(self._path.encode('utf-8')).hexdigest()

    # Path for files
    def get_dbfilename(self):
        return self._hashfile + '.db'

    def get_metafilename(self):
        return self._hashfile + '.meta'

    # Database
    def save_database(self):
        self._conn.commit()

    # Meta
    def save_meta(self):
        with open(self.get_metafilename(), 'w') as fp:
            self._meta.write(fp)

    # Utils
    def list_files(self, dirname=''):
        path = os.path.join(self._path, dirname)
        for filename in sorted(os.listdir(path)):
            partial_filename = os.path.join(dirname, filename)
            abs_filename = os.path.join(self._path, partial_filename)

            if os.path.isdir(abs_filename):
                for f in self.list_files(partial_filename):
                    yield f
                continue

            file_stat = os.stat(abs_filename)
            yield partial_filename, file_stat.st_mtime, file_stat.st_size


# Create user directory if not exists

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
