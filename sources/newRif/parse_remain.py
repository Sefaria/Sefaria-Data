import re
import django
django.setup()
import json
import copy
from data_utilities.util import getGematria
from sefaria.utils.talmud import daf_to_section, section_to_daf
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.model import *
from rif_utils import path
from more_talmud_refs import base_tokenizer

def find_dh(comm):
    comm = comm.split('<br>')[0]
    comm = re.sub('כתוב בהלכות רבינו הגדול ר"י אלפסי ז"ל|כתוב בהלכות|כתוב בהל\'|כו\'', '', comm)
    return ' '.join(comm.split()[:7])

def find_section(daf):
    try:
        return daf_to_section(daf) - 1
    except ValueError:
        return getGematria(daf) * 2 - 2 if '.' in daf else getGematria(daf) * 2 - 1

def parse_pages(data, title):
    if title == 'zk':
        old = 'ספר הזכות מסכת כתובות דף ([י-ס][א-ט]?) עמוד ([אב])\n\nספר הזכות מסכת כתובות דף [י-ס][א-ט]? עמוד [אב]'
        data = re.sub(old, r'@@\1@\2', data)
        data = re.sub('(@@..?)@א', r'\1.', data)
        data = re.sub('(@@..?)@ב', r'\1:', data)
    data = data.split('@@')[1:]
    newdata = [[] for _ in range (124)]
    for page in data:
        num, npage = page.split(None, 1)
        num = find_section(num)
        newdata[num].append(npage)
    return newdata

def parse_page(page, title):
    if page == []: return []
    if title == 'td':
        page = [p+':' for p in page.split(':')[:-1]]
    elif title == 'zg':
        page = re.sub(' ?@44', '<br>', page)
        page = page.split('@11')[1:]
    elif title == 'zy':
        page = page.replace('@11', '', 1)
        page = ['<br>'.join([p.strip() for p in page.split('@11')])]
    elif title == 'zk':
        if 'כתוב בהלכות לשבועה' in page:
            page = re.split('כתוב בהלכות לשבועה|כתוב בהלכות וכל זמן', page)
            page[1] = 'כתוב בהלכות לשבועה' + page[1]
            page[2] = 'כתוב בהלכות וכל זמן' + page[2]
            page = [[par.strip() for par in p.split('\n') if par.strip()] for p in page]
            page = ['<br>'.join(p) for p in page]
        else:
            page = [par.strip() for par in p.split('\n') if par.strip()]
            page = ['<br>'.join(page)]
    page = [re.sub('@|\d|\n', '', p) for p in page]
    return [re.sub(' +', ' ', p).strip() for p in page]

def createlinks(data, title):
    links = []
    link = {'refs': [],
        'type': 'commentary',
        'generated_by': 'rif commentary'}
    if title in ['zg', 'zk']:
        masechet = 'Gittin' if title == 'zg' else 'Ketubot'
        for p, page in enumerate(data):
            if page:
                for s, _ in enumerate(page):
                    daf = section_to_daf(p+1)
                    section = s+1
                    if masechet == 'Ketubot' and daf == '21b' and section == 3:
                        section = 2
                    ravad = f'Hasagot HaRaavad on Rif {masechet} {daf}:{section}'
                    ramban = f'Sefer HaZekhut on Hasagot HaRaavad {masechet} {daf}:{s+1}'
                    if Ref(ravad).text('he').text:
                        links.append(copy.deepcopy(link))
                        links[-1]['refs'] = [ravad, ramban]
                        for l in Ref(ravad).linkset():
                            if l.generated_by == 'rif inline commentaries':
                                links.append(copy.deepcopy(link))
                                links[-1]['refs'] = [l.refs[0], ramban]
                    else: print(ramban, 'not finding ravad')
    elif title == 'zy':
        for p, page in enumerate(data):
            for s, section in enumerate(page):
                daf = section_to_daf(p+1)
                rif = f'Rif Yevamot {daf}'
                trif = Ref(rif).text('he')
                matches = match_ref(trif, [section], base_tokenizer=base_tokenizer, dh_extract_method=find_dh)['matches']
                for match in matches:
                    if match:
                        links.append(copy.deepcopy(link))
                        links[-1]['refs'] = [match.tref, f'Sefer HaZekhut on Hasagot HaRaavad Yevamot {daf}:{s+1}']
    elif title == 'td':
        refs = [['36b:3'], ['51b:4', '52a:4'], ['54a:3']]
        for l in refs:
            daf = l[0].split(':')[0]
            for ref in l:
                links.append(copy.deepcopy(link))
                links[-1]['refs'] = [f'Rif Ketubot {ref}', f"Ha'atakat Teshuvat HaRif Ketubot {daf}:1"]
    return links

for title in ['td', 'zg', 'zy', 'zk']:
    with open(f'{path}/commentaries/{title}.txt', encoding='utf-8') as fp:
        data = fp.read()
    if title == 'zg':
        intro = data.split('@@', 1)[0]
    data = parse_pages(data, title)
    newdata = []
    for page in data:
        newdata.append([])
        for p in page:
            newdata[-1] += parse_page(p, title)
    links = createlinks(newdata, title)
    with open(f'{path}/commentaries/json/{title}.json', 'w', encoding='utf-8') as fp:
        json.dump(newdata, fp)
    with open(f'{path}/commentaries/json/links_{title}.json', 'w', encoding='utf-8') as fp:
        json.dump(links, fp)
