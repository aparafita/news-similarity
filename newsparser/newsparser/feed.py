# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import os.path
import json

from . import __version__, __url__

import feedparser as fp
# Set User-Agent for feedparser
fp.USER_AGENT = "newsparser/{version} +{url}".format(
    version=__version__,
    url=__url__
)

from .entry import Entry
from . import exceptions

import logging


class Feed(object):
    """
        Class that stores metadata from feeds and its entries.
        Can also update the feed with the new data
        and load and save entries.
    """

    ENTRIES_PER_FILE = 1000
    ENTRIES_METADATA_FILE_FORMAT = "entries%.5d.json"


    def __init__(self, folder, name, link=None, metadata=None):
        """
            Main constructor for Feed.
            Pass it the folder where to load/save its data
            and the feed name.
            If metadata, a dict, is given, its metadata will be loaded from there.
            If None, it will try to download it 
        """
        self.folder = folder
        self.name = name

        # Make sure the {feedname} folder is created
        feed_folder = os.path.join(folder, name)
        if not os.path.exists(feed_folder):
            os.makedirs(feed_folder)

        if metadata is None:
            try:
                with open(os.path.join(folder, self.name, 'metadata.json')) as f:
                    metadata = json.loads(f.read())
            except:
                metadata = {}

        self.link = link or metadata.get('link')

        self.etag = metadata.get('etag')
        self.modified = metadata.get('modified')
        self.language = metadata.get('language')
        self.num_entries = metadata.get('num_entries', 0)
        self.active = metadata.get('active', True)


    def get_metadata(self):
        """
            Returns a dict with the metadata stored in this Feed instance
        """

        return {
            'name': self.name,
            'link': self.link,
            'etag': self.etag,
            'modified': self.modified,
            'language': self.language,
            'num_entries': self.num_entries,
            'active': self.active
        }
        

    def save_metadata(self):
        """
            Saves a json file with a dict retrieved from get_metadata()
        """

        with open(os.path.join(self.folder, self.name, 'metadata.json'), 'w') as f:
            f.write(json.dumps(self.get_metadata(), indent=2))


    def update(self):
        """
            Called whenever we want to parse the RSS feed again.
            Updates metadata from the feed and gets new entries.
            Stores all the data in the respective json files.
        """

        if not self.active:
            # Don't try to update a feed that has been deactivated
            logging.warning('Feed "{name}" is deactivated, '
                'so couldn\'t be updated'.format(name=self.name))
            return

        # Try retrieving the feed
        feed = fp.parse(self.link, etag=self.etag, modified=self.modified)

        if feed.get('bozo', 0):
            # There's been an error in the parsing of the XML feed
            self.active = False
            raise exceptions.BozoException(self, feed)
        
        # Check if we got a redirect or an error
        status = feed.get('status', 500)

        if status == 304:
            # Not modified. Don't do anything else
            logging.info('Feed "{name}" not modified'.format(name=self.name))
            return

        elif 300 <= status and status < 400:
            # Consider redirects to another location
            logging.info('Feed "{name}" redirected from "{old}" to "{new}"'.\
                format(
                    name=self.name,
                    old=self.link,
                    new=feed.get('href', '')
                )
            )

            # If there's a new url, it will be updated just after this if

        elif 400 <= status and status < 500:
            # Has the feed disappeared?
            logging.warning('Feed "{name}" lost with status %d'.format(
                    name=self.name
                ) % status
            )
            self.active = False
            raise exceptions.LostFeedException(self, feed)

        elif status >= 500:
            # Server Exception. Notify it, but don't do anything else.
            # We'll try later
            logging.warning('Feed "{name}" got status code %d'.format(
                    name=self.name
                ) % status
            )
            return

        self.etag = feed.get('etag')
        self.modified = feed.get('modified')
        self.link = feed.get('href', self.link)
        self.language = feed.get('language')

        # Retrieve new entries, asign them an index and put them in the list
        self.save_entries(self.new_entries(feed))
        self.save_metadata()


    def new_entries(self, feed):
        """
            Private method called by update to retrieve entry metadata 
            from the parsed feed given as parameter.
            Returns a list with all the new entries, if any.
        """

        entries = {}

        for i, entry in enumerate(feed['entries']):
            entry_json = {}
            
            entry_json['published'] = entry.get('published')
            entry_json['author'] = entry.get('author')
            entry_json['title'] = entry.get('title')
            entry_json['link'] = entry.get('link')
            entry_json['entryid'] = entry.get('id', entry_json['link'])
            
            # Add tags too, but just the term
            entry_json['tags'] = [
                t['term']
                for t in entry.get('tags', [])
                if 'term' in t
            ]

            entry_json['index'] = i

            entries[str(entry_json['entryid'])] = entry_json

        # Get only new entries
        # Retrieve the set of all entryids
        entryids = {
            e.entryid
            for e in self.get_entries()
            if e.entryid
        }

        entries = [
            entries[ids]
            for ids in (
                set(entries.keys()) - entryids
            )
        ]

        for i, entry in enumerate(sorted(entries, key=lambda e: e['index'])):
            # Notice how the previous index loses its value
            # Its only purpose was to order entries after the filtering
            entry['index'] = self.num_entries + i

        return [ Entry(self.folder, self.name, entry) for entry in entries ]


    def save_entries(self, entries):
        """
            Saves current state of passed entries, 
            locating them according to their index value.
        """

        getnfile = lambda x: int(x / Feed.ENTRIES_PER_FILE) # utility function

        entries = sorted(entries, key=lambda entry: entry.index)

        i = 0
        new_num_entries = max(
            self.num_entries, 
            max( [ x.index for x in entries ] or [-1] ) + 1
        )

        while i < len(entries):
            nfile = getnfile(entries[i].index)

            # Get all entries from passed entries that belong to the same file
            j = i + 1
            while j < len(entries) and getnfile(entries[j].index) == nfile:
                j += 1

            # Use those indexes to get the entries located in the same file
            block_entries = entries[i:j]

            # Get all entries from this file
            file_entries = self.get_entries(
                nfile * Feed.ENTRIES_PER_FILE,
                (nfile + 1) * Feed.ENTRIES_PER_FILE
            )

            # Replace all entries belonging to that file
            k = 0
            for l in range(Feed.ENTRIES_PER_FILE):
                if k < len(block_entries):
                    # More entries to add or replace
                    if l < len(file_entries):
                        if block_entries[k].index < file_entries[l].index:
                            file_entries.insert(l, block_entries[k])
                            k += 1
                        elif block_entries[k].index == file_entries[l].index:
                            # Replace
                            file_entries[l] = block_entries[k]
                            k += 1
                        else:
                            # Nothing to add before this, nor to replace. 
                            continue
                    else:
                        # Nothing more to check on. So add what remains
                        file_entries += block_entries[k:]
                        break
                else:
                    # Nothing more to add or replace, so leave it like it is now
                    break

            # Save file
            file_result = json.dumps(
                [e.get_metadata() for e in file_entries], 
                indent=2
            )

            # Avoid KeyboardInterrupt
            while True:
                try:    
                    with open(os.path.join(
                        self.folder,
                        self.name,
                        self.ENTRIES_METADATA_FILE_FORMAT % (nfile)
                    ), 'w') as f:
                        f.write(file_result)

                    break
                except KeyboardInterrupt:
                    pass

            i = j

        self.num_entries = new_num_entries
        

    def get_entries(self, low=None, high=None):
        """
            Returns list with metadata from entries[low:high]
        """

        if low is None:
            low = 0

        if high is None:
            high = self.num_entries

        # Consider the python negative notation for indexes
        if low < 0:
            low = (low % self.num_entries) if self.num_entries else 0
        if high < 0:
            high = (high % self.num_entries) if self.num_entries else 0

        if low >= high: 
            # Avoid trivial cases
            return []

        entries = []
        lowfile = int(low / Feed.ENTRIES_PER_FILE)
        highfile = int((high-1) / Feed.ENTRIES_PER_FILE)

        for nfile in range(lowfile, highfile + 1):
            try:
                # Exceptions could occur trying to access files that didn't exist
                # because you asked for entry index that is higher than the highest.
                # In that case, an Exception will be raised, 
                # and we will return only what we found
                with open(os.path.join(
                        self.folder, self.name, 
                        self.ENTRIES_METADATA_FILE_FORMAT % nfile
                    )) as f:
                    j = [ Entry(self.folder, self.name, d) for d in json.loads(f.read()) ]
            except:
                # File doesn't exist, so nothing will be added to entries
                j = []

            entries += j

        # Get low level
        i = 0
        while i < len(entries):
            if entries[i].index >= low:
                break
            else:
                i += 1

        # Get high level
        j = len(entries) - 1
        while j >= 0:
            if entries[j].index < high:
                j += 1
                break
            else:
                j -= 1

        return entries[i:j]


    def __str__(self):
        return json.dumps(self.get_metadata(), indent=2)


    def __repr__(self):
        return "Feed: " + self.name