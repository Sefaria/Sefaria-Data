import django
django.setup()
from sefaria.model import *
import re
from sources.functions import getGematria, post_text, post_index, post_link, add_term, add_category
from sefaria.utils.talmud import section_to_daf
from data_utilities.dibur_hamatchil_matcher import ComputeLevenshteinDistanceByWord, match_text
import time

#SERVER = 'http://localhost:9000'
SERVER = 'https://maharsha.cauldron.sefaria.org'

with open('data.txt', encoding='utf-8') as fp:
    data = fp.readlines()
mases = {}
mas = ''
links = []
book = 'Piskei Tosafot'

for line in data:
    line = ' '.join(line.split())
    find_mas = re.findall('^פסקי תוספות (.*?)(?: פרק|$)', line)
    if find_mas:
        if mas != find_mas[0]:
            oi = 0
            old_daf = ''
            en_mas = library.get_index(find_mas[0]).title
            mases[en_mas] = []
        mas = find_mas[0]
        continue
    if not line:
        continue
    i, line = line.split(None, 1)
    i = getGematria(i)
    concat = True if i - oi == 0 else False
    if i - oi > 1:
        mases[en_mas] += [[] for _ in range(i-oi-1)]
    oi = i
    if concat:
        mases[en_mas][-1].append(line)
    else:
        mases[en_mas].append([line])

    daf = re.findall(r' דף \b(.{1,}?)\b', line[-20:])
    if daf and re.findall(f'[\[\(][^\]\)]*? דף {daf[-1]}', line):
        daf = None
    if daf:
        daf = old_daf = getGematria(daf[-1])
        old_amud = ''
        old_dh = ''
    elif old_daf:
        daf = old_daf
    else:
        continue

    amud = re.search('ע"([אב])', line)
    if amud:
        amud = old_amud = amud.group(1)
        old_dh = ''
    elif old_amud:
        amud = old_amud
    if amud:
        page = section_to_daf(daf*2+getGematria(amud)-2)
    else:
        page = daf
    dh = re.search(r'ד"ה \b(.{1,}?)\b', line)
    if dh:
        dh = old_dh = dh.group(1)
    elif old_dh:
        dh = old_dh
    else:
        continue

    options = {}
    for subref in Ref(f'Tosafot on {en_mas} {page}').all_segment_refs():
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
    links += [{"refs": [ref, f'{book} on {en_mas} {len(mases[en_mas])}:{len(mases[en_mas][-1])}'],
               "type": "Commentary",
               "auto": True,
               "generated_by": 'piskei tosfot'},
                 {"refs": [ref2, f'{book} on {en_mas} {len(mases[en_mas])}:{len(mases[en_mas][-1])}'],
              "type": "Commentary",
              "auto": True,
              "generated_by": 'piskei tosfot'}]
print(len(links))

add_term(book, 'פסקי תוספות', server=SERVER)
cats = ['Talmud', 'Bavli', 'Rishonim on Talmud', book]
add_category(book, cats, server=SERVER)
for seder in ['Zeraim', 'Moed', 'Nashim', 'Nezikin', 'Kodashim', 'Tahorot']:
    add_category(f'Seder {seder}', cats+[f'Seder {seder}'], server=SERVER)
for mas in mases:
    name = f'{book} on {mas}'
    talmud = library.get_index(mas)
    schema = JaggedArrayNode()
    schema.add_title(name, 'en', True)
    schema.add_title(f'פסקי תוספות על {talmud.get_title("he")}', 'he', True)
    schema.key = name
    schema.depth = 2
    schema.addressTypes = ['Integer', 'Integer']
    schema.sectionNames = ['Comment', 'Paragraph']
    schema.validate()
    index_dict = {
        'title': name,
        'categories': cats + talmud.categories[-1:],
        'schema': schema.serialize(),
        'dependence': 'Commentary',
        'base_text_titles': [mas],
        'collective_title': book}
    post_index(index_dict, server=SERVER)

    text_version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': mases[mas]}
    post_text(name, text_version, server=SERVER, index_count='on')

while True:
    try:
        x=post_link(links, server=SERVER, VERBOSE=False)
        if 'error' not in x and '503' not in x:
            break
    except:
        pass
    time.sleep(180)
