# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import os.path

from collections import Counter, defaultdict

import numpy as np

from sklearn.externals import joblib
from pyemd import emd

import newsparser

from . import nlp
from .nes import NE


class TopicModel(object):

    def __init__(self, folder, model_filename, vocab_filename):
        self.model = joblib.load(os.path.join(folder, model_filename))

        with open(os.path.join(folder, vocab_filename)) as f:
            self.vocab = f.read().split('\n')


class NLPDoc(object):

    def __init__(self, entry, nlp=nlp):
        self._nlp = nlp
        self._entry = entry
        self._nlp_docs = {}
        self._nlp_selected_doc = None


    def __call__(self, tag=True, parse=True, entity=True):
        for (t, p, e), doc in self._nlp_docs.items():
            if  (t >= tag) and \
                (p >= parse) and \
                (e >= entity):

                self._nlp_selected_doc = doc
                return self

        else:
            doc = self._nlp(
                self._entry.content, 
                tag=tag, parse=parse, entity=entity
            )

            # Delete all docs with inferior category than this doc
            for (t, p, e), _ in list(self._nlp_docs.items()):
                if  (t <= tag) and \
                    (p <= parse) and \
                    (e <= entity):
                    del self._nlp_docs[(t, p, e)]

            # Save the current doc
            self._nlp_docs[(tag, parse, entity)] = doc

            # Select the current doc and return
            self._nlp_selected_doc = doc
            return self


    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            pass

        return self.__getattr_from_doc__(name)


    def __getattr_from_doc__(self, name):
        if self._nlp_selected_doc is None:
            raise Exception("Doc not initialized; looking for attr '%s'" % name)
        else:
            return getattr(self._nlp_selected_doc, name)


    # The following methods ensure that some doc functions
    # are available directly from self, because __getattribute__ 
    # won't be called on them

    def __iter__(self):
        return self.__getattr_from_doc__('__iter__')()


    def __getitem__(self, key):
        return self.__getattr_from_doc__('__getitem__')(key)


    def __len__(self):
        return self.__getattr_from_doc__('__len__')()


    def reset(self):
        self._nlp_docs = {}
        self._nlp_selected_doc = None


