# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

class BostonHerald(FeedFilter):

    title_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [
            'tv watch',
            'the ticker'
        ],
        'regex': [
            '(monday|tuesday|wednesday|thursday|friday|saturday|sunday)( night)?'
        ],
        'funcs': []
    }

    tags_filter_patterns = {
        'exact': [],
        'lower': [
            'obituaries',
            'food & recipes',
            'calendar',
            'jobfind',
            'horoscope'
        ],
        'contains': [],
        'regex': [],
        'funcs': []
    }