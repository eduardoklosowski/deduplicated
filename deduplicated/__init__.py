# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from __future__ import unicode_literals

import os


# Global Vars

CACHE_DIR = os.path.join(os.path.expanduser('~'), '.deduplicated')


# Create user directory if not exists

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
