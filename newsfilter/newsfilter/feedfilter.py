# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import re
import os.path

from collections import Counter

import pandas as pd
import numpy as np
from sklearn.externals import joblib

from pymongo import MongoClient
from spacy.en import English


class PoliticsModel:

    def __init__(self, folder):
        with open(os.path.join(folder, 'politics_model', 'words.txt')) as f:
            self.WORDS = f.read().split('\n')

        self.clf = joblib.load(
            os.path.join(folder, 'politics_model', 'politics_model.pkl')
        )

        self.nlp = English()


    def build_features(self, entry):
        doc = self.nlp(entry.content, tag=False, parse=False, entity=False)
    
        counter = Counter(
            w.lower_
            for w in doc
            if w.is_alpha
        )
        
        return np.array([counter.get(w, 0) for w in self.WORDS])


class FeedFilter:

    _db = None
    _politics_model = None


    def __init__(self, folder):
        self.folder = folder

        self.title_filter_patterns['regex'] = [
            re.compile(s, flags=re.IGNORECASE) if type(s) == str else s
            for s in self.title_filter_patterns.get('regex', [])
        ]

        self.paragraphs_filter_patterns['regex'] = [
            re.compile(s, flags=re.IGNORECASE) if type(s) == str else s
            for s in self.paragraphs_filter_patterns.get('regex', [])
        ]

        self.paragraphs_filter_patterns['regex_group'] = [
            (
                re.compile(s, flags=re.IGNORECASE) if type(s) == str else s, 
                groupname
            )

            for s, groupname in self.paragraphs_filter_patterns.get(
                'regex_group', []
            )
        ]


    @property
    def db(self):
        if self.__class__._db is None:
            self.__class__._db = MongoClient().entries

        return self._db


    @property
    def politics_model(self):
        if self.__class__._politics_model is None:
            self.__class__._politics_model = PoliticsModel(self.folder)

        return self._politics_model


    def downloaded(self, entry):
        return bool(entry.downloaded)


    def date_filter(self, entry):
        try:
            date = pd.to_datetime(entry.published).strftime('%Y-%m-%d')
        except:
            date = None
            
        entry.data['date'] = date
            
        return bool(date)


    def check_pattern(self, x, patterns):
        """ Returns True if x fulfills any of the patterns in dict patterns """

        for y in patterns.get('exact', []):
            if y == x: return True

        lower = x.lower()
        for y in patterns.get('lower', []):
            if y == lower: return True

        for y in patterns.get('contains', []):
            if y in lower: return True

        for regex in patterns.get('regex', []):
            if regex.fullmatch(x): return True

        for func in patterns.get('funcs', []):
            if func(x): return True

        return False


    # When inheriting from this class, 
    # fill these values to filter titles
    title_filter_patterns = {
        'exact': [], # exact match
        'lower': [], # lower matches
        'contains': [], # title contains x
        'regex': [], # regex fullmatches x, with IGNORECASE
        'funcs': [] # func returns True given input title
    }

    def title_filter(self, entry): 
        t = (entry.title or '').strip()
        if not t:
            return False # entry to be removed

        return not self.check_pattern(t, self.title_filter_patterns)


    # When inheriting from this class, 
    # fill these values to filter tags
    tags_filter_patterns = {
        'exact': [], # exact match
        'lower': [], # lower matches
        'contains': [], # title contains x
        'regex': [], # regex fullmatches x, with IGNORECASE
        'funcs': [] # func returns True given input tag
    }

    def tags_filter(self, entry):
        tags = [(t or '').strip() for t in entry.tags]
        if not tags:
            return True # don't filter entries without tags

        return not any(
            self.check_pattern(t, self.tags_filter_patterns)
            for t in tags
        )


    def tags_filter(self, entry):
        tags = [(t or '').strip() for t in entry.tags]
        if not tags:
            return True # don't filter entries without tags

        return not any(
            self.check_pattern(t, self.tags_filter_patterns)
            for t in tags
        )


    def politics_filter(self, entry):
        """ 
            Creates variable entry.data['politics'] as a boolean
            retrieven from politics_model, but this filter returns True
            always, to avoid filtering entries by politics (we only want
            to create this value in data, not filter entries based on that) 
        """

        entry.data['politics'] = bool(
            self.politics_model.clf.predict(
                self.politics_model.build_features(entry)
            )[0]
        )

        return True # return True to avoid filtering by politics


    paragraphs_filter_patterns = {
        'exact': [], # exact match
        'lower': [ # the following values try to filter newspaper media-substitution
            'photo', 'enlarge', 'video'
            'digitalglobe via google earth',
            'digital globe via google earth'
        ], # lower matches
        'contains': [], # title contains x
        'regex': [
            r'(Photo )?Advertisement ?(Continue reading the main story)?'
        ], # regex fullmatches x, with IGNORECASE
        'regex_group': [
            (
                r'\[Graphic: (?P<graphic_description>.*?)\]',
                'graphic_description'
            )
        ], # regex fullmatches x, with IGNORECASE, but only extracts group
        'funcs': [] # func returns True given input tag
    }


    def paragraphs_filter(self, entry):
        """ Returns True if entry still has text after all pattern filtering """

        paragraphs = [
            p 
            for p in map(
                lambda p: p.strip(),
                entry.content.split('\n')
            ) 
            if p
        ]

        filtered_paragraphs = []

        for p in paragraphs:
            if p in self.paragraphs_filter_patterns.get('exact', []):
                continue

            lower = p.lower()

            if lower in self.paragraphs_filter_patterns.get('lower', []):
                continue

            if any(
                x in lower 
                for x in self.paragraphs_filter_patterns.get('contains', [])
            ):
                continue

            if any(
                bool(regex.fullmatch(p)) 
                for regex in self.paragraphs_filter_patterns.get('regex', [])
            ):
                continue

            for regex, groupname in self.paragraphs_filter_patterns.get(
                'regex_group', []
            ):
                g = regex.fullmatch(p)
                if g:
                    p = g.group(groupname)
                    break

            filtered_paragraphs.append(p)

        entry.content = '\n'.join(filtered_paragraphs)
        
        return len(filtered_paragraphs) >= 2


    precontent_filters = [downloaded, date_filter, title_filter, tags_filter]
    content_filters = [politics_filter, paragraphs_filter]


    def filter_entry(self, entry):
        def filter_iter(entry, filters, flags): 
            for f, fname in map(lambda f: (f, f.__name__), filters):
                if fname not in flags:
                    flags[fname] = f(self, entry)

                if not flags[fname]:
                    # Didn't pass a previous filter, so don't continue
                    return False

            return True

        entry.data['filter'] = entry.data.get('filter', {})
        flags = entry.data['filter'].get('step_flags', {})
        entry.data['filter']['step_flags'] = flags

        ok = filter_iter(entry, self.precontent_filters, flags)
        
        if ok and not all(f.__name__ in flags for f in self.content_filters):
            entry.load_content() # make sure content is loaded
            ok = filter_iter(entry, self.content_filters, flags)

            if ok:
                # Entry content may have changed; we have to store it in db
                self.db[entry.feedname].update_one(
                    {'index': entry.index},
                    {
                        '$set': {
                            'filtered_content': entry.content
                        }
                    },
                    upsert=True
                )
        else:
            ok = ok and all(
                flags.get(f.__name__, False)
                for f in self.content_filters
            )

        entry.data['filter']['discarded'] = not ok # if True, discard it

        return ok