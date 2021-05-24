import sys
import argparse
import signal
import socket
import logging

from flask import Flask, request, render_template, abort, make_response, redirect, url_for

from .n5links import find_volumes, links_for_volumes, construct_nglink, TocEntry

ROOT_DIR = '/nrs/flyem/render/n5'
EXCLUDE_DIRS = []

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('toc'))


@app.route('/toc')
def toc():
    print(f"Finding volumes in {ROOT_DIR} (excluding {EXCLUDE_DIRS})")
    vol_attrs = find_volumes(ROOT_DIR, EXCLUDE_DIRS)
    print(f"Constructing links for {len(vol_attrs)} volumes")
    links = links_for_volumes(vol_attrs)
    print("Rendering template")
    column_names = 'sample stage section version offset offset_link link'.split()
    return render_template('n5toc.html.jinja',
                           root_dir=ROOT_DIR,
                           entries=links.values(),
                           column_names=column_names)

def main():
    global ROOT_DIR
    global EXCLUDE_DIRS
    print(sys.argv)

    # Don't log ordinary GET, POST, etc.
    #logging.getLogger('werkzeug').setLevel(logging.ERROR)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=9998)
    parser.add_argument('--root-dir', default=ROOT_DIR)
    parser.add_argument('--exclude-dirs', nargs='*')
    parser.add_argument('--debug-mode', action='store_true')
    args = parser.parse_args()

    ROOT_DIR = args.root_dir
    EXCLUDE_DIRS = args.exclude_dirs

    # Terminate results in normal shutdown
    signal.signal(signal.SIGTERM, lambda signum, stack_frame: exit(1))

    print("Starting server on 0.0.0.0:{}".format(args.port))

    app.run(host='0.0.0.0', port=args.port, debug=args.debug_mode)
    print("Exiting normally.")

