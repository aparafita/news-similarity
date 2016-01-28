# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

"""
    Transforms network and week distance collections in DB 
    to json files ready for viz
"""

import sys
import json

from newsbreaker.data import load_entries
from pymongo import MongoClient


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
    base_feedname = sys.argv[1]
    base_index = sys.argv[2]
    base_name = '%s|%s' % (base_feedname, base_index)
    threshold = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.6 # for network

    client = MongoClient()
    db = client.distances

    entries = load_entries('data')
    feed_names = sorted({entry.feedname for entry in entries})
    base_entry = get_entry(base_name)

    # Network
    result = {}
    result['threshold'] = threshold
    result['title'] = base_entry.title
    result['feedNames'] = feed_names
    result['nodes'] = []
    result['links'] = []

    dists = list(
        getattr(db, 'network_%s' % entry_ids(base_entry, sep='_')).find()
    )

    nodes = set()
    for dist in dists:
        source_name, target_name = dist['_id'].split('_')
        
        source_entry = get_entry(source_name)
        target_entry = get_entry(target_name)

        nodes.add(source_entry)
        nodes.add(target_entry)

        dist = dist['dist']

        result['links'].append(
            {
                'source': source_name,
                'target': target_name,
                'value': dist
            }
        )

    nodes = list(nodes)
    
    nodes_dict = { entry_ids(node): n for n, node in enumerate(nodes) }
    for link in result['links']:
        link['source'] = nodes_dict[link['source']]
        link['target'] = nodes_dict[link['target']]

    result['nodes'] = [
        {
            "name": entry_ids(entry),
            "feed": feed_names.index(entry.feedname),
            "index": entry.index,
            "title": entry.title
        } 

        for entry in nodes
    ]

    with open('network_%s.json' % base_entry.data.get('date'), 'w') as f:
        f.write(json.dumps(result, indent=2))


    # Week
    result = {}
    result['threshold'] = threshold
    result['base_title'] = base_entry.title
    result['base_name'] = base_name
    result['feedNames'] = feed_names
    result['entries'] = []

    dists = list(
        getattr(db, 'week_%s' % entry_ids(base_entry, sep='_')).find()
    )

    for dist in dists:
        entryid = dist['_id']
        entry = get_entry(entryid)

        if entry == base_entry:
            continue

        dist = dist['dist']

        result['entries'].append(
            {
                "name": entryid,
                "feed": feed_names.index(entry.feedname),
                "title": entry.title,
                "date": entry.data.get('date'),
                "dist": dist,
            }
        )

    with open('week_%s.json' % base_name.replace('|', ''), 'w') as f:
        f.write(json.dumps(result, indent=2))