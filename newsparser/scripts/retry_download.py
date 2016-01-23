# -*- coding: utf-8-*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import pandas as pd

from newsparser.updater import retry_download
from newsparser.data import load_feeds

folder = '/Users/alvaro_parafita/Desktop/TFG/data'

feeds = load_feeds(folder)

# Update local files
try:
    for feed in feeds:
        print(feed.name)
        retry_download(folder, feed.name, low=0)
except KeyboardInterrupt:
    # Don't load anything else for the moment
    pass

df = pd.DataFrame(
    [
        [
            feed.name, 
            feed.num_entries, 
            sum(e.downloaded for e in feed.get_entries())
        ]
        for feed in feeds
    ],
    columns=['feed', '# entries', '# entries downloaded']
)

df['ratio'] = df['# entries downloaded'] / df['# entries']

df = df.append(
    {
        'feed': 'Total', 
        '# entries': df['# entries'].sum(),
        '# entries downloaded': df['# entries downloaded'].sum(),
        'ratio': df['# entries downloaded'].sum() / df['# entries'].sum()
    }, 
    ignore_index=True
)

print(df)
