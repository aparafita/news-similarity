# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import os.path

from flask import Flask, request, render_template, redirect, url_for
app = Flask(__name__)

from pymongo import MongoClient

mongo_client = MongoClient()
entries_db = mongo_client.entries
tests_db = mongo_client.newstagger

from newsparser.data import load_feeds

import newsbreaker
from newsbreaker.data import load_entries

feeds = []
entries_metadata = {}

import json
import re
regex_test = re.compile(r't[0-9]+', flags=re.IGNORECASE)

from collections import defaultdict

from random import sample, choice
MAX_BASE_FOR_PAIRS = 50
MAX_TESTS_PAIRS = 10
MAX_TESTS_POLITICS = 20


newsbreaker_initialized = False


@app.route('/', strict_slashes=False, methods=['GET'])
def main_page():
    return redirect(url_for('login'))


@app.route('/login', strict_slashes=False, methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user' in request.cookies:
            return render_template('directory.html')
        else:
            return render_template('login.html')

    elif request.method == 'POST':
        if not request.form.get('user'):
            return 'User not filled in login form', 400

        response = redirect(url_for('login'))
        response.set_cookie('user', request.form['user'])

        return response


@app.route('/tag_politics', strict_slashes=False, methods=['GET', 'POST'])
def tag_politics_page():
    if 'user' not in request.cookies:
        return 'User must be logged in to tag news', 401

    user = request.cookies['user']

    if request.method == 'GET':
        if 'stats' in request.args:
            n = tests_db['politics'].find().count()
            return json.dumps(
                { 
                    'user': user,
                    'politics_ratio': tests_db['politics'].find(
                        {'res': 1}
                    ).count() / n,
                    'count': n
                }, indent=2
            )

        try:
            maxtests = int(request.args.get('maxtests'))
        except:
            maxtests = MAX_TESTS_POLITICS

        tests = sample(
            [
                e 
                for feed in feeds 
                for e in entries_metadata[feed.name]
                if e.data.get('newsbreaker', False)
            ],
            min(
                sum(len(l) for l in entries_metadata.values()), 
                maxtests
            )
        )

        # Only filtered entries remain now

        if not tests:
            return 'Not a single entry to tag!', 500


        tests = load_entries(
            metadata_folder, 
            it=(
                (
                    feed,
                    (
                        entry
                        for entry in tests
                        if entry.feedname == feed.name
                    )
                )
                for feed in feeds
            )
        )

        return render_template('tag_politics.html', 
            title='Politics tagger',

            tests=[
                {
                    'feedname': entry.feedname,
                    'index': entry.index,
                    'title': entry.title, 
                    'content': entry.content,
                }

                for entry in tests
            ],

            enumerate=enumerate, # pass it to jinja
        )


    elif request.method == 'POST':
        tests = []
        for k, v in request.form.items():
            if regex_test.fullmatch(k):
                tests.append((k, str(v))) # str it just in case

        response = redirect(
            url_for('tag_politics_page') + '?maxtests=%d' % len(tests)
        )

        if not tests:
            return response

        tests = [
            [
                request.form[testname + 'entry'], 
                testvalue == '1' # 0 -> false, 1 -> true
            ]

            for testname, testvalue in tests
            if testvalue in ('-1', '1')
        ]

        if not tests:
            return response # don't insert to tests_db without any values

        tests_db['politics'].insert_many(
            { 
                'entry': test[0],
                'res': test[1],
                'user': user
            }

            for test in tests
        )

        return response


@app.route('/get_base_for_pairs', strict_slashes=False, methods=['GET'])
def get_base_for_pairs():
    if 'user' not in request.cookies:
        return 'User must be logged in to tag news', 401

    entries = {
        feed: [
            entry 
            for entry in entries_metadata[feed.name]
        ]

        for feed in feeds
    }

    if 'date' in request.args:
        entries = {
            feed: [e for e in l if e.data.get('date') == request.args['date']]
            for feed, l in entries.items()
        }

    entries = load_entries(
        metadata_folder, 
        it=(
            (
                feed, 
                (
                    entry
                    for entry in l
                    if entry.data.get('newsbreaker', False) and \
                        entry.data.get('politics')
                )
            )
            for feed, l in entries.items()
        )
    )

    try:
        max_entries = int(request.args.get('maxentries'))
    except:
        max_entries = MAX_BASE_FOR_PAIRS

    max_entries = min(len(entries), max_entries)
    max_entries = max_entries - max_entries % 3

    tests = sample(entries, max_entries)

    if not tests:
        # No more entries in this date
        return '%s cannot be used for tagger' % request.args.get('date'), 400

    # Only filtered entries remain now

    return render_template('get_base_for_pairs.html', 
        title='Base for pairs',

        tests=[
            [
                {
                    'feedname': tests[i*3 + j].feedname,
                    'index': tests[i*3 + j].index,
                    'title': tests[i*3 + j].title, 
                    'content': tests[i*3 + j].content,
                }

                for j in range(3)
            ]

            for i in range(len(tests) // 3)
        ],

        maxtests=request.args.get('maxtests'), # for tag_pairs_page

        enumerate=enumerate, # pass it to jinja
    )


@app.route('/tag_pairs', strict_slashes=False, methods=['GET', 'POST'])
def tag_pairs_page():
    if 'user' not in request.cookies:
        return 'User must be logged in to tag news', 401

    if not newsbreaker_initialized:
        newsbreaker.init(
            os.path.join(metadata_folder, 'topic_model'), 
            'topic_model.pkl', 
            'vocab.txt'
        )

        globals()['newsbreaker_initialized'] = True

    user = request.cookies['user']

    if request.method == 'GET':
        if 'stats' in request.args:
            n = tests_db['pairs'].find().count()
            return json.dumps(
                { 
                    'user': user,
                    'count': n
                }, indent=2
            )

        try:
            basefeed = request.args.get('feed') or choice(feeds).name
            baseindex = int(
                request.args.get('index') or choice(
                    [
                        entry 
                        for entry in entries_metadata[basefeed] 
                        if entry.data.get('newsbreaker') and \
                            entry.data.get('politics')
                    ]
                ).index
            )

        except KeyError as e:
            return 'Invalid feed: %s' % e.args, 400

        except ValueError as e:
            return 'Invalid index: %s' % e.args, 400


        for base_metadata in entries_metadata[basefeed]:
            if base_metadata.index == baseindex:
                break
        else:
            return '%s|%d not found' % (basefeed, baseindex), 400


        if not base_metadata.data.get('newsbreaker', False):
            return '%s|%d isn\'t a filtered entry' % (basefeed, baseindex), 400


        selected_date = base_metadata.data['date']

        # Get all entries in the same date as base
        # that are breakable, and get them as BreakableEntries
        day_entries = load_entries(
            metadata_folder, 
            it=(
                (
                    feed, 
                    (
                        entry
                        for entry in entries_metadata[feed.name]
                        if entry.data.get('date') == selected_date and \
                            entry.data.get('newsbreaker', False) and \
                            entry.data.get('politics')
                    )
                )
                for feed in feeds
            )
        )

        # Retrieve base as BreakableEntry
        for base in day_entries:
            if base.feedname == basefeed and base.index == baseindex:
                break
        else:
            return 'Base entry isn\'t breakable', 500

        # Get the WHAT distance of all entries with base
        day_entries = [
            (entry, entry.what_distance(base))
            for entry in day_entries
        ]

        # Get all pairs of entries that are not base
        # ordering by dist_e1 + dist_e2 ascending
        tests = [
            (e1, e2) 

            for e1, e2, _ in sorted(
                (
                    (e1, e2, d1 + d2)
                    for i, (e1, d1) in enumerate(day_entries)
                    for j, (e2, d2) in enumerate(day_entries)
                    if i < j and e1 != base and e2 != base
                ), key=lambda t: t[2]
            )
        ]

        # Get a sample of as much as request.args.get('maxtests', MAX_TESTS_PAIRS)
        try:
            max_tests = int(request.args.get('maxtests'))
        except:
            max_tests = MAX_TESTS_PAIRS

        tests = sample(
            tests, 
            min(len(tests), max_tests)
        )

        if not tests:
            # No more entries in this date
            return '%s|%d cannot be used for tagger' % (basefeed, baseindex), 400


        # Only filtered entries remain now

        return render_template('tag_pairs.html', 
            title='Pairs tagger',

            base={
                'feedname': base.feedname,
                'index': base.index,
                'title': base.title, 
                'content': base.content,
            },

            tests=[
                [
                    {
                        'feedname': e1.feedname,
                        'index': e1.index,
                        'title': e1.title, 
                        'content': e1.content,
                    },
                    {
                        'feedname': e2.feedname,
                        'index': e2.index,
                        'title': e2.title, 
                        'content': e2.content,
                    }
                ]

                for e1, e2 in tests
            ],

            enumerate=enumerate, # pass it to jinja
        )


    elif request.method == 'POST':
        if 'base' not in request.form:
            return 'Base not found in form inputs', 400

        tests = []
        for k, v in request.form.items():
            if regex_test.fullmatch(k):
                tests.append((k, str(v))) # str it just in case

        response = redirect(
            url_for('get_base_for_pairs') + '?maxtests=%d' % len(tests)
        )

        if not tests:
            return response

        tests = [
            [
                request.form[testname + 'e1'], 
                request.form[testname + 'e2'], 
                int(testvalue == '1') # 0 or 1
            ]

            for testname, testvalue in tests
            if testvalue in ('-1', '1')
        ]

        if not tests:
            return response # don't insert to tests_db without any values

        tests_db['pairs'].insert_many(
            { 
                'base': request.form['base'], 
                'e1': test[0], 
                'e2': test[1], 
                'res': test[2],
                'user': user
            }

            for test in tests
        )

        return response


def run(metadata_folder):
    global feeds, entries_metadata
    globals()['metadata_folder'] = metadata_folder
    
    feeds += load_feeds(metadata_folder)
    for feed in feeds:
        entries_metadata[feed.name] = feed.get_entries()

    return app.run(
        threaded=False,
        port=8080,
        debug=False
    )