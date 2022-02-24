import re
import os
import django
django.setup()
from sefaria.model import *
from sefaria.helper.normalization import RegexNormalizer, NormalizerComposer

failed = []
for file in os.listdir('txt'):
    print(file)
    mas, ch = re.findall('(.*?) (.?.) פירוש', file)[0]
    mas = mas.replace('תעניות', 'תענית')
    with open(f'txt/{file}', encoding='utf-8') as fp:
        data = fp.read()
    for t in re.findall('([\s\S]{,250})#####', data):
        text = [re.escape(word) for word in t.split()]
        text = '(?: |<br>)*'.join(text[-25:])
        text = text.replace('\-', '[\-–]')
        segs = []
        for ref in Ref(f'אור לישרים על תלמוד ירושלמי {mas} {ch}').all_segment_refs():
            rtext = ' '.join(re.sub('<[^>]+>', '', ref.text('he').text).split())
            if re.search(text, rtext):
                segs.append(ref)
        if len(segs) != 1:
            failed.append(f'{mas} {ch}\n{t}\n{len(segs)}')
            continue
        if len(segs[0].version_list()) > 1: print('many versions')
        vtitle = segs[0].version_list()[0]['versionTitle']
        tc = segs[0].text('he', vtitle=vtitle)
        tct = tc.text
        html_nor = RegexNormalizer('<[^>]*>', '')
        spaces_nor = RegexNormalizer('\s+', ' ')
        nor = NormalizerComposer(steps=[html_nor, spaces_nor])
        tct_nor = nor.normalize(tct)
        to_find = re.findall(text, tct_nor)
        # if len(to_find) != 1:
        #     print('finding in the ref', len(to_find))
        #     print(text, tct_nor)
        to_find = to_find[-1] #ad hoc - in the one place it has more than one it's the last
        start = tct_nor.find(to_find, 2)
        if start < 0:
            start = tct_nor.find(to_find)
            if start < 0:
                print('didnt find')
                print(1, tct_nor)
                print(2, to_find)
        norm_range = (start, start + len(to_find))
        mapping = nor.get_mapping_after_normalization(tct)
        orig_range = nor.convert_normalized_indices_to_unnormalized_indices([norm_range], mapping)[0]

        a, b = tct[:orig_range[1]].strip(), tct[orig_range[1]:].strip()
        while not a.endswith('<br>') and re.search('<[^/>]*>$', a):
            b = re.search('<[^/>]*>$', a).group() + b
            a = re.sub('<[^/>]*>$', '', a)
        while re.search('^</[^>]*>', b):
            a += re.search('^</[^>]*>', b).group()
            b = re.sub('^</[^>]*>', '', b)
        if a.endswith('<br>'):
            new = f'{a}• • •<br>{b}'
        elif b.startswith('<br>') or not b:
            new = f'{a}<br>• • •{b}'
        else:
            new = f'{a}<br>• • •<br>{b}'

        tc.text = new
        # tc.save(force_save=True)


with open('failed.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(failed))
