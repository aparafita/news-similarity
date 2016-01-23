# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

class NYPost(FeedFilter):

    title_filter_patterns = {
        'exact': [],
        'lower': [
            'the day in photos',
            'daily blotter'
        ],
        'contains': [
            'we hear...'
        ],
        'regex': [],
        'funcs': []
    }

    tags_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [],
        'regex': [],
        'funcs': []
    }