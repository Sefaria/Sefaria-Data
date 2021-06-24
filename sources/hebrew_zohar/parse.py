import django
django.setup()
from sefaria.model import *
import re
from sources.functions import getGematria, strip_nekud, post_text
from sefaria.utils.talmud import section_to_daf
import csv
import json

#SERVER = 'http://localhost:9000'
SERVER = 'https://newtos.cauldron.sefaria.org'

books = {}
aramaic = {}
N,Y = 0,0
for i in range(8):
    with open(f'zoher{i}', encoding='utf-8') as fp:
        data = fp.read()

    data = re.sub('~ *(דף [^\'" ]{1,3}(?:\'\'?|")?[^\'" ]? ע(?:\'\'|")[אב])([\s\S]*?)<small><small><span style="color=#0055ff"> *\(\1\) *</small></small></span>',
                  r'\2\n~\1\n', data)
    data = data.split('\n')

    if i == 0:
        book = 'Zohar 1'
    elif i < 4:
        book = f'Zohar {i}'
    elif i < 6:
        book = 'Zohar 3'
    elif i == 6:
        book = 'Tikkunei Zohar'
    else:
        book = 'Zohar Chadash'
    try:
        books[book]
    except KeyError:
        books[book] = []
        aramaic[book] = []

    for line in data:
        line = re.sub('<!--#autolink.*?-->', '', line)
        line = line.strip()
        if not line:
            continue
        if line.startswith('~'):
            page = re.findall(r'דף ([^\'" ]{1,3}(?:\'\'?|")?[^\'" ]?) ע(?:\'\'|")([אב])', line)
            if not page:
                #(print(i, line))
                continue
            index = getGematria(page[0][0]) * 2 + getGematria(page[0][1]) - 3
            if len(books[book]) > index:
                print(i, len(books[book]), index, line)
            else:
                books[book] += [[] for _ in range(index - len(books[book]) + 1)]
                aramaic[book] += [[] for _ in range(index - len(aramaic[book]) + 1)]
            sec = 1
            continue
        if i == 7 and line.startswith('@'):
            books[book].append([])
            aramaic[book].append([])
            sec = 1
            continue
        if line.startswith('{'):
            line = line[1:-1].strip().replace('{', '(').replace('}', ')')
            line = re.sub(r'([\[\]\(\)])\1', r'\1', line)
            books[book][-1].append(line)
            if error:
                aramaic[book][-1].append(site)
            else:
                aramaic[book][-1].append('')
        else:
            if i == 7:
                ref = f'{library.get_index(book).all_section_refs()[len(books[book])-1]} {sec}'
            else:
                ref = f'{book} {section_to_daf(len(books[book]))}:{sec}'
            site = Ref(ref).text('he').text.strip()
            line, fixed_site = strip_nekud(re.sub('<.*?>|\(.*?\)', '', line)).strip(), strip_nekud(re.sub('<.*?>|\(.*?\)', '', site)).strip()
            if i == 7:
                line, fixed_site = re.sub('כמה דאת אמר|כדבר אחר', '', line).replace('ד', 'ה'), re.sub('כמה דאת אמר|כדבר אחר', '', fixed_site).replace('ד', 'ה')
            if line == fixed_site:
                Y+=1
                error = False
            else:
                N+=1
                error = True
                '''print(ref)
                print('site:', fixed_site)
                print('file:', line)'''
            sec += 1
print(Y,N)

report = []
for book in books:
    for sec, section in enumerate(books[book]):
        for seg, segment in enumerate(section):
            if aramaic[book][sec][seg]:
                if book == 'Zohar Chadash':
                    ref = f'{library.get_index(book).all_section_refs()[sec]} {seg+1}'
                else:
                    ref = f'{book} {section_to_daf(sec+1)}:{seg+1}'
                report.append({'ref': ref, 'aramaic': Ref(ref).text('he').text, 'hebrew': segment})

text_version = {
            'versionTitle': 'Hebrew Translation -- Torat Emet [he]',
            'versionSource': 'http://www.toratemetfreeware.com/online/f_01775.html',
            'language': 'he'}
books['Zohar'] = [books[f'Zohar {i}'] for i in range(1,4)]
name = 'Tikkunei Zohar'
text_version['text'] = books[name]
while 'status' not in post_text(name, text_version, server=SERVER):
    pass

name = 'Zohar'
with open('hebrew_zohar.json', 'w') as fp:
    json.dump(books[name], fp, ensure_ascii=False, indent=2)

name = 'Zohar Chadash'
for s, sec in enumerate(library.get_index(name).all_section_refs()):
    text_version['text'] = books[name][s]
    while 'status' not in post_text(sec.tref, text_version, server=SERVER):
        pass

with open('hebrew_zohar_aligning.csv', 'w', encoding='utf-8', newline='') as fp:
    writer = csv.DictWriter(fp, fieldnames=['ref', 'aramaic', 'hebrew'])
    writer.writeheader()
    for item in report:
        writer.writerow(item)
