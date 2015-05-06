# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys

from . import __version__, Directory, directory_delete, directory_list, str_size


# Argument parser

parser = argparse.ArgumentParser(prog='deduplicated')
subparsers = parser.add_subparsers(dest='action')

parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)

# list command
parser_list = subparsers.add_parser('list',
                                    help='list directories')

# update command
parser_update = subparsers.add_parser('update',
                                      help='update directories informations')
parser_update.add_argument('directory', nargs='*',
                           help='list of directories, if not present use all')

# duplicated command
parser_duplicated = subparsers.add_parser('duplicated',
                                          help='list duplicated files in directories')
parser_duplicated.add_argument('directory', nargs='*',
                               help='list of directories, if not present use all')

# check command
parser_check = subparsers.add_parser('check',
                                     help='update and duplicated directories')
parser_check.add_argument('directory', nargs='*',
                          help='list of directories, if not present use all')

# delete command
parser_delete = subparsers.add_parser('delete',
                                      help='delete directory information')
parser_delete.add_argument('directory', nargs='+',
                           help='list of directories')

# indir command
parser_indir = subparsers.add_parser('indir',
                                     help='check file exists in directories')
parser_indir.add_argument('file',
                          help='file for check')
parser_indir.add_argument('directory', nargs='*',
                          help='list of directories, if not present use all')

# delindir command
parse_delindir = subparsers.add_parser('delindir',
                                       help='delete duplicated files in directory')
parse_delindir.add_argument('directory', nargs=1,
                            help='directory information')
parse_delindir.add_argument('delindir',
                            help='subdirectory for delete')


# Utils

def print_directories(directories):
    rows = [(str(directory),
             str(directory.get_lastupdate() or '-') + ('i' if not directory.is_completed() else ''),
             str(directory.get_duplicated_hash()),
             str(directory.get_duplicated_files()),
             str_size(directory.get_duplicated_size()))
            for directory in directories]
    if not rows:
        return

    header = 'Directory', 'Last update', 'Hashs', 'Files', 'Size'
    sizes = [max(len(header[i]), *[len(row[i]) for row in rows]) for i in range(len(header))]
    print('%-*s  %-*s  %-*s  %-*s  %-*s' % (sizes[0], header[0], sizes[1], header[1], sizes[2], header[2],
                                            sizes[3], header[3], sizes[4], header[4]))
    for row in rows:
        print('%-*s  %-*s  %*s  %*s  %*s' % (sizes[0], row[0], sizes[1], row[1], sizes[2], row[2],
                                             sizes[3], row[3], sizes[4], row[4]))


def print_update_tree(directory):
    print('==> Update tree (%s): ' % directory, end='')
    print('+%d  ~%d  -%d' % directory.update_tree())


def print_update_hash(directory):
    for filename in directory.hash_for_update():
        print('Updating %s' % filename)
        directory.update_hash(filename)


def print_duplicated(directory):
    print('==> Duplicated (%s):' % directory)
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

    if 'directory' in args and not args.directory:
        args.directory = directory_list()

    if args.action == 'list':
        directories = [Directory(dirname, checkvalid=False) for dirname in directory_list()]
        print_directories(directories)
        sys.exit(0)

    if args.action == 'update':
        for dirname in args.directory:
            directory = Directory(dirname)
            print_update_tree(directory)
            print_update_hash(directory)
        sys.exit(0)

    if args.action == 'duplicated':
        for dirname in args.directory:
            directory = Directory(dirname)
            print_duplicated(directory)
        sys.exit(0)

    if args.action == 'check':
        for dirname in args.directory:
            directory = Directory(dirname)
            print_update_tree(directory)
            print_update_hash(directory)
            print_duplicated(directory)
        sys.exit(0)

    if args.action == 'delete':
        for dirname in args.directory:
            directory = Directory(dirname, checkvalid=False)
            directory_delete(directory.get_hash())

    if args.action == 'indir':
        has = False
        for dirname in args.directory:
            directory = Directory(dirname)
            files = directory.is_file_in(args.file)
            if files:
                has = True
                for filename in files:
                    print(filename)
        if has:
            sys.exit(0)
        else:
            sys.exit(1)

    if args.action == 'delindir':
        delindir = args.delindir
        if not delindir.endswith('/'):
            delindir += '/'
        directory = Directory(args.directory[0])
        directory.delete_duplicated_indir(delindir)
        sys.exit(0)

    parser.print_usage()
