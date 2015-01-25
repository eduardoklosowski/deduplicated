# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from flask import Flask, redirect, render_template, request
import jinja2

from .. import Directory, directory_get, directory_list, str_size


# Init app

jinja2.filters.FILTERS['str_size'] = str_size

app = Flask(__name__)


# Pages

@app.route('/')
def dirlist():
    directories = [(d[0], Directory(d[1])) for d in directory_list()]
    directories.sort(key=lambda d: str(d[1]).lower())
    return render_template('dirlist.html', directories=directories)


@app.route('/dir/add', methods=['post'])
def diradd():
    dirname = request.form.get('directory', '')
    if dirname:
        Directory(dirname)
    return redirect('/')


@app.route('/dir/<dirhash>')
def dirinfo(dirhash):
    return render_template('dirinfo.html', directory=directory_get(dirhash))


@app.route('/dir/<dirhash>/update')
def dirupdate(dirhash):
    directory = directory_get(dirhash)
    outtree = directory.update_tree()
    outhash = list(directory.hash_for_update())
    [directory.update_hash(i) for i in outhash]
    return render_template('dirupdate.html',
                           directory=directory,
                           outtree=outtree,
                           outhash=outhash)


# Run

def main():
    import sys
    from gunicorn.app.wsgiapp import run
    sys.argv = ['gunicorn',
                '--access-logfile=-',
                '--error-logfile=-',
                '-b', '127.0.0.1:5050',
                'deduplicated.web:app']
    run()
