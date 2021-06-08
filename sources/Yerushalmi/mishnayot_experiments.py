# encoding-utf-8

import json
from itertools import zip_longest
import data_utilities.text_align as align
from diff_match_patch import diff_match_patch
from sefaria.utils.hebrew import strip_nikkud


with open('./code_output/mishnayot.json') as fp:
    mishnayot = json.load(fp)

shabbat = mishnayot['Jerusalem Talmud Shabbat']
gugg1, mehon1 = shabbat[0]['gugg-mishnayot'], shabbat[0]['mehon-mishnayot']

for g, m in zip_longest(gugg1, mehon1, fillvalue='-'):
    print(strip_nikkud(g), m, sep='\n\n', end='\n---\n')
# gugg1 = strip_nikkud(' '.join(gugg1))
# mehon1 = ' '.join(mehon1)
#
# matching = diff_match_patch().diff_main(gugg1, mehon1)
# print(gugg1, mehon1, sep='\n\n')

# cb = align.CompareBreaks(gugg1, mehon1)
# with_markers = cb.insert_break_marks()

# print(with_markers)
result = []
# print((shabbat[0]))
# print(*shabbat[0].keys(), sep='\n')
