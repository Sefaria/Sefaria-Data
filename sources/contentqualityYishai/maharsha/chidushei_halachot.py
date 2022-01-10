import json
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import BookNameError
import re
from sources.functions import getGematria, post_text, post_index, post_link
import requests
from sefaria.utils.talmud import section_to_daf
from data_utilities.dibur_hamatchil_matcher import ComputeLevenshteinDistanceByWord, match_text, match_ref
import time

def find_index(book):
    try:
        return library.get_index(f"{book.replace('מסכת', 'על')}").title
    except BookNameError:
        try:
            return library.get_index(f"{book.replace('מסכת', 'על מסכת')}").title
        except BookNameError:
            try:
                return library.get_index(f" {book.replace('מסכת', 'על מסכת')}").title
            except BookNameError:
                return find_index(book.replace('חידושי', 'חדושי'))

SERVER = 'http://localhost:9000'
#SERVER = 'https://maharsha.cauldron.sefaria.org'
links = []
indexes = []
A,Y = 0,0
kret = requests.request('get', 'https://sefaria.org/api/v2/raw/index/Chidushei_Agadot_on_Chullin').json()
kret['title'] = 'Chidushei Agadot on Keritot'
kret['schema']['titles'][0]['text'] = 'רב נסים גאון על מסכת ערובין'
kret['schema']['titles'][1]['text'] = 'Chidushei Agadot on Keritot'
kret['schema']['key'] = 'Chidushei Agadot on Keritot'
#post_index(kret, server=SERVER)

for en, he in [['halachot', 'הלכות'], ['agadot', 'אגדות']]:
    with open(f'chidushei_{en}.txt', encoding='utf-8') as fp:
        data = fp.readlines()
    mass = {}
    inds = {}
    for line in data:
        line = ' '.join(line.split())
        if not line:
            continue
        if len(line.split()) < 4 and line.split()[0] == 'פרק':
            continue
        loc = re.findall(f'מהרש"א חידושי {he} מסכת (.*?) דף (.*?) עמוד ([אב])', line)
        if loc:
            masechet, daf, amud = loc[0]
            inds[masechet] = re.findall(f'(חידושי {he} מסכת .*?) דף', line)[0]
            mas = library.get_index(masechet).title
            sec = getGematria(daf) * 2 + getGematria(amud) - 3
            continue
        edited = '<b>' + line.replace(' ', '</b> ', 1)
        try:
            mass[masechet]
        except KeyError:
            mass[masechet] = []
        try:
            mass[masechet][sec]
        except IndexError:
            mass[masechet] += [[] for _ in range(sec+1-len(mass[masechet]))]
        mass[masechet][sec].append(edited)

        A+=1
        if any(line.startswith(g) for g in ["גמ'", "גמרא", "מתני", 'במשנה', "במתני'", "בגמ'", 'בגמרא']) or en == 'agadot':
            base = mas
        elif any(line.startswith(r) for r in ['רש"י', 'ברש"י', 'בפרש"י', 'בפירש"י', 'פירש"י', 'פרש"י']):
            base = f'Rashi on {mas}'
        elif any(line.startswith(r) for r in ['רשב"ם', 'ברשב"ם']):
            base = f'Rashbam on {mas}'
        elif any(line.startswith(t) for t in ["תוס", 'תוד"ה', "בתוס'", 'תוספות', 'תד"ה']):
            base = f'Tosafot on {mas}'
        elif any(line.startswith(s) for s in ['בהר"ן', 'בר"ן', 'ר"נ', 'בהר"נ']):
            base = f'Ran on {mas}'
        elif line.startswith("שם"):
            if not base:
                continue
        elif any(line.startswith(s) for s in ['בא"ד', 'בסה"ד']):
            base = 'same'
        elif any(line.startswith(s) for s in ['ד"ה', 'בד"ה']):
            pass
        else:
            #print(he, inds[masechet], line[:20])
            continue

        dh = line.split('.')[0].split("כו'")[0].split('עכ"ל')[0]
        page = section_to_daf(len(mass[masechet]))
        if base == mas:
            gemara = Ref(f'{base} {page}').text('he', vtitle='Wikisource Talmud Bavli')
            match = match_ref(gemara, [dh], base_tokenizer=lambda x: x.split())['matches'][0]
            if match == None:
                continue
            else:
                ref = match.tref
                ref2 = ''
        elif base != 'same':
            if 'ד"ה' in dh:
                dh = dh.split('ד"ה')[1]
            else:
                dh = ' '.join(dh.split()[1:])
            dh = re.split("וכו'|כו'", dh)[0].strip()
            options = {}
            coms = {}
            for subref in Ref(f'{base} {page}').all_segment_refs():
                com = subref.text('he').text
                com = ' '.join(com.split()[:len(dh.split()) + 1])
                if match_text(com.split(), [dh]):
                    options[com] = f'{subref}'
            levs = {}
            for com in options:
                levs[ComputeLevenshteinDistanceByWord(dh, com)] = options[com]
            if not levs:
                continue
            ref = levs[min(levs)]
            ref2 = ':'.join(ref.split('on ')[1].split(':')[:-1])

        index = find_index(inds[masechet])
        links.append({"refs": [ref, f'{index} {page}:{len(mass[masechet][sec])}'],
                      "type": "Commentary",
                      "auto": True,
                      "generated_by": 'new maharsha'})
        Y+=1
        if ref2:
            links.append({"refs": [ref2, f'{index} {page}:{len(mass[masechet][sec])}'],
                          "type": "Commentary",
                          "auto": True,
                          "generated_by": 'new maharsha'})

    for mas in mass:
        index = find_index(inds[mas])
        indexes.append(index)
        Ref(index).linkset().delete() #just for local
        text_version = {
                'versionTitle': 'Vilna Edition',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
                'language': 'he',
                'text': mass[mas]
            }
        while True:
            try:
                post_text(index, text_version, server=SERVER, index_count='on')
                post_link(links, server=SERVER, VERBOSE=False)
                break
            except:
                time.sleep(180)
print(Y,A)
with open('indexes.json', 'w') as fp:
    json.dump(indexes, fp)
