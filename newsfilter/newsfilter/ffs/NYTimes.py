# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

class NYTimes(FeedFilter):

    title_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [],
        'regex': [
            'your [a-z]+ briefing'
        ],
        'funcs': []
    }

    tags_filter_patterns = {
        'exact': [],
        'lower': [
            'restaurants'
        ],
        'contains': [],
        'regex': [],
        'funcs': []
    }