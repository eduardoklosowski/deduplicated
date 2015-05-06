# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from flask import Flask, redirect, render_template, request
import jinja2
from tempfile import NamedTemporaryFile

from .. import Directory, directory_by_hash, directory_delete, directory_list, str_size


# Init app

jinja2.filters.FILTERS['str_size'] = str_size

app = Flask(__name__)


# Pages

@app.route('/')
def dirlist():
    directories = [(d[0], Directory(d[1], checkvalid=False)) for d in directory_list(hashid=True)]
    return render_template('dirlist.html', directories=directories)


@app.route('/dir/add', methods=['post'])
def diradd():
    dirname = request.form.get('directory', '')
    if dirname:
        Directory(dirname)
    return redirect('/')


@app.route('/dir/<dirhash>')
def dirinfo(dirhash):
    return render_template('dirinfo.html',
                           directory=directory_by_hash(dirhash, checkvalid=False))


@app.route('/dir/<dirhash>/option', methods=['post'])
def diroption(dirhash):
    directory = directory_by_hash(dirhash)
    directory.set_option_follow_link('followlink' in request.form)
    directory.save_meta()
    directory.exclude = request.form.get('exclude', '').splitlines()
    directory.save_exclude()
    return redirect('/dir/%s' % dirhash)


@app.route('/dir/<dirhash>/update')
def dirupdate(dirhash):
    directory = directory_by_hash(dirhash)
    outtree = directory.update_tree()
    outhash = list(directory.hash_for_update())
    [directory.update_hash(i) for i in outhash]
    return render_template('dirupdate.html',
                           directory=directory,
                           outtree=outtree,
                           outhash=outhash)


@app.route('/dir/<dirhash>/delete')
def dirdelete(dirhash):
    directory_delete(dirhash)
    return redirect('/')


@app.route('/dir/<dirhash>/deletefile', methods=['post'])
def dirdeletefile(dirhash):
    directory = directory_by_hash(dirhash)
    for filename in request.form.getlist('file'):
        directory.delete_file(filename)
    return redirect('/dir/%s' % dirhash)


@app.route('/dir/<dirhash>/indir', methods=['post'])
def indir(dirhash):
    directory = directory_by_hash(dirhash)
    with NamedTemporaryFile(prefix='deduplicated-') as tmpfile:
        request.files.get('file').save(tmpfile.name)
        files = directory.is_file_in(tmpfile.name)
    return render_template('indir.html',
                           name=request.files.get('file').filename,
                           files=files)


# Run

def main():
    app.run(port=5050)
