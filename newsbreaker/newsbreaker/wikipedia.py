# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import time
import json

from collections import Counter
from functools import lru_cache

import wikipedia
import requests # to try-catch its Exception base class
import numpy as np

from pymongo import MongoClient

from . import nlp
from .utils import lazyinit
from .utils.decorators import try_again_dec


# Use try_again_dec with the main methods of wikipedia
for name in ['geosearch', 'languages', 'page', 'search', 'suggest', 'summary']:
    setattr(
        wikipedia, name,
        try_again_dec(
            wikipedia.exceptions.HTTPTimeoutError,
            wikipedia.exceptions.RedirectError,
            requests.exceptions.RequestException,
            retry=3
        )(getattr(wikipedia, name))
    )

# wikipedia configuration
wikipedia.set_lang('en')
wikipedia.set_rate_limiting(True)
wikipedia.set_user_agent(
    'Newsparser NE comparison (http://newsparser704.pythonanywhere.com/)'
)


class WikiData:
    
    pages = 'pages'
    ne_mapping = 'ne_mapping'

    nlp = nlp
    

    def __init__(self):
        self.mongo_client = MongoClient()
        self.db = self.mongo_client.wiki


    def __del__(self):
        self.mongo_client.close()
    
    
    def article(self, pageid=None, title=None):
        """ 
            Returns a specific article from Wikipedia, 
            given its pageid or its title.
            Downloads it if necessary
        """
        if pageid is None and title is None:
            raise Exception('Pageid and title can\'t be None at the same time')

        if pageid is None:
            d = self.db.articles.find_one({'title': title})

            if d is not None:
                return d # found it
        else:
            d = self.db.articles.find_one({'_id': pageid})

            if d is not None:
                return d # found it
            
        try:
            if not(pageid is None):
                page = wikipedia.page(pageid=pageid)
            else:
                page = wikipedia.page(title=title)

        except (
            wikipedia.exceptions.DisambiguationError,
            wikipedia.exceptions.PageError,
            wikipedia.exceptions.WikipediaException,
            requests.exceptions.RequestException,
            ValueError # error decoding JSON response
        ):
            return

        try:
            time.sleep(0.5)
        except:
            time.wait(0.5)

        # Even if we didn't find pageid or title, it still could be in the DB
        # since the title could have changed
        try:
            d = {
                '_id': int(page.pageid),
                'title': page.title,
                'content': page.content
            }
        except KeyboardInterrupt: # filter KeyboardInterrupt from here
            raise
        except Exception:
            return # can't add this entry

        self.db.articles.update_one(
            {'_id': d['_id']},
            {'$set': d},
            upsert=True
        )

        return d
        
        
    @lru_cache(maxsize=1000)
    def ne(self, ne):
        """ 
            Returns Wikipedia article ids related to the given ne, 
            downloading them if necessary
        """
        
        ne = ne.lower()
        d = self.db.nes.find_one({'_id': ne})

        if d is not None:
            return d # already processed
        
        # Not found -> download it
        
        try:
            search = wikipedia.search(ne)
        except wikipedia.exceptions.WikipediaException:
            search = []
            
        pages = []

        for title in search:
            found = False
            
            d = self.article(title=title)
            if d is None:
                continue

            pages.append(d['_id'])

        d = {'_id': ne, 'articles': pages}
        self.db.nes.insert_one(d)

        return d
    
    
    @lru_cache(maxsize=500)
    def article_vector(self, pageid):
        """
            Returns the NE vector for the article with the given pageid
        """
        
        d = self.article(pageid=pageid) # download it if necessary

        if d is None:
            return {}
        elif 'ne_vector' in d:
            return json.loads(d['ne_vector'])

        doc = self.nlp(d['content'], tag=True, parse=False, entity=True)

        counter = Counter( 
            ent.text.lower() 
            for ent in doc.ents 
            if ent.label_ in ('PERSON', 'ORG', 'FAC', 'GPE', 'LOC')
        )

        s = sum(v for v in counter.values()) # get the sum to build an histogram

        ne_vector = { k: v / s for k, v in counter.items() } if s else {}

        self.db.articles.update_one(
            {'_id': d['_id']},
            {'$set': { 'ne_vector': json.dumps(ne_vector) }},
            upsert=True
        )

        return ne_vector
        

    @lru_cache(maxsize=10000)
    def article_similarity(self, id1, id2):
        """
            Returns article similarity given two article ids.
        """
        
        v1 = self.article_vector(id1)
        v2 = self.article_vector(id2)
            
        words_in_common = set(v1).intersection(set(v2))

        v1 = np.array([v1[w] for w in words_in_common])
        v2 = np.array([v2[w] for w in words_in_common])
                
        return max(0, min(1, np.minimum(v1, v2).sum()))