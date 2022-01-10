import json
import django
django.setup()
from sefaria.model import *
import re
from data_utilities.text_align import CompareBreaks
from sources.functions import post_link

mapping = {}
links = []
for ind in library.get_indexes_in_category('Yerushalmi'):
    if ind == 'Jerusalem Talmud Shekalim':
        continue

    print(ind)
    for ch in Ref(ind).all_subrefs():
        y_mish = [r.all_subrefs()[0].text('he', 'Mechon-Mamre').text if r.all_subrefs() else '' for r in ch.all_subrefs()]
        y_mish = [re.sub('[^א-ת ]', '', t) for t in y_mish]
        mishna_tref =  re.sub('Jerusalem Talmud|JTmock', 'Mishnah', ch.normal())
        m_mish = [re.sub('[^א-ת ]', '', t) for t in Ref(mishna_tref).text('he').text]
        cb = CompareBreaks(y_mish, m_mish)
        for key, value in cb.create_mapping().items():
            tref_y = f'{ch.normal()}:{key}:1'
            tref_m = Ref(f'{mishna_tref} {min(value)}-{max(value)}').normal()
            if not Ref(tref_y).text('he').text:
                continue
            mapping[tref_y] = tref_m
            links.append({'refs': [tref_y, tref_m],
                         'type': 'Related Passage',
                          'auto': True,
                          'generated_by': 'yerushalmi-mishnah linker'})

post_link(links, server='http://localhost:9000', skip_lang_check=False, VERBOSE=False)
json.dump(mapping, open('mishanh_mappings.json', 'w'))
