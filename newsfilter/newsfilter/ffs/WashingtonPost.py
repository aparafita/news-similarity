# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from . import FeedFilter

class WashingtonPost(FeedFilter):

    title_filter_patterns = {
        'exact': [],
        'lower': [],
        'contains': [],
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