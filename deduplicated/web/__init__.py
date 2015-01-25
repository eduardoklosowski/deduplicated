# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Eduardo Klosowski
# License: MIT (see LICENSE for details)
#

from flask import Flask, render_template
import jinja2

from .. import Directory, directory_list, str_size


# Init app

jinja2.filters.FILTERS['str_size'] = str_size

app = Flask(__name__)


# Pages

@app.route('/')
def dirlist():
    directories = [(d[0], Directory(d[1])) for d in directory_list()]
    directories.sort(key=lambda d: str(d[1]).lower())
    return render_template('dirlist.html', directories=directories)


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
