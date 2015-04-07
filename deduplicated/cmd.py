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

# check command
parser_check = subparsers.add_parser('check',
                                     help='update and duplicated')
parser_check.add_argument('check', nargs='+')

# indir command
parser_indir = subparsers.add_parser('indir',
                                     help='check file in dir')
parser_indir.add_argument('indir', nargs=1)
parser_indir.add_argument('directory', nargs='+')

# delindir command
parse_delindir = subparsers.add_parser('delindir',
                                       help='delete duplicated files in directory')
parse_delindir.add_argument('directory', nargs=1)
parse_delindir.add_argument('delindir', nargs=1)


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
    print('%d hashs (%d files) %s' % (
        directory.get_duplicated_hash(),
        directory.get_duplicated_files(),
        str_size(directory.get_duplicated_size()),
    ))


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

    if hasattr(args, 'check'):
        for dirname in args.check:
            directory = Directory(dirname)
            print_update_tree(directory)
            print_update_hash(directory)
            print_duplicated(directory)

    if hasattr(args, 'indir'):
        has = False
        for dirname in args.directory:
            directory = Directory(dirname)
            files = directory.is_file_in(args.indir[0])
            if files:
                has = True
                for filename in files:
                    print(filename)
        if has:
            sys.exit(0)
        else:
            sys.exit(1)

    if hasattr(args, 'delindir'):
        delindir = args.delindir[0]
        if not delindir.endswith('/'):
            delindir += '/'
        directory = Directory(args.directory[0])
        directory.delete_duplicated_indir(delindir)
        sys.exit(0)
