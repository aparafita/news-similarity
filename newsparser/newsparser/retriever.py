# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

"""
    Module that stores entries in the server
    polling the feeds RSS for new entries.
    Notice how this polling doesn't retrieve the contents
    of the entries, just the metadata.

    Usage example:
        * Create a folder named as the variable in this module "folder", 
          which defaults to 'feeds'
        * Call add_feed with all feed names and links 
          you want to add to the system.

        * Whenever you want to update the feeds (1 hour intervals recommended),
          call update_feeds.
"""

import json
import os
import shutil

import newsparser
from . import Feed
from .exceptions import NewsparserException

import logging


folder = 'feeds'


def save_feeds(feeds):
    """ Saves feed list only with name and link of each feed """

    with open(os.path.join(folder, 'feeds.json'), 'w') as f:
        f.write(json.dumps([
            {
                'name': feed.name,
                'link': feed.link
            }

            for feed in feeds
        ], indent=2))


def load_feeds():
    """
        Returns a list with all the feeds added to the system
    """

    try:
        with open(os.path.join(folder, 'feeds.json'), 'r') as f:
            j = json.loads(f.read())
    except:
        j = []

    return [ Feed(folder, x['name']) for x in j ]


def update_feeds():
    """ Retrieves RSS feed in search for new entries """

    logging.info("Updating feeds")
    print("Updating feeds")
    feeds = load_feeds()

    for feed in feeds:
        try:
            feed.update()
        except NewsparserException as e:
            # Feed is deactivated in these cases.
            logging.warning('Feed "{name}" has been deactivated '
                'because of Exception {e}'.format(name=feed.name, e=e))


def add_feed(name, link):
    """ Adds a feed to the system """

    feeds = load_feeds()

    feed = Feed(folder, name, link=link)
    feeds.append(feed)

    feed.save_metadata()
    save_feeds(feeds)


def delete_feed(name):
    """ Deletes a feed from the system """
    
    feeds = load_feeds()
    feeds = [ x for x in feeds if x.name != name ]

    try:
        shutil.rmtree(os.path.join(folder, name))
    except:
        # Doesn't exist? Doens't matter; we were deleting it anyway
        pass

    save_feeds(feeds)


def load_feed(name):
    """ Returns the feed whose name is that in the parameter """
    feeds = load_feeds()

    for feed in feeds:
        if feed.name == name:
            return feed


def change_active(name, active):
    """ Change active status for the given feed """
    feeds = load_feeds()

    feed = None
    for x in feeds:
        if x.name == name:
            feed = x
            break

    if feed is None:
        raise KeyError(name)

    feed.active = active
    save_feeds(feeds)