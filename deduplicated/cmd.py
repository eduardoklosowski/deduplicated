# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys

from . import Directory, str_size


# Argument parser

parser = argparse.ArgumentParser(prog='deduplicated')
subparsers = parser.add_subparsers(help='actions')

# update command
parser_update = subparsers.add_parser('update',
                                      help='update directory information')
parser_update.add_argument('update', nargs='+')

# duplicated command
parser_duplicated = subparsers.add_parser('duplicated',
                                          help='list duplicated')
parser_duplicated.add_argument('duplicated', nargs='+')


# Utils

def print_update_tree(directory):
    print('==> Update tree (%s): ' % directory, end='')
    print('+%d  ~%d  -%d' % directory.update_tree())


def print_update_hash(directory):
    for filename in directory.hash_for_update():
        print('Updating %s' % filename)
        directory.update_hash(filename)


def print_duplicated(directory):
    print('==> Duplicated (%s):' % str(directory))
    for hashfile, size, files in directory.get_duplicated():
        print('%s [%s]' % (str_size(size), hashfile))
        print('    %s' % '\n    '.join(files))


def main():
    args = parser.parse_args()

    if hasattr(args, 'update'):
        for dirname in args.update:
            directory = Directory(dirname)
            print_update_tree(directory)
            print_update_hash(directory)
        sys.exit(0)

    if hasattr(args, 'duplicated'):
        for dirname in args.duplicated:
            directory = Directory(dirname)
            print_duplicated(directory)
        sys.exit(0)
