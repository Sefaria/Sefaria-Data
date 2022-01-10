import django
django.setup()
from sefaria.model import *
import csv


with open('yalkut.csv') as fp:
    data = list(csv.DictReader(fp))
    chs = [int(row['Chapter']) for row in data]
    diffs = [chs[n+1] - chs[n] for n in range(len(chs)-1)]
    if any(n>1 for n in diffs):
        print('jumping')

    books = {row['Book']: [] for row in data}
    for row in data:
        books[row['Book']].append(row['ref'])

i = library.get_index('Yalkut Shimoni on Nach')
alts = i.alt_structs['Books']['nodes'][:]
for book in books:
    start, end = '', ''
    for ref in books[book]:
        if not start and ref:
            start = Ref(ref).all_segment_refs()[0].tref
        if ref:
            end = Ref(ref).all_segment_refs()[-1].tref.split()[-1]
    wholeref = f'{start}-{end}'
    for n in range(len(alts)):
        if book in [title['text'] for title in alts[n]['titles']]:
            if alts[n]['wholeRef'] != wholeref: print(alts[n]['wholeRef'], wholeref, book)
            alts[n]['wholeRef'] = wholeref
            alts[n]['refs'] = books[book]
print(i.alt_structs['Books']['nodes'] == alts)
'''i.alt_structs['Books']['nodes'] = alts
i.save()
library.refresh_index_record_in_cache(i)
'''