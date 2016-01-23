# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

class USAToday(FeedFilter):

    title_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [
            'things you need to know',
            'on campus, '
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