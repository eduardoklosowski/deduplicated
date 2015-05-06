# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from __future__ import unicode_literals

from datetime import datetime
from hashlib import sha1
import os
import sqlite3
import sys

# workaround for Python 2
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

if sys.version_info[0] == 2:
    reload(sys)  # NOQA
    sys.setdefaultencoding('utf-8')


# Global Vars

__version__ = '1.0b1'
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
    size = float(size)
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

def directory_by_hash(hashid, checkvalid=True):
    config = ConfigParser()
    if not config.read([os.path.join(CACHE_DIR, hashid + '.meta')]):
        raise IOError('hash directory not found')
    return Directory(config.get('META', 'path'), checkvalid=checkvalid)


def directory_delete(hashid):
    for filename in [filename for filename in os.listdir(CACHE_DIR) if filename.startswith(hashid)]:
        os.remove(os.path.join(CACHE_DIR, filename))


def directory_list(hashid=False):
    dirlist = []
    for filename in [filename for filename in os.listdir(CACHE_DIR) if filename.endswith('.meta')]:
        meta = ConfigParser()
        meta.read([os.path.join(CACHE_DIR, filename)])
        path = meta.get('META', 'path')
        if hashid:
            dirlist.append((filename[:-5], path))
        else:
            dirlist.append(path)
    if hashid:
        return sorted(dirlist, key=lambda x: x[1].lower())
    return sorted(dirlist, key=lambda x: x.lower())


