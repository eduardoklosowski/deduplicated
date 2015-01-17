# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from __future__ import unicode_literals

from hashlib import sha1
import os


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


# Create user directory if not exists

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
