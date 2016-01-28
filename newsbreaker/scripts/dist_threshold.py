# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

"""
    Gets week distance data from DB and runs tests to test similarity between
    base entry and the rest of the entries. Those tests are stored in 
    threshold_{base_entry_id} and from there the right threshold can be found
"""

import sys
import json
import random

from collections import defaultdict

from newsbreaker.data import load_entries
from pymongo import MongoClient

from sklearn.lda import LDA # nothing to do with Latent Dirichlet Analysis
# This is Linear Discriminant Analysis, which is used to get the threshold
# for similar entries
import numpy as np


def threshold(base_entry_id):
    """ 
        Given a collection, returns the threshold to distinguish classes.
        That threshold is retrieved with the decision boundary of LDA, 
        which will be computed with -lda.intercept_[0] / lda.coef_[0]
        (since this problem deals with dimension 1)
    """

    with MongoClient() as client:
        col = getattr(
            client.distances, 
            'threshold_%s' % base_entry_id.replace('|', '_')
        )

        tests = list(col.find()) # this is done to ensure the same order for each test
        lda = LDA()

        X = np.array([ [d['dist']] for d in tests ])
        Y = np.array([ int(d['similar']) for d in tests ])

        lda.fit(X, Y)

        return (-lda.intercept_[0] / lda.coef_[0])[0]


def run_tests(base_entry_id, multiple=10):
    """ Stores up to 'multiple' tests to the DB and runs those tests """

    with MongoClient() as client:
        col = getattr(
            client.distances, 
            'week_%s' % base_entry_id.replace('|', '_')
        )

        dists = list(col.find()) # to close the connection asap

        col_threshold = getattr(
            client.distances, 
            'threshold_%s' % base_entry_id.replace('|', '_')
        )

        existing_tests = set(
            d['_id']
            for d in col_threshold.find({}, { '_id': True })
        )

    dists = [
        d
        for d in dists
        if d['_id'] not in existing_tests
    ]

    by_date = defaultdict(list)
    for d in dists:
        by_date[get_entry(d['_id']).data.get('date')].append(d)

    for l in by_date.values():
        random.shuffle(l) # make tests "random" for each date

    dists = []
    for l in map(
        lambda pair: pair[1], 
        sorted(by_date.items(), key=lambda pair: pair[0])
    ):
        dists += l

    base_entry = get_entry(base_entry_id)

    tmp = []
    col_name = 'threshold_%s' % base_entry_id.replace('|', '_')

    def save(tmp):
        with MongoClient() as client:
            col = getattr(client.distances, col_name)
            col.insert_many(tmp)


    try:
        for d in dists:
            entry = get_entry(d['_id'])

            print(base_entry.title)
            print(entry.title)
            similar = input('Similar (y/[n]) > ').lower() == 'y' # default to False

            tmp.append({'_id': d['_id'], 'dist': d['dist'], 'similar': similar})

            if len(tmp) >= multiple:
                save(tmp)
                
                tmp = [] # reset temporal list

            print() # Separation between tests

        if tmp:
            save(tmp)
    except KeyboardInterrupt:
        if tmp:
            save(tmp)


def entry_ids(entry, sep='|'):
    return '%s%s%d' % (entry.feedname, sep, entry.index)


def get_entry(name, sep='|'):
    feedname, index = name.split(sep)
    index = int(index)

    for entry in entries:
        if entry.feedname == feedname and entry.index == index:
            return entry
    else:
        raise KeyError(name)


if __name__ == '__main__':
    action_tests = sys.argv[1] == 'tests' # else, threshold

    base_feedname = sys.argv[2]
    base_index = sys.argv[3]
    base_name = '%s|%s' % (base_feedname, base_index)
    multiple = int(sys.argv[4]) if len(sys.argv) >= 5 else None

    entries = load_entries('data')
    
    if action_tests:
        if multiple:
            run_tests(base_name, multiple=int(multiple))
        else:
            run_tests(base_name)
    else:
        print('Threshold:', threshold(base_name))
