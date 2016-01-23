# -*- coding: utf-8-*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from newsparser.data import load_feeds

folder = '/Users/alvaro_parafita/Desktop/TFG/data'

feeds = load_feeds(folder)

for feed in feeds:
    e = feed.get_entries(low=-1, high=feed.num_entries)[0]
    print(feed.name, e.published)