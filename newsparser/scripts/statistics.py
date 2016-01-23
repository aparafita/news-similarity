# -*- coding: utf-8-*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)

import pandas as pd

from newsparser.data import load_feeds

folder = '/Users/alvaro_parafita/Desktop/TFG/data'

# Display statistics
feeds = load_feeds(folder)

df = pd.DataFrame(
    [
        [feed.name, feed.num_entries]
        for feed in feeds
    ],
    columns=['feed', '# entries']
)

df = df.append(
    {
        'feed': 'Total', 
        '# entries': df['# entries'].sum()
    }, 
    ignore_index=True
)

print(df)