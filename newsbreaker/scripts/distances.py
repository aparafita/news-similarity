# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

# Loads ne_vector of every article in the database

import os.path
import sys
from datetime import datetime, timedelta

from pandas import to_datetime

from newsbreaker.data import load_entries
from newsbreaker import init


def get_entry(feedname, index):
    index = int(index) # just in case

    for entry in entries:
        if entry.feedname == feedname and entry.index == index:
            return entry
    else:
        raise KeyError((feedname, index))


if __name__ == '__main__':
    viz = sys.argv[1]
    feedname = sys.argv[2]
    index = sys.argv[3]


    folder = 'data'
    init(os.path.join(folder, 'topic_model'), 'topic_model.pkl', 'vocab.txt')

    entries = load_entries(folder)

    # Filter entries: only politics
    entries = [entry for entry in entries if entry.data.get('politics')]

    from pymongo import MongoClient
    mongo_client = MongoClient()

    dists_db = mongo_client.distances


    collection = '_'.join(sys.argv[1:4])
    col = getattr(dists_db, collection)

    base = get_entry(feedname, index)
    base_date = to_datetime(base.data['date'])


    if viz == 'network':
        ids = lambda entry: '%s|%s' % (entry.feedname, entry.index)

        date = str(base_date.date())
        entries = [ 
            entry 
            for entry in entries 
            if entry.data.get('date') == date
        ]

        entries = sorted(entries, key=ids)
        # sort them because we want pairs ordered by entry_repr

        processed, total = 0, len(entries) * (len(entries) + 1) / 2
        for i, e1 in enumerate(entries):
            for e2 in entries[i:]:
                ids_pair = '%s_%s' % (ids(e1), ids(e2))

                if col.find_one({'_id': ids_pair}) is None:
                    col.insert_one(
                        { 
                            '_id': ids_pair, 
                            'dist': e1.distance(e2) 
                        }
                    )

                processed += 1

                print('%.4d/%.4d' % (processed, total), datetime.now())


    elif viz == 'week':
        day = timedelta(days=1)
        dates = [ str((base_date + n * day).date()) for n in range(7) ]

        entries = [ 
            entry 
            for entry in entries 
            if entry.data.get('date') in dates 
        ]

        processed, total = 0, len(entries)
        while entries:
            entry = entries.pop()
            ids = '%s|%s' % (entry.feedname, entry.index)

            if col.find_one({'_id': ids}) is None:
                col.insert_one(
                    { 
                        '_id': ids, 
                        'dist': base.distance(entry) 
                    }
                )

            processed += 1

            print('%.4d/%.4d' % (processed, total), datetime.now())