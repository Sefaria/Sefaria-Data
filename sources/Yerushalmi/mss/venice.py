import os
from PIL import Image
import django
django.setup()
from sefaria.model import *
import json
from sources.Yerushalmi.links.parse import get_all_chapters_alts
from sefaria.system.exceptions import DuplicateRecordError
from pymongo.errors import DuplicateKeyError

with open('mapping.json') as fp:
    MAPPING = json.load(fp)
MAPPING['JTmock Shabbat, 2a'] = ['JTmock Shabbat 1:1:1', '1:1:1']
MAPPING['JTmock Shabbat, 18a'] = ['JTmock Shabbat 23:3:1', '24:5:1']
MAPPING['JTmock Eruvin, 18a'] = ['JTmock Shabbat 1:1:1', '1:1:1']
MAPPING['JTmock Makkot, 30d'] = ['JTmock Makkot 1:1:1', '1:1:1']

def create_thumb(file):
    im = Image.open(f'venice/{file}')
    height, length = im.size
    aspect_ratio = length / height
    new_h = 256
    new_l = int(aspect_ratio * length)
    im.thumbnail((new_h, new_l))
    im.save(f'venice/{file[:-4]}_thumbnail.jpg')

def find_page(mas, page):
    try:
        return MAPPING[f'{mas}, {page}']
    except KeyError:
        pass
    pereks = get_all_chapters_alts(Ref(mas))
    matches = []
    for per in pereks:
        for p in per:
            if page == p['addr']:
                matches.append(p)
    if not matches:
        return
    MAPPING[f'{mas}, {page}'] = (f'{matches[0]["start"].tref}', f'{matches[-1]["end"].tref.split()[-1]}')
    return f'{matches[0]["start"].tref}', f'{matches[-1]["end"].tref.split()[-1]}'

def create_manusripts():
    m = Manuscript()
    m.source = ''
    m.description = ''
    m.he_description = ''
    m.title = ' Jerusalem Talmud Bomberg (Venice) Pressing (1523 CE)'
    m.he_title = 'ירושלמי דפוס בומברג (ונציה) (1523)'
    try:
        m.save()
    except (DuplicateKeyError, DuplicateRecordError):
        pass

for file in os.listdir('venice/'):
    if 'thumb' in file:
        continue
    #create_thumb(file)
    create_manusripts()
    num = int(file[:4])
    if 6 < num < 135:
        page = num - 4
        inds = library.get_indexes_in_category(['Talmud','Yerushalmi','Seder Zeraim'])
        volume = 'I'
    elif 136 < num < 301:
        page = num - 134
        inds = library.get_indexes_in_category(['Talmud','Yerushalmi','Seder Moed'])
        volume = 'II'
    elif 302 < num < 432:
        page = num - 300
        inds = library.get_indexes_in_category(['Talmud','Yerushalmi','Seder Nashim'])
        volume = 'III'
    elif 434 < num < 534:
        page = num - 432
        inds = library.get_indexes_in_category(['Talmud','Yerushalmi','Seder Nezikin']) + ['Jerusalem Talmud Niddah']
        volume = 'IV'
    else:
        continue
    inds = [ind.replace('Jerusalem Talmud', 'JTmock') for ind in inds]
    daf = (page + 1) // 2
    pages = [f'{(page+1)//2}{"a" if page//2!=page/2 else "c"}', f'{(page+1)//2}{"b" if page//2!=page/2 else "d"}']
    refs = []
    for page in pages:
        f = False
        for ind in inds:
            ref = find_page(ind, page)
            if ref:
                if len(ref)!=2:
                    print(333, ind, page, ref)
                ref = f'{ref[0]}-{ref[1]}'
                refs.append(ref)
                f=True
        if not f:
            print(555, ind, page)
    mp = ManuscriptPage()
    if all(Ref(refs[0]).book == Ref(r).book for r in refs):
        mp.contained_refs = [Ref(f'{refs[0].split("-")[0]}-{refs[1].split("-")[-1]}').normal()]
        if f'{refs[0].split("-")[0]}-{refs[1].split("-")[-1]}'.count(':') != 4:print(111,refs)
    else:
        if len(refs) == 2:
            mp.contained_refs = refs
        else:
            mp.contained_refs = []
            for book in {Ref(r).book for r in refs}:
                r_b = [r for r in refs if Ref(r).book==book]
                if len(r_b) == 2:
                    mp.contained_refs.append(Ref(f'{r_b[0].split("-")[0]}-{r_b[1].split("-")[-1]}').normal())
                else:
                    mp.contained_refs += r_b
            print(777, mp.contained_refs)

    url = 'https://manuscripts.sefaria.org/venice/0'
    end = f'_FL77977{str(num+157).zfill(3)}'
    mp.page_id = f'Volume {volume} {pages[0]}-{pages[1][-1]}'
    num = str(num).zfill(3)
    mp.image_url = f'{url}{num}{end}.jpg'
    mp.thumbnail_url = f'{url}{num}{end}_thumbnail.jpg'
    mp.manuscript_slug = 'jerusalem-talmud-bomberg-(venice)-pressing-(1523-ce)'
    mp.set_expanded_refs()
    mp.validate()
    try:
        mp.save()
        print(f'saving msp {mp.page_id}')
    except (DuplicateKeyError, DuplicateRecordError):
        pass
