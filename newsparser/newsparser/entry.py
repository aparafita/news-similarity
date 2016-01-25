# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

"""
    Module with class Entry, that stores metadata for an Entry
    and functions for its content download and storage.
"""

import os.path
import json

from datetime import datetime

from newspaper import Article, ArticleException

try:
    from pymongo import MongoClient
    db = MongoClient().entries

except:
    db = None


class Entry(object):
    db = db

    CONTENT_KEY = 'raw_content'

    def __init__(self, folder, feedname, data):
        """
            Constructor of entry. 

            Parameters:
                folder - absolute or relative path to the folder where to find
                    the feed folder.
                feedname - name of the feed this entry belongs to
                data - dict with all the metadata of the entry
        """

        self.folder = folder
        self.feedname = feedname

        self.index = int(data['index'])
        self.entryid = data.get('entryid', data.get('link'))
        self.link = data.get('link')
        self.title = data.get('title')
        self.author = data.get('author')
        self.published = data.get('published')
        self.tags = data.get('tags')

        self.downloaded = data.get('downloaded', False)
        self.content = None

        self.data = data.get('data', {})


    def get_metadata(self):
        """
            Returns a dict with all the metadata from this entry,
            to use for saving in the feed storage
        """

        return {
            'index': self.index,
            'entryid': self.entryid,
            'link': self.link,
            'title': self.title,
            'author': self.author,
            'published': self.published,
            'tags': self.tags,
            'downloaded': self.downloaded,

            'data': self.data
        }


    def __str__(self):
        return json.dumps(self.get_metadata(), indent=2)


    def __repr__(self):
        return "Entry {feedname}|{index}: {title}".format(
            feedname=self.feedname,
            index=self.index,
            title=self.title
        )


    def __hash__(self):
        return hash('%s%d' % (self.feedname, self.index))


    def __eq__(self, other):
        return self.feedname == other.feedname and self.index == other.index


    def load_content(self):
        if self.db is None:
            raise Exception('Trying to load content without a DB')

        if not (self.content is None):
            return self.content

        if self.downloaded:
            d = self.db[self.feedname].find_one({'index': self.index})

            if d is None:
                # Entry not found
                raise Exception('Entry content not found in DB')
            else:
                self.content = d[self.CONTENT_KEY]
                return self.content # and avoid entering for-else

        else:
            # Try downloading it and storing its content to DB
            article = Article(self.link)

            try:
                article.download()
                article.parse()
                self.content = article.text.strip()

                self.db[self.feedname].update_one(
                    { 'index': self.index },
                    { '$set': { self.CONTENT_KEY: self.content }},
                    upsert=True
                )

                self.downloaded = True
                return self.content
                
            except ArticleException:
                # Don't write anything. It can be downloaded later (or not)
                self.downloaded = False
                self.content = ''
                return self.content