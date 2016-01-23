# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from functools import lru_cache
from ..feedfilter import FeedFilter
from . import *

@lru_cache(maxsize=None)
def ff(feedname, folder):
    from importlib import import_module as imp

    return getattr(imp('.' + feedname, __package__), feedname)(folder)