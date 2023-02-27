import re
import django
django.setup()
import json
import copy
from parsing_utilities.util import getGematria
from sefaria.utils.talmud import daf_to_section, section_to_daf
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.model import *
from rif_utils import path
from more_talmud_refs import base_tokenizer

def find_dh(comm):
    dh = comm.split('אלפס ז"ל')[1]
    dh = re.sub("וכו'|כו'", '', dh)
    return ' '.join(comm.split()[:7])

for title in ['tds', 'ravad_Makkot', 'ravad_Shevuot']:
    with open(f'{path}/commentaries/{title}.txt', encoding='utf-8') as fp:
        data = fp.read()
    newdata = [[] for _ in range(66)]
    links = []
    link = {'refs': [],
        'type': 'commentary',
        'generated_by': 'rif commentary'}
    if title == 'ravad_Shevuot':
        data = re.sub('@00([^\n]*)\n', r'<b>\1</b><br>', data)
        for line in data.split('\n'):
            if re.findall(r'אלפס ז"ל \[דף [א-ל]\'?"?[א-ט]? ע"[אב]\]', line):
                daf, amud = re.findall(r'אלפס ז"ל \[דף ([א-ל]\'?"?[א-ט]?) ע"([אב])\]', line)[0]
                sec = getGematria(daf) * 2 - 3 + getGematria(amud)
                line = re.sub(r'(אלפס ז"ל) \[דף [א-ל]\'?"?[א-ט]? ע"[אב]\]', r'\1', line)
                newdata[sec].append(line)
                daf = section_to_daf(sec+1)
                trif = Ref(f'Rif Shevuot {daf}').text('he')
                matches = match_ref(trif, [line], base_tokenizer=base_tokenizer, dh_extract_method=find_dh)['matches']
                for match in matches:
                    if match:
                        links.append(copy.deepcopy(link))
                        links[-1]['refs'] = [match.tref, f'Hasagot HaRaavad on Rif Shevuot {daf}:{len(newdata[sec])}']
            else:
                newdata[sec][-1] += f'<br>{line.strip()}'
    else:
        for comm in data.split('@@')[1:]:
            daf, comm = comm.split(None, 1)
            sec = daf_to_section(daf.split(':')[0]) - 1
            if title != 'tds':
                comm = re.sub(': +\n', ':<br>', comm, 1)
                comm = comm.replace('\n', '')
                newdata[sec].append(comm)
                dafpar = f"{daf.split(':')[0]}:{len(newdata[sec])}"
                links.append(copy.deepcopy(link))
                links[-1]['refs'] = [f'Rif Makkot {daf}', f'Hasagot HaRaavad on Rif Makkot {dafpar}']
            else:
                newdata[sec] = [par.strip() for par in comm.split('\n') if par.strip()]
                links = [{'refs': ['Rif Shevuot 31a:3', "Ha'atakat Teshuvat HaRif Shevuot 31a:1"],
                    'type': 'commentary',
                    'generated_by': 'rif commentary'}]

    if title == 'tds':
        with open(f'{path}/commentaries/json/{title}.json', 'w', encoding='utf-8') as fp:
            json.dump(newdata, fp)
    else:
        with open(f'{path}/tags/topost/{title}.json', 'w', encoding='utf-8') as fp:
            json.dump(newdata, fp)
    with open(f'{path}/commentaries/json/links_{title}.json', 'w', encoding='utf-8') as fp:
        json.dump(links, fp)
