# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import json
import os
import os.path

from flask import Flask, Response, request, abort
from newsparser.data import load_feeds

folder = 'feeds'
feeds = load_feeds(folder)

app = Flask(__name__)


def get_feed(feedname):
    for feed in feeds:
        if feed.name == feedname:
            return feed
    # returns None if it isn't found


@app.route('/')
def hello_world():
    return """
    <h1>newsparser</h1>
    <ul>
        {}
    </ul>""".format(
        '\n'.join([
            '<li><a href="/feeds/{name}">{name}</a></li>'.format(name=feed.name)
            for feed in feeds
        ])
    )


@app.route('/feeds/', methods=['GET'])
def feed_list():
    with open(os.path.join(folder, 'feeds.json')) as f:
        return Response(f.read(), mimetype='application/json')


@app.route('/feeds/<feedname>/', methods=['GET'])
def feed_metadata(feedname):
    feed = get_feed(feedname)

    if feed is None:
        abort(404)
    else:
        best_match = request.accept_mimetypes.best_match(
            ['application/json', 'text/html']
        )

        if best_match == 'application/json':
            return Response(
                json.dumps(feed.get_metadata()), 
                mimetype='application/json'
            )
        else:
            return """
                <h1> {feedname} </h1>
                <ul>
                    {entries}
                </ul>
            """.format(
                feedname=feed.name,
                entries='\n'.join([
                    '<li><a href="entries?id={index}">'
                    '{index} | {title}</a></li>'.format(
                        index=entry.index,
                        title=entry.title
                    )
                    for entry in feed.get_entries()
                ])
            )


@app.route('/feeds/<feedname>/entries/', methods=['GET'])
def feed_entries(feedname):
    feed = get_feed(feedname)

    if feed is None:
        abort(404)
    else:
        low = request.args.get('from')
        high = request.args.get('to')
        ids = request.args.get('id')

        if not (ids is None):
            try:
                ids = int(ids)
            except:
                abort(400)

            if ids < 0:
                ids = ids % feed.num_entries

            low = ids
            high = ids + 1

        if low is None:
            low = 0
        if high is None:
            high = feed.num_entries

        try:
            low = int(low)
            high = int(high)
        except:
            abort(400)

        return Response(json.dumps([
            x.get_metadata()
            for x in feed.get_entries(low, high)
        ]), mimetype='application/json')