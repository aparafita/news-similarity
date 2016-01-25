# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

# Loads ne_vector of every article in the database

from newsbreaker import wiki

if __name__ == '__main__':
    total_articles = wiki.db.articles.find().count()
    articles = [
        x['_id'] 

        for x in wiki.db.articles.find(
            { 'ne_vector': { '$exists': False } }, 
            { '_id': True }
        )
    ]

    processed = total_articles - len(articles)
    for n, pageid in enumerate(articles):
        wiki.article_vector(pageid)

        if not ((processed + n + 1) % 100):
            print(
                processed + n + 1,
                total_articles - (processed + n + 1), 
                (processed + n + 1) / total_articles
            )