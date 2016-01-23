# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import json
import os.path

from . import Feed


def load_feeds(folder):
    """ Loads all Feed instances retrivable from feeds.json """

    with open(os.path.join(folder, 'feeds.json')) as f:
        return [Feed(folder, j['name']) for j in json.loads(f.read())]