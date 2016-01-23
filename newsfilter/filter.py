# -*- coding: utf-8-*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import pandas as pd

from newsparser.data import load_feeds
from newsfilter.general_filter import GeneralFilter

folder = '/Users/alvaro_parafita/Desktop/TFG/data'

gf = GeneralFilter(folder)
gf.filter_entries()

# Display statistics
feeds = load_feeds(folder)
entries = { feed: feed.get_entries() for feed in feeds }

df = pd.DataFrame(
    [
        [
            feed.name, 
            len(entries[feed]),
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
        'filtered'
    ]
)

df = df.append(
    {
        'feed': 'Total', 
        '# entries': df['# entries'].sum(),
        'filtered': df['filtered'].sum()
    }, 
    ignore_index=True
)

df['ratio'] = df['filtered'] / df['# entries']

print(df)