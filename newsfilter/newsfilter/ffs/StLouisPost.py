# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

class StLouisPost(FeedFilter):

    title_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [
            'things to know for',
            'today in ',
            'AP NewsAlert'
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