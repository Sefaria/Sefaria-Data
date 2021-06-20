import csv
import django
django.setup()
from sefaria.model import *
from sources.functions import getGematria, post_index, post_text, post_link, add_category
import copy

text = [[] for _ in range(407)]
links = []
sa = 'Shulchan Arukh, Choshen Mishpat'
cs = f'Chatam Sofer on {sa}'
link = {'refs': [],
        'generated_by': 'chatam sofer sa cm',
        'type': 'commentary',
        'auto': True}
server = 'http://localhost:9000'
server = 'https://newtos.cauldron.sefaria.org'

with open('cs-final.csv', encoding='utf-8', newline='') as fp:
    data = csv.DictReader(fp)
    for row in data:
        siman = getGematria(row['siman'])
        text[siman-1].append(row['content'].strip())
        base = row['basis']
        if base in sa:
            base = sa
        else:
            base = f'{base} on {sa}'
        seif = getGematria(row['seif'])
        if not seif:
            print('no seif', row['content'])
            continue
        ref = f'{base} {siman}:{seif}'
        if 'Siftei' in base:
            ref += ':1'
        if not Ref(ref).text('he').text:
            print('no ref', row['content'], ref)
            continue
        cs_ref = f'{cs} {siman}:{len(text[siman-1])}'
        links.append(copy.deepcopy(link))
        links[-1]['refs'] = [ref, cs_ref]
        if base != sa:
            base_links = Ref(ref).linkset()
            options = [r for bl in base_links for r in bl.refs if r.startswith(sa)]
            if len(options) == 0:
                print('no links in base', ref)
                continue
            if len(options) > 1:
                print('more than one link in base', ref)
            links.append(copy.deepcopy(link))
            links[-1]['refs'] = [options[0], cs_ref]

cats = ["Halakhah", "Shulchan Arukh", "Commentary", 'Chatam Sofer']
add_category('Chatam Sofer', cats, server=server)

record = SchemaNode()
record.add_primary_titles(cs, 'חתם סופר על שלחן ערוך חושן משפט')
node = JaggedArrayNode()
node.key = 'default'
node.default = True
node.add_structure(['Siman', 'Pararaph'])
record.append(node)
record.validate()
index_dict = {
    'collective_title': 'Chatam Sofer',
    'title': cs,
    'categories': cats,
    'schema': record.serialize(),
    'dependence' : 'Commentary',
    'base_text_titles': [sa, f"Siftei Kohen on {sa}", f"Me'irat Einayim on {sa}", f'Turei Zahav on {sa}', f"Be'er HaGolah on {sa}"]
}
post_index(index_dict, server=server)

text_version = {
    'versionTitle': "Shulhan Arukh, Hoshen ha-Mishpat, Lemberg, 1898",
    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
    'language': 'he',
    'text': text
}
post_text(cs, text_version, server=server, index_count='on')
post_link(links, server=server, VERBOSE=False)
