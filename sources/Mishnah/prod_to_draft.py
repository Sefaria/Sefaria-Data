# -*- coding: utf-8 -*-

from sefaria.model import *
from sources import functions

# grab category
books = library.get_indexes_in_category('Mishnah')

for book in books:
    print book
    # grab English versions
    r = Ref(book)
    versions = [v for v in r.version_list() if v['language'] == u'en']

    for version in versions:
        t = TextChunk(r, version['language'], version['versionTitle'])
        version['text'] = t.ja().array()
        functions.post_text(book, version)