class Directory(object):
    def __init__(self, path, checkvalid=True):
        path = os.path.abspath(path)
        self._path = path
        if checkvalid and not self.is_valid():
            raise IOError('%s is not valid directory' % path)

        self._hashfile_prefix = os.path.join(CACHE_DIR, self.get_hash())

        self._meta = ConfigParser()
        if os.path.exists(self.get_metafilename()):
            self._meta.read([self.get_metafilename()])
        if not self._meta.has_section('META'):
            self._meta.add_section('META')
            self._meta.set('META', 'path', path)
            self._meta.set('META', 'lastupdate', '')
            self.save_meta()
        if not self._meta.has_section('options'):
            self._meta.add_section('options')
            self._meta.set('options', 'follow_link', 'False')
            self.save_meta()
        if not self._meta.has_section('duplicated'):
            self._meta.add_section('duplicated')
            self._meta.set('duplicated', 'hash', '0')
            self._meta.set('duplicated', 'files', '0')
            self._meta.set('duplicated', 'size', '0')
            self.save_meta()

        if os.path.exists(self.get_excludefilename()):
            with open(self.get_excludefilename()) as fp:
                self.exclude = fp.read().splitlines()
        else:
            self.exclude = []

        self._conn = sqlite3.connect(self.get_dbfilename())
        self._db = self._conn.cursor()
        self._db.execute('CREATE TABLE IF NOT EXISTS files '
                         '(filename TEXT PRIMARY KEY, mtime FLOAT, size INT, hash TEXT, exist INT)')

    def __str__(self):
        return self._path

    def get_hash(self):
        return sha1(self._path.encode('utf-8')).hexdigest()

    def is_valid(self):
        return os.path.isdir(self._path)

    # Path for files
    def get_dbfilename(self):
        return self._hashfile_prefix + '.db'

    def get_excludefilename(self):
        return self._hashfile_prefix + '.exclude'

    def get_metafilename(self):
        return self._hashfile_prefix + '.meta'

    # Database
    def save_database(self):
        self._conn.commit()

    # Exclude
    def save_exclude(self):
        with open(self.get_excludefilename(), 'w') as fp:
            fp.write('\n'.join(self.exclude))

    # Meta
    def get_duplicated_hash(self):
        return self._meta.getint('duplicated', 'hash')

    def get_duplicated_files(self):
        return self._meta.getint('duplicated', 'files')

    def get_duplicated_size(self):
        return self._meta.getint('duplicated', 'size')

    def get_lastupdate(self):
        lastupdate = self._meta.get('META', 'lastupdate')
        if lastupdate:
            return datetime.strptime(lastupdate, '%Y-%m-%d %H:%M:%S')
        return None

    def now_lastupdate(self):
        return self._meta.set('META', 'lastupdate', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def set_option_follow_link(self, value):
        self._meta.set('options', 'follow_link', 'yes' if value else 'no')

    def is_option_follow_link(self):
        return self._meta.getboolean('options', 'follow_link')

    def save_meta(self):
        with open(self.get_metafilename(), 'w') as fp:
            self._meta.write(fp)

    # Utils
    def is_completed(self):
        self._db.execute('SELECT count(*) FROM files WHERE exist != 2')
        return not self._db.fetchone()[0]

    def is_file_in(self, filename):
        hashfile = sha1_file(filename)
        self._db.execute('SELECT filename FROM files WHERE hash = ?', (hashfile,))
        return [os.path.join(self._path, row[0]) for row in self._db.fetchall()]

    def delete_file(self, filename):
        self._db.execute('DELETE FROM files WHERE filename = ?', (filename,))
        if self._db.rowcount:
            os.remove(os.path.join(self._path, filename))
            self.save_database()

    def delete_duplicated_indir(self, dirname):
        for _, _, files in self.get_duplicated():
            for filename in [filename for filename in files if filename.startswith(dirname)]:
                self.delete_file(filename)

    def list_files(self, dirname=''):
        path = os.path.join(self._path, dirname)
        follow_link = self.is_option_follow_link()
        try:
            filenames = sorted(os.listdir(path))
        except OSError:
            filenames = []
        for filename in filenames:
            partial_filename = os.path.join(dirname, filename)
            abs_filename = os.path.join(self._path, partial_filename)

            if partial_filename in self.exclude:
                continue

            if not follow_link and os.path.islink(abs_filename):
                continue

            if os.path.isdir(abs_filename):
                for f in self.list_files(partial_filename):
                    yield f
                continue

            file_stat = os.stat(abs_filename)
            yield partial_filename, file_stat.st_mtime, file_stat.st_size

    def update_duplicated(self):
        d_hash = 0
        d_files = 0
        d_size = 0

        for hashfile, size, files in self.get_duplicated():
            d_hash += 1
            files_len = len(files)
            d_files += files_len
            d_size += (files_len - 1) * size

        self._meta.set('duplicated', 'hash', str(d_hash))
        self._meta.set('duplicated', 'files', str(d_files))
        self._meta.set('duplicated', 'size', str(d_size))
        self.save_meta()

    # Steps
    def update_tree(self):
        insert = 0
        update = 0
        self._db.execute('UPDATE files SET exist = 0')
        for partial_filename, mtime, size in self.list_files():
            self._db.execute('SELECT mtime, size FROM files WHERE filename = ?', (partial_filename,))
            row = self._db.fetchone()

            # New file
            if row is None:
                self._db.execute('INSERT INTO files (filename, mtime, size, hash, exist) VALUES (?, NULL, ?, NULL, 1)',
                                 (partial_filename, size))
                insert += 1
                continue

            # Update file
            if mtime != row[0] or size != row[1]:
                self._db.execute('UPDATE files SET mtime = NULL, size = ?, hash = NULL, exist = 1 WHERE filename = ?',
                                 (size, partial_filename))
                update += 1
                continue

            # Unmodified file
            self._db.execute('UPDATE files SET exist = 2 WHERE filename = ?', (partial_filename,))

        self._db.execute('DELETE FROM files WHERE exist = 0')
        delete = self._db.rowcount
        self.save_database()
        return insert, update, delete

    def hash_for_update(self):
        self._db.execute('SELECT filename FROM files WHERE exist = 1')
        for filename in self._db.fetchall():
            yield filename[0]
        self.now_lastupdate()
        self.update_duplicated()
        self.save_meta()

    def update_hash(self, filename):
        abs_filename = os.path.join(str(self), filename)
        stat = os.stat(abs_filename)
        self._db.execute('UPDATE files SET mtime = ?, size = ?, hash = ?, exist = 2 WHERE filename = ?',
                         (stat.st_mtime, stat.st_size, sha1_file(abs_filename), filename))
        self.save_database()

    def get_duplicated(self):
        self._db.execute('SELECT hash, COUNT(hash) FROM files GROUP BY hash ORDER BY size ASC')
        for row in self._db.fetchall():
            if row[1] > 1:
                self._db.execute('SELECT filename, size FROM files WHERE hash = ?', (row[0],))
                files = self._db.fetchall()
                yield row[0], files[0][1], [f[0] for f in files]


# Create user directory if not exists

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
