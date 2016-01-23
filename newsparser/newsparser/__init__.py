# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

__version__ = "0.1.0"
__url__ = 'https://github.com/aparafita/news-similarity'

logging_file = 'feed_retrieval.log'

from .feed import Feed
from .entry import Entry

import logging
# logging.basicConfig(
#     filename=logging_file, 
#     format='%(asctime)s: %(message)s', 
#     level=logging.INFO
# )