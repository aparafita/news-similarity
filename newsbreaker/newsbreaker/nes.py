# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

from collections import defaultdict
from functools import lru_cache

import numpy as np
import pandas as pd

from . import wiki


class NE(object):
    
    ne_distance_threshold = 0.5
    similarity_decreasing_ratio = 0.9
    mu = 0.023143740437546346
    sigma = 0.03160862980242218

    wiki = wiki
    
    
    def __init__(self, ne):            
        self.ne = ne.lower()
        self.articles = self.wiki.ne(self.ne)['articles']
    
    
    @lru_cache(maxsize=1000)
    def similarity(self, other):
        # Create a list of all pairs to check between the two NEs 
        # ordering by index1 + index2 ascending
        pairs = sorted(
            [
                (i, j) 
                for i in range(len(self.articles))
                for j in range(len(other.articles))
            ],
            key=lambda pair: sum(pair),
            reverse=False
        )
        
        # Create sublists based on levels
        pairs2 = defaultdict(list)
        for i, j in pairs:
            pairs2[i + j].append([i, j])
            
        pairs = [
            [ pair for pair in level ]
            for _, level in sorted(pairs2.items(), key=lambda t: t[0])
        ]
        
        # Process each level; if we pass the threshold, we stop there
        for level in pairs:
            sims = []
            for i, j in level:
                a1 = self.articles[i]
                a2 = other.articles[j]

                sim = max(0., min(1., 
                    (self.wiki.article_similarity(a1, a2) - self.mu) / \
                        (self.sigma / 0.1) + 0.5
                ))

                if sim >= self.ne_distance_threshold:
                    # Got the nearest-to-top pair; end here
                    sim *= (self.similarity_decreasing_ratio ** (i + j))
                    sims.append(sim)
            
            if sims: # surpassed the threshold on this level; stop here
                sim = max(sims)
                break
        else:
            sim = 0
        
        return sim


    @staticmethod
    def matrix(nes):
        """
            Given a iterable of Named Entities,
            it returns a np.ndarray matrix with the distances of all NEs passed 
            and a list of those NEs ordered and lowered, without repetitions.
        """
        
        nes = [ 
            NE(ne) 
            for ne in sorted({ne.lower() for ne in nes})
        ]
                        
        matrix = np.array(
            [
                [ 
                    (1. - ne1.similarity(ne2)) \
                    if i < j else 0.
                    
                    for j, ne2 in enumerate(nes)
                ]
                
                for i, ne1 in enumerate(nes)
            ]
        )
        
        matrix = matrix + matrix.T # make it simetric
        
        return matrix, [str(ne) for ne in nes]
    
    
    def __str__(self): return self.ne.title()
    def __hash__(self): return hash(self.ne)
    
    def __lt__(self, other): return self.ne <= other.ne
    def __le__(self, other): return self.ne < other.ne
    def __eq__(self, other): return self.ne == other.ne
    def __ne__(self, other): return self.ne != other.ne
    def __gt__(self, other): return self.ne >= other.ne
    def __ge__(self, other): return self.ne > other.ne