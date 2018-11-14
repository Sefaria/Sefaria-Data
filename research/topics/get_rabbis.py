# -*- coding: utf-8 -*-
import re
import django
import codecs
import json
import unicodecsv
import pygtrie
from collections import defaultdict
django.setup()
from sefaria.model import *

maxrabbilen = 0
with open("RabbisNames.csv", 'rb') as fin:
    tonorabbiscsv = unicodecsv.DictReader(fin)
    tonorabbis = pygtrie.Trie()
    for row in tonorabbiscsv:
        rabbiName = u""
        for i in range(1,11):
            tempName = row[u"Name{}".format(i)]
            if not tempName:
                break
            if i > 1:
                rabbiName += u" "
            rabbiName += tempName
        rabbiName = rabbiName.replace(u"ר'", u"רבי")
        if len(rabbiName) > maxrabbilen:
            maxrabbilen = len(rabbiName)
        tonorabbis[rabbiName] = 0

    pass

def get_rabbis_in_category(cat):


    for ind in library.get_indexes_in_category(cat):
        r = Ref(ind)
        vtitle = None
        if cat == 'Bavli':
            willy = u'William Davidson Edition - Aramaic'
            has_willy = len(filter(lambda v: v['versionTitle'] == willy, r.version_list())) > 0
            if not has_willy:
                print 'Skipping {}'.format(ind)
            vtitle = willy
        tc = TextChunk(Ref(ind), 'he', vtitle=vtitle)
        flat = tc.ja().flatten_to_array()
        for segment in flat:
            start = 0
            while start < len(segment):
                end = start + maxrabbilen - 1
                while end >= start:
                    temp = segment[start:end + 1]
                    has_node = tonorabbis.has_node(temp)
                    if has_node == pygtrie.Trie.HAS_VALUE:
                        tonorabbis[temp] += 1
                        print u'found {}'.format(temp)
                        start = end
                        break
                    elif has_node == pygtrie.Trie.HAS_SUBTRIE:
                        end -= 1
                    else:
                        break
                start += 1



get_rabbis_in_category('Bavli')