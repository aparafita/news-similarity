# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from newsparser.data import load_feeds
from .breakable_entry import BreakableEntry


def load_entries(folder, it=None):
    if it is None:
        feeds = load_feeds(folder)
        
        return [
            BreakableEntry(entry.folder, feed, entry.get_metadata())

            for feed in feeds
            for entry in feed.get_entries()
            if entry.data.get('newsbreaker')
        ]
    else:
        return [
            BreakableEntry(entry.folder, feed, entry.get_metadata())

            for feed, entries in it
            for entry in entries
            if entry.data.get('newsbreaker')
        ]


def save_entries(folder, entries):
    d = {}

    for entry in entries:
        if type(entry) != BreakableEntry:
            raise TypeError("Entry must be BreakableEntry")

        if entry.feed not in d:
            d[entry.feed] = []

        d[entry.feed].append(entry)

    for feed, l in d.items():
        feed.save_entries(l)
