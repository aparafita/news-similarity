# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

"""
    Module that stores entries in the local terminal
    and polls the server for new entries.
    When a new one is found, it retrieves its contents from its url.
"""

import time
import os.path
import json

import requests

from . import Feed, Entry

url = 'http://newsparser704.pythonanywhere.com/'
headers = {'Accept': 'application/json'}


def update_local(folder, download_content=True):
    """ Updates local storage to the server's state """
    feeds = requests.get(url + 'feeds', headers=headers).json()

    with open(os.path.join(folder, 'feeds.json'), 'w') as f:
        f.write(json.dumps(feeds, indent=2))

    for name in map(lambda x: x['name'], feeds):
        print ('Downloading from {}'.format(name))

        # Try to obtain the last entry_index that's been downloaded
        try:
            with open(os.path.join(folder, name, 'metadata.json')) as f:
                j = json.loads(f.read())
                low = j.get('num_entries', 0)
        except FileNotFoundError:
            low = 0

        d = requests.get(url + 'feeds/{}'.format(name), headers=headers).json()

        if low == d.get('num_entries', 0):
            continue # nothing new to download

        feed = Feed(folder, name, metadata=d)
        # Set low as num_entries so we can execute save_entries
        # with the new entries correctly. 
        # This method will update num_entries accordingly when finished.
        feed.num_entries = low 

        j = requests.get(
            url + 'feeds/{feedname}/entries'.format(feedname=name),
            params={ 'from': low }
        ).json()

        # Download entries
        entries = []
        try:
            for metadata in j:
                entry = Entry(folder, feed.name, metadata)
            
                if download_content:
                    entry.load_content()

                entries.append(entry)

                try:
                    time.sleep(0.5)
                except AttributeError:
                    time.wait(0.5)
            
            feed.save_entries(entries)
            # Notice that feed won't be really affected until the following line
            # since num_entries won't be updated in the storage file
            # until all metadata is saved. So, interrupting it here isn't a risk
            feed.save_metadata() 

        except:
            # Save what was processed
            feed.save_entries(entries)
            feed.save_metadata()
            raise # exit the loop


def retry_download(folder, feedname, low=0):
    """ 
        Retries download on all local entries 
        whose content couldn't be downloaded,
        given the feed name and an optional low index
        that states from which entry we'd like to start
        (to avoid unnecessary retries)
    """

    with open(os.path.join(folder, feedname, 'metadata.json')) as f:
        j = json.loads(f.read())
        feed = Feed(folder, j['name'])

    all_entries = feed.get_entries(low)
    updated = []

    try:
        for entry in all_entries:
            if not entry.downloaded:
                entry.load_content()
                updated.append(entry)

                try:
                    time.sleep(0.5)
                except AttributeError:
                    time.wait(0.5)
        
        feed.save_entries(updated)
        # Same as above
        feed.save_metadata()

    except:
        # Save what was processed
        feed.save_entries(updated)
        feed.save_metadata()
        raise # exit the loop