class BreakableEntry(newsparser.Entry):

    who_ne_cats = {'PERSON', 'ORG'}
    where_ne_cats = {'FAC', 'GPE', 'LOC'}
    max_nes = 10

    _topic_model = None

    CONTENT_KEY = 'filtered_content'


    def __init__(self, folder, feed, metadata, nlp=nlp):
        data = metadata['data']
        if 'newsbreaker' not in data or not data['newsbreaker']:
            raise ValueError(
                "Unfiltered or discarded entries "
                "cannot be converted to BreakableEntry"
            )

        super().__init__(folder, feed.name, metadata)

        self.feed = feed
        self.doc = NLPDoc(self, nlp)


    # Make content available from the moment it's referenced
    @property
    def content(self):
        if not hasattr(self, '_content') or self._content is None:
            for d in self.db[self.feedname].find({'index': self.index}):
                self.content = d[self.CONTENT_KEY]
                break
            else:
                raise Exception('Content not found in DB')

        return self._content


    @content.setter
    def content(self, value):
        self._content = value


    @property
    def topic_model(self):
        if self._topic_model is None:
            raise Exception('Topic model not initialized')
        else:
            return self._topic_model


    @topic_model.setter
    def topic_model(self, topic_model):
        self.__class__._topic_model = topic_model

    
    @property
    def what(self):
        if hasattr(self, '_what'):
            return self._what
        
        self.doc(tag=False, parse=False, entity=False)

        counter = Counter(
            word.lower_
            for word in self.doc
        )

        self._what = self.topic_model.model.transform(
            np.array([ counter[word] for word in self.topic_model.vocab ])
        )
        
        return self._what
        
        
    def what_distance(self, other):
        return 1. - np.minimum(self.what, other.what).sum()
    
    
    @property
    def scores(self):
        """
            Returns a list of tuples (i, j, score)
            where i, j signal the bounds of doc[i:j] 
            for a given sentence and score is that sentence score.
        """
        
        if hasattr(self, '_scores'):
            return self._scores
        
        doc = self.doc(tag=False, parse=False, entity=False)
        
        # Get TF-IDFs of all words in document
        counter = Counter( word.lower_ for word in doc )
        
        for word in counter:
            counter[word] *= -nlp.vocab[word].prob # * IDF
            
        s = sum(counter.values())
        
        for word in counter:
            counter[word] /= s
            
        # Get sentences scores
        self._scores = []
        for sent in doc.sents:
            score = sum(
                counter[word.lower_]
                for word in sent
            ) / len(sent)
            
            self._scores.append((sent.start, sent.end, score))
            
        return self._scores
    
    
    def ent_score(self, ent):
        s, e = ent.start, ent.end
        
        for start, end, score in self.scores:
            if start <= s and e <= end:
                return score
            
        assert False # shouldn't get here
    
    
    def _ws_ne_property(self, w):
        if hasattr(self, '_' + w):
            return getattr(self, '_' + w)
        
        self.doc(tag=True, parse=False, entity=True)
        
        counter = Counter()
        
        for ent in self.doc.ents:
            if ent.label_ in getattr(self, w + '_ne_cats'):
                ent_text = ent.text.lower()
                score = self.ent_score(ent)
                counter[ent_text] += score
        
        s = sum(counter.values())
        counter2 = defaultdict(float)
        for k, v in counter.items():
            counter2[k] = (float(v) / s) if s else 0.
        
        setattr(self, '_' + w, counter2)
        return counter2
    

    @property
    def who(self): return self._ws_ne_property('who')
    
    @property
    def where(self): return self._ws_ne_property('where')
    
    
    def _wh_ne_distance(self, other, w):
        c1 = getattr(self, w)
        c2 = getattr(other, w)
        
        if not len(c1) or not len(c2):
            # one of them has nothing to compare; distance is np.nan
            return np.nan

        s1 = sorted(c1.keys(), key=lambda k: c1[k], reverse=True)
        s2 = sorted(c2.keys(), key=lambda k: c2[k], reverse=True)

        if self.max_nes > 0:
            penalty = max(
                sum(
                    c1[w] 
                    for w in s1[self.max_nes:]
                ), sum(
                    c2[w]
                    for w in s2[self.max_nes:]
                )
            )

            s1 = s1[:self.max_nes]
            s2 = s2[:self.max_nes]
        else:
            penalty = 0

        # penalty will make up for those documents that have low-scoring
        # NEs, meaning they should not be compared with other news items
        # since this method would not have meaning with them

        matrix, nes = NE.matrix(set(s1).union(set(s2)))
        
        if not nes:
            # Not a single NE to compare; distance is np.nan
            return np.nan
        
        nes = [ne.lower() for ne in nes] # NE.matrix returns Titles
        v1 = np.array([ c1[ne] for ne in nes ])
        v2 = np.array([ c2[ne] for ne in nes ])

        # Make it sum 1
        s = v1.sum()
        if s > 0:
            v1 /= s

        s = v2.sum()
        if s > 0:
            v2 /= s

        # Now compute emd of the two vectors.
        # That distance is in [0, 1]
        # By multiplying per (1 - penalty) and adding penalty,
        # you ensure distance is in [penalty, 1],
        # penalty being the maximum uncertainty there is in each of the vectors.
        return (1 - penalty) * emd(v1, v2, matrix) + penalty
    
    
    def who_distance(self, other):
        return max(0., min(1., self._wh_ne_distance(other, 'who')))
    

    def where_distance(self, other):
        return max(0., min(1., self._wh_ne_distance(other, 'where')))
    
    
    def distance(self, other):
        return \
            0.3657526 * self.what_distance(other) + \
            0.3274783 * self.who_distance(other) + \
            0.3067691 * self.where_distance(other)
    

    def w_print(self, top=None):
        print('Who?\n' + '*' * 20)

        for k, v in sorted(
            self.who.items(), 
            key=lambda pair: pair[1], 
            reverse=True
        )[:top or len(self.who)]:
            print(k, v)
        
        print('\nWhere?\n' + '*' * 20)

        for k, v in sorted(
            self.where.items(), 
            key=lambda pair: pair[1], 
            reverse=True
        )[:top or len(self.where)]:
            print(k, v)