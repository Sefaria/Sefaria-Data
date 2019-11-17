# -*- coding: utf-8 -*-

import django
django.setup()
import unicodecsv as csv
from sefaria.system.database import db
from sefaria.model import *


from collections import Counter
counts = Counter()
for tractate in library.get_indexes_in_category("Bavli"):
    counts.update(TextChunk(Ref(tractate), 'he').ja().flatten_to_string().split())
most_common = counts.most_common(1000)
most_common_with_lex = []
for word in most_common:
    lex_lookup = LexiconLookupAggregator.lexicon_lookup(word[0])
    if lex_lookup:
        lex_lookup = [x.contents() for x in lex_lookup if not isinstance(x, StrongsDictionaryEntry)]
        for i, lookup in enumerate(lex_lookup):
            csv_row = {
                "Common Word" : word[0] if i == 0 else "", # only list the orig word at the top of a nested list of matched entries
                "Headword" : lookup["headword"],
                "Lexicon" : lookup["parent_lexicon"],
                "URL" : u"https://www.sefaria.org/{}, {}".format(lookup["parent_lexicon_details"]["index_title"], lookup["headword"]) if "index_title" in lookup["parent_lexicon_details"] else ""
            }
            most_common_with_lex.append(csv_row)

    else:
        csv_row = {
            "Common Word" : word[0],  # only list the orig word at the top of a nested list of matched entries
            "Headword" : "",
            "Lexicon" : "",
            "URL" : u""
        } # no definitions ?
        most_common_with_lex.append(csv_row)


with open("/tmp/most_common_words_and_lexicon_entries.csv", "wb") as fout:
    writer = csv.DictWriter(fout, [u"Common Word", u"Headword", u"Lexicon", u"URL"])
    writer.writeheader()
    writer.writerows(most_common_with_lex)

