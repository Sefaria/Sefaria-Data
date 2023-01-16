import json
import django
django.setup()
import re
from rif_utils import tags_map, path
from tags_fix_and_check import tags_by_criteria, gem_to_num, save_tags
from sefaria.utils.talmud import section_to_daf
from parsing_utilities.util import getGematria
from sefaria.model import *

import csv
REPORT = []
COUNT = 0
COUNTB = 0

def gemara_rif(rif_ref):
    rif_links = Ref(rif_ref).linkset()
    return [link.refs[1] for link in rif_links if link.generated_by=='rif gemara matcher']

def gemara_halakha_links(gemara_refs, em_ref):
    refs = []
    halakha_refs = []
    for ref in gemara_refs:
        section_links = Ref(ref).linkset()
        section_links = [link for link in section_links if link.type=='ein mishpat / ner mitsvah']
        halakha_refs += section_links
    halakha_refs = [link.refs[1] for link in halakha_refs]
    for ref in halakha_refs:
        if em_ref in ref:
            refs.append(ref)
    return refs

def precise_ref(em_ref, rif_ref):
    if 'Mishneh Torah' not in em_ref:
        em_ref = em_ref.replace('Tur', 'Shulchan Arukh')
    gemara_refs = gemara_rif(rif_ref)
    #if not gemara_refs:
    sec = int(rif_ref.split(':')[1])
    prev, next = Ref(rif_ref).prev_segment_ref(), Ref(rif_ref).next_segment_ref()
    if prev: gemara_refs += gemara_rif(prev.tref)
    if next: gemara_refs += gemara_rif(next.tref)

    refs = gemara_halakha_links(gemara_refs, em_ref)
    if not refs:
        for ref in gemara_refs:
            prev, next = Ref(ref).prev_segment_ref(), Ref(ref).next_segment_ref()
            if prev: refs += gemara_halakha_links([prev.tref], em_ref)
            if next: refs += gemara_halakha_links([next.tref], em_ref)

    #report
    global COUNT,COUNTB,REPORT
    if 'Mishneh Torah' in em_ref and refs:
        COUNT += 1
        if COUNT < 1000:
            REPORT.append({'rif ref': rif_ref,
             'rif text': Ref(rif_ref).text('he').text,
             'rambam refs': list(set(refs)),
             'rambam texts': [Ref(ref).text('he').text for ref in list(set(refs))]})
    if 'Mishneh Torah' in em_ref and not refs:
        COUNTB += 1
        if COUNTB < 10:
            REPORT.append({'rif ref': rif_ref,
             'rif text': Ref(rif_ref).text('he').text,
             'rambam refs': em_ref,
             'rambam texts': 'not found'})
    return list(set(refs))

for masechet in tags_map:
    if masechet == 'Nedarim': continue
    print(masechet)
    links = []
    with open(path+'/tags/topost/rif_{}.json'.format(masechet)) as fp:
        data = json.load(fp)
    with open(path+'/commentaries/json/EM_{}.json'.format(masechet)) as fp:
        em = json.load(fp)
    for page in range(len(data)):
        tags = tags_by_criteria(masechet, key=lambda x: int(x[1:4])==page, value=lambda x: x['referred text']==6)
        for tag in tags:
            section = int(tag[4:6])
            label = re.sub(r'[^א-ת]', '', tags[tag]['original'])
            letter = gem_to_num(getGematria(label))
            if tag not in data[page][section]:
                print(f'dont find tag {tag}')
                continue

            rif_ref = f'Rif {masechet} {section_to_daf(page+1)}:{section+1}'
            emobj = em[page][letter-1]
            titles = set()
            refs = [r for r in emobj['Semag'] if r] + [r for r in emobj['Tur Shulchan Arukh'] if r]
            for ref in [r for r in emobj['Rambam'] if r] + [r for r in emobj['Tur Shulchan Arukh'] if r]:
                refs += precise_ref(ref, rif_ref)

            for ref in refs:
                if 'Sefer Mitzvot Gadol' in ref or 'Tur' in ref:
                    title = ref.split(',')[0]
                else:
                    title = ' '.join(ref.split()[:-1])
                titles.add(title)
                link = ({'refs': [rif_ref, ref],
                'type': 'ein mishpat',
                'inline_reference': {'data-commentator': title, 'data-label': "⚬"},
                'generated_by': 'rif ein mishpat'})
                if link not in links: links.append(link) #two letters in same segment can cause double link

            inline = ''.join([f'<i data-commentator="{title}" data-label="⚬"></i>' for title in titles])
            data[page][section] = re.sub(f'\${tag} *', inline, data[page][section])
            tags[tag]['used'] = True
        save_tags(tags, masechet)

    with open(path+'/tags/topost/rif_{}.json'.format(masechet), 'w') as fp:
        json.dump(data, fp)
    with open(path+'/tags/topost/em_links_{}.json'.format(masechet), 'w') as fp:
        json.dump(list(links), fp)

with open('emreport.csv', 'w', encoding='utf-8', newline='') as fp:
    awriter = csv.DictWriter(fp, fieldnames=['rif ref', 'rif text', 'rambam refs', 'rambam texts'])
    awriter.writeheader()
    for item in REPORT: awriter.writerow(item)
print(COUNT, COUNTB)
