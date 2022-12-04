import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup
import re
import os
from sefaria.utils.hebrew import encode_hebrew_numeral
from itertools import chain

MIS, ER, NO = [[] for _ in range(3)]

def get_data(chumash, parasha, ot):
    files = {}
    for s in [ot, f'אות {ot}']:
        for m in ['_', '_א', '_ב', '_ג', '']:
            for e in ['', ' (1)']:
                path = f'commentary/פירוש הסולם/{chumash}/{parasha}/{s}{m}{e}.html'
                try:
                    with open(f'{path}') as fp:
                        files[path] = fp.read()
                except FileNotFoundError:
                    pass
    files = [files[f] for f in files if not re.search('li>כתבי בעל הסולם / זהר עם פירוש הסולם / .* / מראות הסולם', files[f])]
    if not files:
        MIS.append(f'{parasha} {ot}')
    if len(files) > 1:
        print(f'{len(files)} files in {parasha} {ot}')
    if files:
        return files


def get_chumash_parasha(title):
    if title == 'צו':
        title = '02 צו'
    for chumash in os.listdir('commentary/פירוש הסולם/'):
        for parasha in os.listdir(f'commentary/פירוש הסולם/{chumash}'):
            if title in parasha:
                return chumash, parasha
    raise Exception(f'{title}')

def handle_element(element):
    new = False
    if not element.name:
        text = element.string.replace('\u200b', ' ').strip()
        text = re.sub(' +\.', '.', text)
        return [' '.join(text.split()).replace('&quot;', '"')], new
    if element.name in ['br', 'p', 'div']:
        new = True
    text = ['']
    for child in element.children:
        subtext, subnew = handle_element(child)
        if subnew:
            text += subtext
        else:
            if subtext:
                text[-1] += f' {subtext[0]}'
                text[-1] = re.sub(' +\.', '.', text[-1])
                text += subtext[1:]
    text = [' '.join(t.split()) for t in text if t.strip()]
    if (element.name == 'b' or 'style' in element.attrs and 'bold' in element.attrs['style']) and text:
        text = [f'<b>{t}</b>' for t in text]
    if not text:
        text = ['']
    return text, new

def parse_file(data, ot, i):
    soup = BeautifulSoup(data, 'html.parser')
    try:
        sulam = soup.find_all('h3')[-1]
    except IndexError:
        ER.append(f'{title} {ot}')
        return
    if sulam.text != 'פירוש הסולם':
        NO.append(f'{title} {ot}')
        return
    for element in sulam.next_elements:
        if element.name == 'span':
            # if element.attrs != {'style': 'font-weight:bold'}:
            #     print(ot, 'span', element)
            pass
        elif element.name == 'a':
            if 'class' in element.attrs and element.attrs['class'] == ['unit_link']:
                pass
            else:
                if ('class' not in element.attrs or 'glyphicon' not in element.attrs['class']) and 'href' not in element.attrs:
                    print(ot, 'a n', element)
                if element.text and element.text.replace('\u200b', '').strip():
                    print(ot, 'a w/ text', element)
        elif not element.name or element.name in ['br', 'b', 'p', 'font', 'div']:
            pass
        else:
            print(ot, 'another tag', element)
    wrapper = BeautifulSoup().new_tag('span')
    wrapper.extend(list(sulam.next_siblings))
    ot_text = handle_element(wrapper)[0]
    start = re.findall('^(?:<b>)?[א-ת]*\)', ot_text[0])
    if not start or start[0][:-1] != ot:
        print('no ot in the beginning', ot, ot_text[0])
    i = f'[{encode_hebrew_numeral(i)[0]}] ' if i else ''
    ot_text[0] = re.sub('^(<b>)?([/א-ת]* *\) *)', r'\1'+i, ot_text[0])
    ot_text[0] = re.sub(f'^{ot} ', '', ot_text[0])
    return ot_text

def parse_parash(title):
    chumash, parasha = get_chumash_parasha(title)
    print(parasha)
    if title == 'בראשית א':
        length = 482
    elif title == 'בראשית א':
        length = 488
    else:
        length = len(Ref(f'{hname}, {title}').all_segment_refs())
    parasha_text = []
    otiot = range(length)
    if title == 'האזינו':
        otiot = chain(range(22), range(201, 260))
    elif title == 'האדרא זוטא':
        otiot = range(22, 201)
    for ot in otiot:
        ot = re.sub('[׳״]', '', encode_hebrew_numeral(ot+1)).replace('ער', 'רע')
        files = get_data(chumash, parasha, ot)
        if not files:
            parasha_text.append([])
            continue
        text = []
        for d, data in enumerate(files, 1):
            new = parse_file(data, ot, d if len(files)>1 else None)
            if new:
                text += new
        parasha_text.append(text)
    return parasha


name = 'Zohar TNNNG'
hname = Ref(name).he_normal()
index = library.get_index(name)
nodes = index.schema['nodes'][:2] + [{'titles': [1, {'text': 'בראשית ב'}]}] + index.schema['nodes'][2:]
texts = []
for node in nodes[:53]:
    title = node['titles'][1]['text']
    if title == 'בראשית':
        title = 'בראשית א'
    print(title)
    text = parse_parash(title)
    if title == 'בראשית ב':
        texts[-1] += text
    else:
        texts.append(text)

with open('report.txt', 'w') as fp:
    fp.write('\n'.join(['missing files']+MIS+['\n', 'erroneous files']+ER+['\n', 'files withno sulam']+NO))
