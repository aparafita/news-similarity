# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

__version__ = "0.1.0"
__url__ = 'https://github.com/aparafita/news-similarity'

from .utils import lazyinit

from pymongo import MongoClient
mongo_client = lazyinit(MongoClient)()

from spacy.en import English
nlp = lazyinit(English)()

from .wikipedia import WikiData
wiki = WikiData()


def init(topic_folder, topic_filename, vocab_filename):
    """
        Call this function to start defining distances between objects.

        Starts nlp and initializes the topic_model used for answering What.
    """

    nlp.__doinit__() # initialize it

    from .breakable_entry import BreakableEntry, TopicModel

    BreakableEntry._topic_model = TopicModel(
        topic_folder, topic_filename, vocab_filename
    )