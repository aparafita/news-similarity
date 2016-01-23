# -*- coding: utf-8-*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import pandas as pd

from newsparser.data import load_feeds

folder = '/Users/alvaro_parafita/Desktop/TFG/data'

# Display statistics
feeds = load_feeds(folder)
entries = { feed: feed.get_entries() for feed in feeds }

df = pd.DataFrame(
    [
        [
            feed.name, 
            len(entries[feed]),
            sum(
                not entry.data.get('filter', {}).get('discarded', True)
                for entry in entries[feed]
            ),
            sum(
                not entry.data.get('filter', {}).get('duplicate', True)
                for entry in entries[feed]
            ),
            sum(
                not entry.data.get('filter', {}).get('news_agency_discarded', True)
                for entry in entries[feed]
            ),
            sum(
                entry.data.get('newsbreaker', False)
                for entry in entries[feed]
            )
        ]
        for feed in feeds
    ],
    columns=[
        'feed', 
        '# entries', 
        'discarded',
        'duplicate',
        'news_agency_discarded',
        'newsbreaker'
    ]
)

df = df.append(
    {
        'feed': 'Total', 
        '# entries': df['# entries'].sum(),
        'discarded': df['discarded'].sum(), 
        'duplicate': df['duplicate'].sum(), 
        'news_agency_discarded': df['news_agency_discarded'].sum(),
        'newsbreaker': df['newsbreaker'].sum(), 
    }, 
    ignore_index=True
)

df['discarded'] = df['discarded'] * 100 / df['# entries']
df['duplicate'] = df['duplicate'] * 100 / df['# entries']
df['news_agency_discarded'] = df['news_agency_discarded'] * 100 / df['# entries']
df['newsbreaker'] = df['newsbreaker'] * 100 / df['# entries']

print(df)