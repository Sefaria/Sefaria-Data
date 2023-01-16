import django
django.setup()
from sefaria.model import *
import re
from sources.functions import getGematria, post_text, post_index, post_link
import requests
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.utils.talmud import section_to_daf

#SERVER = 'http://localhost:9000'
SERVER = 'https://maharsha.cauldron.sefaria.org'
Y, A = 0, 0

def find_dh(dh, daf):
    talmud = Ref(f'Eruvin {daf}').text('he', vtitle='Wikisource Talmud Bavli')
    return match_ref(talmud, [dh], base_tokenizer=lambda x: x.split())['matches'][0]

book = 'Rav Nissim Gaon on Eruvin'
with open('ranag.txt', encoding='utf-8') as fp:
    data = fp.read()
pages = []
links = []
data, notes = data.split('**')
notes = re.findall('\*(.*?)\n', notes)
while '*' in data:
    data = data.replace('*', f'<sup>$</sup><i class="footnote">{notes.pop(0).strip()}</i>', 1)
data = data.replace('$', '*')
data = data.split('\n')
old_sec = -1
twice = False

for line in data:
    line = ' '.join(line.split())
    if not line:
        continue
    loc = re.findall(f'רב ניסים גאון מסכת עירובין דף (.*?) עמוד ([אב])', line)
    if loc:
        daf, amud = loc[0]
        sec = getGematria(daf) * 2 + getGematria(amud) - 3
        if sec == old_sec:
            if twice:
                skip = True
            twice = True
        else:
            skip, twice = False, False
        old_sec = sec
        continue
    if skip:
        continue
    pages += [[] for _ in range(sec+1-len(pages))]
    pages[sec].append(line)

for p, page in enumerate(pages):
    if not page:
        continue
    if not page[-1].endswith(':'):
        try:
            next_page = [l for l in pages[p+1:] if l!=[]][0]
        except IndexError:
            continue
        next_ind = pages.index(next_page)
        if ':' not in next_page[0]:
            print('no :', next_page[0])
            continue
        prev, next = next_page[0].split(':')
        page[-1] += f' {prev}:'
        next_page[0] = next.strip()
        if not next_page[0]:
            next_page.pop(0)
        pages[next_ind] = next_page

for sec, page in enumerate(pages):
    for seg, comm in enumerate(page):
        if '.' in comm:
            dh, comm = comm.split('.', 1)
            pages[sec][seg] = f'<b>{dh}.</b>{comm}'
            daf = section_to_daf(sec+1)
            talmud = find_dh(dh, daf)
            A += 1
            if talmud:
                Y += 1
                links.append({'refs': [talmud.tref, f'{book} {daf}:{seg+1}'],
                            'generated_by': 'r. nissim gaon eruvin',
                            'type': 'Commentary',
                            'auto': True})

ind = requests.request('get', 'https://sefaria.org/api/v2/raw/index/Rav_Nissim_Gaon_on_Shabbat').json()
ind['title'] = ind['schema']['titles'][1]['text'] = ind['schema']['key'] = book
ind['schema']['titles'][0]['text'] = 'רב נסים גאון על מסכת עירובין'
ind['base_text_titles'] = ['Eruvin']
post_index(ind, server=SERVER)

text_version = {
    'versionTitle': 'Vilna Edition',
    'versionSource': 'http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001300957&context=L',
    'language': 'he',
    'text': pages
}
post_text(book, text_version, server=SERVER, index_count='on')

post_link(links, server=SERVER)
print(Y, A)
