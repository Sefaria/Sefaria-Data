import django
django.setup()
from sefaria.model import *
import re
from sources.functions import getGematria, post_index, post_text, post_link, add_term, add_category
from sefaria.utils.talmud import section_to_daf
from data_utilities.dibur_hamatchil_matcher import ComputeLevenshteinDistanceByWord, match_text, match_ref

with open('gilyon_hashas.txt', encoding='utf-8') as fp:
    data = fp.readlines()

book = 'Gilyon HaShas'
A,Y=0,0
mases = {}
links = []
for line in data:
    line = line.strip()
    if not line:
        continue

    loc = re.findall('גליון הש"ס מסכת (.*?) דף (.*?) עמוד ([אב])', line)
    if loc:
        mas, daf, amud = loc[0]
        mas = f'{Ref(mas)}'
        if 'Shekalim' in mas:
            mas = 'Jerusalem Talmud Shekalim'
        i = getGematria(daf) * 2 - 3 + getGematria(amud)
        sec = 0
        try:
            mases[mas][i]
        except (IndexError, KeyError) as e:
            if isinstance(e, KeyError):
                mases[mas] = []
            mases[mas] += [[] for _ in range(i+1-len(mases[mas]))]
        base = ''
        continue

    if '.' in line:
        l1, l2 = line.split('.', 1)
    mases[mas][i].append(f'<b>{l1}.</b>{l2}')
    sec += 1
    A+=1

    if 'Shekalim' in mas:
        continue

    if any(line.startswith(g) for g in ["גמ'", "גמרא", "מתני", 'במשנה', "במתני'", "בגמ'"]):
        base = mas
    elif any(line.startswith(r) for r in ['רש"י', 'ברש"י']):
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
        #print(mas, line)
        base = ''
        continue

    dh = line.split('.')[0]
    page = section_to_daf(i+1)
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
            com = ' '.join(com.split()[:len(dh.split())+1])
            if match_text(com.split(), [dh]):
                options[com] = f'{subref}'
        levs = {}
        for com in options:
            levs[ComputeLevenshteinDistanceByWord(dh, com)] = options[com]
        if not levs:
            continue
        ref = levs[min(levs)]
        ref2 = ':'.join(ref.split(':')[:-1])

    links.append({"refs": [ref, f'{book} on {mas} {page}:{sec}'],
                        "type": "Commentary",
                        "auto": True,
                        "generated_by": 'gilyon hashas'})
    Y+=1

#SERVER = 'http://localhost:9000'
SERVER = 'https://gilyon.cauldron.sefaria.org'
add_term(book, 'גליון הש"ס', server=SERVER)
path = ['Talmud', 'Bavli', 'Acharonim on Talmud', book]
add_category(book, path, server=SERVER)
for seder in ['Zeraim', 'Moed', 'Nashim', 'Nezikin', 'Kodashim', 'Tahorot']:
    add_category(f'Seder {seder}', path+[f'Seder {seder}'], server=SERVER)
for mas in mases:
    schema = JaggedArrayNode()
    title = f'{book} on {mas}'
    gemara_ind = library.get_index(mas)
    schema.add_primary_titles(title, f'גליון הש"ס על {gemara_ind.get_title("he")}')
    schema.depth = 2
    schema.add_structure(['Daf', 'Comment'])
    schema.addressTypes = ['Talmud', 'Integer']
    schema.validate()
    order = gemara_ind.order
    seder = gemara_ind.categories[-1]
    print(mas)
    index_dict = {
        'title': title,
        'categories': path + [seder],
        'schema': schema.serialize(),
        'collective_title': book,
        'dependence': 'Commentary',
        'base_text_titles': [mas]
    }
    #post_index(index_dict, server=SERVER)

    text_version = {
        'versionTitle': 'Vilna Edition',
        'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH001300957/NLI',
        'language': 'he',
        'text': mases[mas]
    }
    #post_text(title, text_version, index_count='on', server=SERVER)

post_link(links, server=SERVER, VERBOSE=False)
print(A,Y)