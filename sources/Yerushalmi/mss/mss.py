import django
django.setup()
from sefaria.model import *
from sources.functions import getGematria
from sources.Yerushalmi.links.parse import get_all_chapters_alts
import csv
import re
from sefaria.model.manuscript import Manuscript, ManuscriptPage
from sefaria.system.exceptions import DuplicateRecordError
from pymongo.errors import DuplicateKeyError
import json
import requests

try:
    with open('mapping.json') as fp:
        MAPPING = json.load(fp)
except FileNotFoundError:
    MAPPING = {}

def fix_mas(mas):
    return mas.replace('ביכורים', 'בכורים').replace('נידה', 'נדה')

def eng_page(page):
    daf = getGematria(page.split()[0])
    amud = chr(getGematria(page.split()[1][-1]) + 96)
    return f'{daf}{amud}'

def get_page_ref(mas, page):
    try:
        return MAPPING[f'{mas}, {page}']
    except KeyError:
        pass
    pereks = get_all_chapters_alts(mas)
    matches = []
    for per in pereks:
        try:
            matches.append(per[page])
        except KeyError:
            pass
    if not matches:
        print(f'doesnt find page {page} in {mas}')
        MAPPING[f'{mas}, {page}'] = ('Jerusalem Talmud Makkot 3:5:1', '3:13:5')
        return 'Jerusalem Talmud Makkot 3:5:1', '3:13:5'
    start = matches[0].all_segment_refs()[0].normal()
    end = matches[-1].all_segment_refs()[-1].normal().split()[-1]
    if start.endswith('1:1:2'):
        start = Ref(start[:-1] + '1')
    MAPPING[f'{mas}, {page}'] = (start, end)
    return start, end

    '''    for p in per:
        if page == p['addr']:
            matches.append(p)
    if not matches:
        print(f'doesnt find page {page} in {mas}')
        MAPPING[f'{mas}, {page}'] = ('Jerusalem Talmud Makkot 3:5:1', '3:13:5')
        return 'Jerusalem Talmud Makkot 3:5:1', '3:13:5'
    elif matches[0]["start"].tref.endswith('1:1:2'):
        matches[0]["start"] = Ref(matches[0]["start"].tref[:-1] + '1')
    MAPPING[f'{mas}, {page}'] = (f'{matches[0]["start"].tref}', f'{matches[-1]["end"].tref.split()[-1]}')
    return f'{matches[0]["start"].tref}', f'{matches[-1]["end"].tref.split()[-1]}'''

def create_manusripts():
    m = Manuscript()
    m.source = ''
    m.description = ''
    m.he_description = ''
    m.title = 'Leiden Manuscript'
    m.he_title = 'כתב יד ליידן'
    try:
        m.save()
    except (DuplicateKeyError, DuplicateRecordError):
        pass

if __name__ == '__main__':
    create_manusripts()
    with open('mss.csv', encoding='utf-8', newline='') as fp:
        data = list(csv.DictReader(fp))

    for row in data:
        mp = ManuscriptPage()
        pages = row['Im_Title']
        reg = '^((?:[^ ]* ){1,2})([א-פ][א-י]? ע"[א-ד]) - ((?:[^ ]* ){1,2})([א-פ][א-י]? ע"[א-ד])'
        mas1, page1, mas2, page2 = re.findall(reg, pages)[0]
        mas1 = fix_mas(mas1)
        mas1 = Ref(f'ירושלמי דמע {mas1}')
        page1, page2 = eng_page(page1), eng_page(page2)
        ref = f'{get_page_ref(mas1, page1)[0]}-{get_page_ref(mas1, page2)[1]}'
        mp.contained_refs = [ref]

        folio = row['Im_File']
        part = re.findall('N1721([ab])', folio)[0]
        part = 'I' if part == 'a' else 'II'
        num = re.findall(r'(\d\d\d[rv]).jpg', folio)[0]
        url = f'https://manuscripts.sefaria.org/leiden/{part}{num}'
        mp.image_url = f'{url}.jpg'
        mp.thumbnail_url = f'{url}_thumbnail.jpg'
        mp.page_id = f'Part {part} {int(num[:-1])}{num[-1]}'

        mp.manuscript_slug = 'leiden-manuscript'
        mp.set_expanded_refs()
        mp.validate()
        try:
            mp.save()
            print(f'saving msp {mp.page_id}')
        except (DuplicateKeyError, DuplicateRecordError):
            pass

    with open('munich.csv', encoding='utf-8', newline='') as fp:
        data = list(csv.DictReader(fp))

    for row in data:
        mp = ManuscriptPage()
        pages = row['Im_Title']
        reg = 'שקלים (..? ע"[א-ד]) - שקלים (..? ע"[א-ד])'
        page1, page2 = re.findall(reg, pages)[0]
        page1, page2 = eng_page(page1), eng_page(page2)
        mas = Ref('ירושלמי דמע שקלים')
        ref = f'{get_page_ref(mas, page1)[0]}-{get_page_ref(mas, page2)[1]}'
        mp.contained_refs = [ref]

        num = row['Im_ImRun']
        url = 'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.0'
        mp.image_url = f'{url}{num}.jpg'
        mp.thumbnail_url = f'{url}{num}_thumbnail.jpg'
        mp.page_id = f'Cod. hebr. 95 pg. 0{num}'

        mp.manuscript_slug = 'munich-manuscript-95-(1342-ce)'
        mp.set_expanded_refs()
        mp.validate()
        try:
            mp.save()
            print(f'saving msp {mp.page_id}')
        except (DuplicateKeyError, DuplicateRecordError):
            pass

        '''if num == '234':
            for x in ['', '_thumbnail']:
                req = requests.get(f'https://storage.googleapis.com/manuscripts.sefaria.org/munich-manuscript/{pages}{x}.jpg')
                with open(f'munich/munich-manuscript-95Cod.hebr.95pg.0{num}{x}.jpg', 'wb') as fp:
                    fp.write(req.content)'''

    with open('mapping.json', 'w') as fp:
        json.dump(MAPPING, fp)
