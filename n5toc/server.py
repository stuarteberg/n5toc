import sys
import argparse
import signal
import socket
import logging

from flask import Flask, request, render_template, abort, make_response, redirect, url_for

from .n5links import find_volumes, links_for_volumes, construct_nglink, TocEntry

ROOT_DIR = '/nrs/flyem/render/n5'

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('toc'))


@app.route('/toc')
def toc():
    vol_attrs = find_volumes(ROOT_DIR)
    links = links_for_volumes(vol_attrs)
    column_names = 'sample stage section version offset offset_link link'.split()
    return render_template('n5toc.html.jinja',
                           root_dir=ROOT_DIR,
                           entries=links.values(),
                           column_names=column_names)

def main():
    global ROOT_DIR
    print(sys.argv)

    # Don't log ordinary GET, POST, etc.
    #logging.getLogger('werkzeug').setLevel(logging.ERROR)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=9998)
    parser.add_argument('--root-dir', default=ROOT_DIR)
    parser.add_argument('--debug-mode', action='store_true')
    args = parser.parse_args()

    ROOT_DIR = args.root_dir

    # Terminate results in normal shutdown
    signal.signal(signal.SIGTERM, lambda signum, stack_frame: exit(1))

    print("Starting server on 0.0.0.0:{}".format(args.port))

    app.run(host='0.0.0.0', port=args.port, debug=args.debug_mode)
    print("Exiting normally.")

