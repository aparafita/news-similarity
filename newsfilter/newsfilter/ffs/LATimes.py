# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

import pandas as pd


def try_to_datetime(title):
    try:
        pd.to_datetime(title)
        return True
    except ValueError:
        return False


class LATimes(FeedFilter):


    title_filter_patterns = {
        'exact': [],
        'lower': [
            'for the record'
        ],
        'contains': [],
        'regex': [],
        'funcs': [
            try_to_datetime
        ]
    }

    tags_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [],
        'regex': [],
        'funcs': []
    }


del try_to_datetime