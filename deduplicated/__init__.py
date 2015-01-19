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
        if not self._meta.has_section('options'):
            self._meta.add_section('options')
            self._meta.set('options', 'follow_link', 'False')
            self.save_meta()

        if os.path.exists(self.get_excludefilename()):
            with open(self.get_excludefilename()) as fp:
                self.exclude = fp.read().splitlines()
        else:
            self.exclude = []

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

    def get_excludefilename(self):
        return self._hashfile + '.exclude'

    def get_metafilename(self):
        return self._hashfile + '.meta'

    # Database
    def save_database(self):
        self._conn.commit()

    # Exclude
    def save_exclude(self):
        with open(self.get_excludefilename(), 'w') as fp:
            fp.write('\n'.join(self.exclude))

    # Meta
    def set_option_follow_link(self, value):
        self._meta.set('options', 'follow_link', str(value))

    def is_option_follow_link(self):
        return self._meta.getboolean('options', 'follow_link')

    def save_meta(self):
        with open(self.get_metafilename(), 'w') as fp:
            self._meta.write(fp)

    # Utils
    def list_files(self, dirname=''):
        path = os.path.join(self._path, dirname)
        for filename in sorted(os.listdir(path)):
            partial_filename = os.path.join(dirname, filename)
            abs_filename = os.path.join(self._path, partial_filename)

            if partial_filename in self.exclude:
                continue

            if os.path.isdir(abs_filename):
                for f in self.list_files(partial_filename):
                    yield f
                continue

            file_stat = os.stat(abs_filename)
            yield partial_filename, file_stat.st_mtime, file_stat.st_size

    # Steps
    def update_tree(self):
        insert = 0
        update = 0
        self._db.execute('UPDATE files SET exist = 0')
        for partial_filename, mtime, size in self.list_files():
            self._db.execute('SELECT mtime, size FROM files '
                             'WHERE filename = ?', (partial_filename,))
            row = self._db.fetchone()

            # New file
            if row is None:
                self._db.execute('INSERT INTO files (filename, mtime, size, '
                                 'hash, exist) VALUES (?, NULL, ?, NULL, 1)',
                                 (partial_filename, size))
                insert += 1
                continue

            # Update file
            if mtime != row[0] or size != row[1]:
                self._db.execute('UPDATE files SET mtime = NULL, size = ?, '
                                 'hash = NULL, exist = 1 WHERE filename = ?',
                                 (size, partial_filename))
                update += 1
                continue

            # Unmodified file
            self._db.execute('UPDATE files SET exist = 2 WHERE filename = ?',
                             (partial_filename,))

        self._db.execute('DELETE FROM files WHERE exist = 0')
        delete = self._db.rowcount
        self.save_database()
        return insert, update, delete

    def hash_for_update(self):
        self._db.execute('SELECT filename FROM files WHERE exist = 1')
        for filename in self._db.fetchall():
            yield filename[0]

    def update_hash(self, filename):
        abs_filename = os.path.join(str(self), filename)
        stat = os.stat(abs_filename)
        self._db.execute('UPDATE files SET mtime = ?, size = ?, '
                         'hash = ?, exist = 2 WHERE filename = ?',
                         (stat.st_mtime, stat.st_size,
                          sha1_file(abs_filename), filename))
        self.save_database()

    def get_duplicated(self):
        self._db.execute('SELECT hash, COUNT(hash) FROM files GROUP BY hash '
                         'ORDER BY size ASC')
        for row in self._db.fetchall():
            if row[1] > 1:
                self._db.execute('SELECT filename, size FROM files '
                                 'WHERE hash = ?', (row[0],))
                files = self._db.fetchall()
                yield row[0], files[0][1], [f[0] for f in files]


# Create user directory if not exists

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
