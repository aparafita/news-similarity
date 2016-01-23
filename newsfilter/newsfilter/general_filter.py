# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import os.path

from collections import Counter, defaultdict
from datetime import timedelta

from spacy.en import English
from pymongo import MongoClient

from newsparser.data import load_feeds

from .ffs import ff


def counter_dist(c1, c2):
    return min(
        1, sum(
            min(c1[k], c2[k])
            for k in set(c1).intersection(set(c2))
        )
    )


def date_between(date, low=None, high=None):
    """ 
        Returns entry.date in [low, high] 
        If high is None, high = low
    """    
    
    b = date is not None

    if low:
        b = b and low <= date
    
    high = high or low
    
    if high:
        b = b and date <= high
        
    return b


class GeneralFilter:

    def __init__(self, folder):
        self.folder = folder
        self.feeds = load_feeds(folder)
        self.entries = { 
            feed: feed.get_entries() for feed in self.feeds 
        }

        self.nlp = English()


    def filter_entries(self):
        # Feed filtering
        print('Feed filtering')
        filtered_entries = {}

        for feed in self.feeds:
            print('\t' + feed.name)
            feedfilter = ff(feed.name, self.folder)
            filtered_entries[feed] = []

            for entry in self.entries[feed]:
                if feedfilter.filter_entry(entry):
                    filtered_entries[feed].append(entry)

            # Since this is a huge process, save entries current status here
            feed.save_entries(self.entries[feed])

        # Separate entries by dates
        by_date = {}

        for feed in self.feeds:
            d = defaultdict(list)
            
            for entry in filtered_entries[feed]:
                d[entry.data['date']].append(entry)
                
            by_date[feed] = d

        dates = { date for feed in self.feeds for date in by_date[feed].keys() }


        # Only check entries where there's something to process

        duplicate_dates = { # dates where to find duplicates
            feed: sorted(
                date
                for date, l in by_date[feed].items()
                if not all('duplicate' in entry.data['filter'] for entry in l)
            )
            
            for feed in self.feeds
        }

        news_agency_dates = sorted( # dates where to find news agency entries
            date
            for date in dates
            if not all(
                'news_agency_discarded' in entry.data['filter']
                for feed in self.feeds
                for entry in by_date[feed].get(date, [])
            )
        )


        dates = set(d for v in duplicate_dates.values() for d in v).union(
            set(news_agency_dates)
        )

        db = MongoClient().entries # open connection to load filtered_content


        def load_counter(entry):
            """ Returns counter of entry, creating it if it didn't exist """
            if hasattr(entry, 'counter'):
                return entry.counter

            # Get entry filtered content; note that only filtered entries get here
            for d in db[entry.feedname].find({'index': entry.index}):
                entry.content = d['filtered_content']
                break

            # Get its counter for later filters
            doc = self.nlp(entry.content, tag=False, parse=False, entity=False)
            del entry.content # to save memory, since we won't need it anymore

            entry.counter = Counter(
                word.text # use text instead of lower_, we want to check absolute similarity
                for word in doc
            )

            s = sum(entry.counter.values())
            for k in entry.counter:
                entry.counter[k] /= s

            return entry.counter

        # Duplicate filter
        print('Duplicate filter')
        dist_threshold = 0.75

        for feed in self.feeds:
            print('\t' + feed.name)
            feed_ents = set()

            for date in duplicate_dates[feed]:
                ents = by_date[feed].get(date, [])

                ents = [
                    entry
                    for entry in ents
                    if not entry.data['filter'].get('duplicate', False)
                ] # avoid all already-duplicate entries
                
                for entry in ents:
                    if not hasattr(entry, 'duplicate_set'):
                        entry.duplicate_set = { entry }

                for i, e1 in enumerate(ents):
                    feed_ents.add(e1)
                        
                    for e2 in ents[i+1:]:
                        if counter_dist(load_counter(e1), load_counter(e2)) >= dist_threshold:
                            union = e1.duplicate_set.union(e2.duplicate_set)
                            for e in union:
                                e.duplicate_set = union
                                
            while feed_ents:
                entry = feed_ents.pop()

                # From entry.duplicate_set, get an entry that hasn't been labelled
                # as duplicate
                for e1 in entry.duplicate_set:
                    if not e1.data['filter'].get('duplicate', True):
                        feed_ents.add(entry)
                        feed_ents.remove(e1)
                        entry = e1
                        break

                entry.duplicate_set.remove(entry)
                
                # first popped from duplicate_set won't be duplicated; the rest is
                entry.data['filter']['duplicate'] = False 
                
                while entry.duplicate_set:
                    e2 = entry.duplicate_set.pop()
                    feed_ents.remove(e2)
                    e2.data['filter']['duplicate'] = True # will be filtered

            feed.save_entries(self.entries[feed])


        # News Agency filter
        print('News Agency filter')
        all_ents = set()
        for date in news_agency_dates:
            ents = set()
            
            for feed in self.feeds:
                ents = ents.union(by_date[feed].get(date, []))

            ents = sorted([
                entry
                for entry in ents
                if not entry.data['filter'].get('duplicate', False) and \
                    not entry.data['filter'].get('news_agency_discarded', False)
            ], key=lambda e: e.data['date'])

            for entry in ents:
                if not hasattr(entry, 'agency_set'):
                    entry.agency_set = { entry }

            for i, e1 in enumerate(ents):
                all_ents.add(e1)

                for e2 in ents[i+1:]:
                    if counter_dist(load_counter(e1), load_counter(e2)) >= dist_threshold:
                        union = e1.agency_set.union(e2.agency_set)
                        for e in union:
                            e.agency_set = union
                                
        while all_ents:
            entry = all_ents.pop()

            for e1 in entry.agency_set:
                if not e1.data['filter'].get('news_agency_discarded', True):
                    all_ents.add(entry)
                    all_ents.remove(e1)
                    entry = e1
                    break

            entry.agency_set.remove(entry)

            # if there's anything else in the set, this is a news agency item
            entry.data['filter']['news_agency'] = bool(entry.agency_set)
            # first poped from agency_set won't be discarded; the rest is
            entry.data['filter']['news_agency_discarded'] = False

            while entry.agency_set:
                e2 = entry.agency_set.pop()
                all_ents.remove(e2)
                e2.data['filter']['news_agency'] = True # if we got here, the set had > 1 items.
                e2.data['filter']['news_agency_discarded'] = True # will be filtered     


        # Create data['newsbreaker'], which stores if entry passes all filters
        # Then, save
        for feed in self.feeds:
            for entry in self.entries[feed]:
                f = entry.data.get('filter', {})

                entry.data['newsbreaker'] = \
                    not f.get('discarded', True) and \
                    not f.get('duplicate', True) and \
                    not f.get('news_agency_discarded', True)

            feed.save_entries(self.entries[feed])