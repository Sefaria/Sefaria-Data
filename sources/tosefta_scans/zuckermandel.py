import csv
import json
import requests
import django
django.setup()
from sefaria.model import *
import re
from sources.functions import getGematria
from parsing_utilities.text_align import CompareBreaks
from sefaria.model.manuscript import Manuscript, ManuscriptPage
from sefaria.system.exceptions import InputError, DuplicateRecordError
from pymongo.errors import DuplicateKeyError

def parse_zucker():
    with open('zuckermandel.txt', encoding='utf-8') as fp:
        data = fp.read()
    data = re.sub('(תוספתא מסכת .*? \(צוקרמאנדל\) פרק .*)', r'\n\1', data)
    data = data.split('\n')
    mases = {}
    mas = ''

    for line in data:
        line = ' '.join(line.split())
        if not line:
            continue
        if re.findall('^הלכה [^ ]*$', line):
            continue
        find_mas = re.findall('תוספתא מסכת (.*?) \(צוקרמאנדל\) פרק (.*)', line)
        if find_mas:
            masechet, perek = find_mas[0]
            perek = getGematria(perek)
            if mas != masechet:
                if 'כלים' in masechet:
                    if 'קמא' in masechet:
                        en_mas = 'Kelim Kamma'
                    elif 'מציעא' in masechet:
                        en_mas = 'Kelim Metzia'
                    else:
                        en_mas = 'Kelim Batra'
                elif 'עדויות' in masechet:
                    en_mas = 'Eduyot'
                else:
                    en_mas = library.get_index(masechet).title.replace('Mishnah ', '')
                if en_mas == 'Oktzin':
                    en_mas = 'Oktsin'
                mases[en_mas] = []
                mas = masechet
            if perek == len(mases[en_mas]):
                continue
            if perek != len(mases[en_mas]) + 1:
                print('error in perek', line, perek, len(mases[en_mas]) + 1)
            mases[en_mas].append([])
            continue
        mases[en_mas][-1].append(line)
    return mases

def map(mases):
    mapping = {}
    for mas in mases:
        zucker = mases[mas]
        if mas == 'Makkot':
            zucker = mases[mas][:1] + [mases[mas][1] + mases[mas][2]] + mases[mas][3:]
        vilna = Ref(f'Tosefta {mas}').text('he').text
        if len(vilna) != len(zucker):
            print(mas, len(vilna), len(zucker))

        for p, perek in enumerate(zucker, 1):
            v_p = p
            if mas == 'Mikvaot' and p == 6:
                v_p = '6-7'
            if mas == 'Avodah Zarah' and p == 3:
                v_p = '3-4'
            if (mas == 'Mikvaot' and p > 6) or (mas == 'Avodah Zarah' and p > 3):
                v_p = p + 1
            v_text = Ref(f'Tosefta {mas} {v_p}').text('he').text
            if isinstance(v_text[0], list):
                v_text = [h for c in v_text for h in c]
            c = CompareBreaks(v_text, perek)
            p_map = c.create_mapping()
            for key, value in p_map.items():
                new_value = []
                for element in value:
                    zuc_p = p
                    if mas == 'Makkot' and p > 1:
                        if p == 2:
                            if element > 11:
                                zuc_p = 3
                                element -= 11
                        else:
                            zuc_p = p + 1
                    new_value.append({'chapter': zuc_p, 'halakha': element})
                    min_chap = min(k['chapter'] for k in new_value)
                    min_hal = min(k['halakha'] for k in new_value if k['chapter']==min_chap)
                    max_chap = max(k['chapter'] for k in new_value)
                    max_hal = max(k['halakha'] for k in new_value if k['chapter']==max_chap)
                    if (mas == 'Mikvaot' and p == 6) or (mas == 'Avodah Zarah' and p == 3):
                        if key > 5:
                            v_p = p + 1
                            key -= 5
                        else:
                            v_p = p
                    mapping[f'Tosefta {mas} {v_p}:{key}'] = f'{min_chap}:{min_hal}-{max_chap}:{max_hal}'
    return mapping

def parse_csv():
    erfurt, vienna = [], []
    with open('mss.csv', encoding='utf-8', newline='') as fp:
        data = csv.DictReader(fp)
        for row in data:
            input = erfurt if 'Berlin' in row['library'] else vienna
            row['chapter'] = getGematria(row['chapter'])
            if row['tractate'].strip() == 'כלים':
                if row['chapter'] < 8:
                    row['tractate'] = 'כלים קמא'
                elif row['chapter'] < 19:
                    row['tractate'] = 'כלים מציעא'
                    row['chapter'] -= 7
                else:
                    row['tractate'] = 'כלים בתרא'
                    row['chapter'] -= 18
            row['tractate'] = row['tractate'].replace('מקואות', 'מקוואות').replace('נידה', 'נדה').replace('עוקצים', 'עוקצין')
            input.append({'tractate': row['tractate'].strip(), 'chapter': row['chapter'], 'halakha': row['halakha'].strip(), 'num': row['im run'].strip()})
    return erfurt, vienna

def unite_refs(refs):
    uni = []
    titles = {' '.join(ref.split()[:-1]) for ref in refs}
    for title in titles:
        tit_refs = [ref.split()[-1] for ref in refs if title in ref]
        min_chapter = min([int(ref.split(':')[0]) for ref in tit_refs])
        min_halakha = min([int(ref.split(':')[1]) for ref in tit_refs if int(ref.split(':')[0]) == min_chapter])
        max_chapter = max([int(ref.split(':')[0]) for ref in tit_refs])
        max_halakha = max([int(ref.split(':')[1]) for ref in tit_refs if int(ref.split(':')[0]) == max_chapter])
        uni.append(Ref(f'{title} {min_chapter}:{min_halakha}-{max_chapter}:{max_halakha}').tref)
    return uni

def map_zucker(mas, chapter, halakha, data):
    if mas == 'עדויות':
        mas = 'עדיות'
    if halakha:
        nums = [e['num'] for e in data if e['tractate']==mas and e['chapter'] == int(chapter) and getGematria(e['halakha']) == int(halakha)]
    else:
        nums = {e['num'] for e in data if e['tractate'] == mas and e['chapter'] == int(chapter)}
    nums = list(set(nums))
    nums.sort()
    if not (0 < len(nums) < 3) and halakha:
        #print(f'found {len(nums)} in', mas, chapter, halakha)
        pass
    return nums

def create_manusripts():
    m = Manuscript()
    m.source = ''
    m.description = ''
    m.he_description = ''
    f = []
    for t, ht in [['Berlin, Staatsbibliothek, Or. fol. 1220', 'כתב יד ארפורט'], ['Wien, Oesterreichische Nationalbibliothek, 46', 'כתב יד וינה']]:
        m.title = t
        m.he_title = ht
        f.append(m.contents())
        try:
            m.save()
        except (DuplicateKeyError, DuplicateRecordError):
            pass
    with open('mss.json', 'w') as fp:
        json.dump(f, fp)

def erfurt_chapter():
    with open('conditions.csv', encoding='utf-8', newline='') as fp:
        return list(csv.DictReader(fp))

def erfurt_diif(conditions, mas, chapter, halakha, edition):
    for row in conditions:
        if row['masechet'] == mas and int(row['chapter<=']) <= chapter <= int(row['chapter=>']) and int(row[f'{edition}<=']) <= halakha <= int(row[f'{edition}=>']):
            return row['add']
    return 0

def add_refs(images, nums, ref):
    for num in nums:
        try:
            images[num]
        except KeyError:
            images[num] = []
        images[num].append(ref.tref)
    return images

def parse_file_ref(ref):
    mas = ' '.join(ref.split()[:-1])
    mas = mas.replace('Beitsah', 'Beitzah')
    try:
        mas = Ref(mas).normal().replace('Tosefta ', '')
    except InputError:
        mas = Ref(f'{mas.replace("Tosefta ", "")}').tref.replace('Mishnah ', '')
    mas = mas.replace('Mishnah ', '').replace('Katan', 'Kattan')
    chapter, halakha = ref.split()[-1].split(':')
    try:
        chapter, halakha = int(chapter), int(halakha)
    except ValueError:
        chapter, halakha = getGematria(chapter), getGematria(halakha)
    if mas == 'Kelim':
        if chapter < 8:
            mas = 'Kelim Kamma'
        elif chapter > 18:
            mas = 'Kelim Batra'
            chapter -= 18
        else:
            mas = 'Kelim Metzia'
            chapter -= 7
    return mas, chapter, halakha

def parse_vienna_filenames():
    with open('vienna_filenames.txt', encoding='utf-8') as fp:
        data = fp.readlines()
    mases = {}
    for line in data:
        if 'thumb' in line:
            continue
        if ' - ' not in line:
            print('no -', line)
            continue
        line = line.split('/')[-1].split('.')[0].strip()
        a, b = line.split(' - ')
        a, b = parse_file_ref(a), parse_file_ref(b)
        try:
            mases[a[0]]
        except KeyError:
            mases[a[0]] = []
        if a[0] == b[0]:
            mases[a[0]].append({'min': a[1]+a[2]/100, 'max': b[1]+b[2]/100, 'name': line})
        else:
            try:
                mases[b[0]]
            except KeyError:
                mases[b[0]] = []
            mases[a[0]].append({'min': a[1] + a[2] / 100, 'max': 100, 'name': line})
            mases[b[0]].append({'min': 0, 'max': b[1] + b[2] / 100, 'name': line})
    return mases

def find_vienna(vienna_filenames, chapter, halakha):
    addresses = []
    for add in vienna_filenames:
        if halakha != None and add['min'] <= int(chapter) + int(halakha) / 100 <= add['max']:
            addresses.append(add['name'])
        elif halakha == None and int(add['min']) <= chapter <= int(add['max']):
            addresses.append(add['name'])
    return addresses

def vina_from_refs(filename, vienna):
    a, b = filename.split(' - ')
    a, b = parse_file_ref(a), parse_file_ref(b)
    nums = []
    for e in [a, b]:
        he_mas = library.get_index(f'Tosefta {e[0]}').get_title('he').replace('תוספתא ', '')
        nums.append(map_zucker(he_mas, e[1], e[2], vienna))
    nums = set(nums[0]) & set(nums[1])
    if len(nums) != 1:
        print('error, not one page', filename, nums, a, b, he_mas)
    return nums.pop()

if __name__ == '__main__':
    create_manusripts()
    mases = parse_zucker()
    mapping = map(mases)
    conditions = erfurt_chapter()
    erfurt, vienna = parse_csv()
    vienna_filenames = parse_vienna_filenames()
    erfurt_images, vienna_images = {}, {}
    for seder in ['Zeraim', 'Moed', 'Nashim', 'Nezikin', 'Kodashim', 'Tahorot']:
        inds = library.get_indexes_in_category(['Tosefta', 'Vilna Edition', f'Seder {seder}'])
        for ind in inds:
            mas = ind.replace('Tosefta ', '')
            he_mas = library.get_index(ind).get_title('he').replace('תוספתא ', '')
            lieb = True if seder in ['Zeraim', 'Moed', 'Nashim'] or (seder == 'Nezikin' and 'Bava' in ind) else False
            check_erfurt = False if seder in ['Kodashim', 'Tahorot'] and 'Zevachim' not in ind else True

            if not lieb:
                for ref in Ref(ind).all_segment_refs():
                    zucker = mapping[ref.tref]
                    for part in zucker.split('-'):
                        chapter, halakha = part.split(':')
                        if check_erfurt and ('Zevachim' not in ind or int(chapter) < 6):
                            nums = map_zucker(he_mas, chapter, halakha, erfurt)
                            erfurt_images = add_refs(erfurt_images, nums, ref)
                        vienna_nums = map_zucker(he_mas, chapter, halakha, vienna)
                        vienna_addres = find_vienna(vienna_filenames[mas], chapter, halakha)
                        if len(vienna_nums) != len(vienna_addres):
                            if mas in ['Makkot', 'Makhshirin', 'Zavim', 'Oktsin']:
                                continue
                            print(mas, chapter, halakha, len(vienna_nums), len(vienna_addres))
                        vienna_images = add_refs(vienna_images, vienna_addres, ref)

            else:
                for ref in Ref(ind).all_segment_refs() + Ref(f'{ind} (Lieberman)'.replace('Kattan', 'Katan')).all_segment_refs():
                    chapter, halakha = ref.tref.split()[-1].split(':')
                    chapter, halakha = int(chapter), int(halakha)
                    edition = 'lieberman' if 'Lieberman' in ref.tref else 'vilna'
                    chapter = chapter + erfurt_diif(conditions, ind, chapter, halakha, edition)
                    nums = map_zucker(he_mas, chapter, None, erfurt)
                    erfurt_images = add_refs(erfurt_images, nums, ref)
                    vienna_nums = map_zucker(he_mas, chapter, None, vienna)
                    vienna_addres = find_vienna(vienna_filenames[mas], chapter, None)
                    vienna_images = add_refs(vienna_images, vienna_addres, ref)
                    if len(vienna_nums) != len(vienna_addres):
                        print(mas, chapter, halakha, len(vienna_nums), len(vienna_addres))

    msp = []
    for images in [erfurt_images, vienna_images]:
        for num, refs in images.items():
            if len(num) > 4:
                f_name = num
                num = vina_from_refs(f_name, vienna)
            else:
                f_name = ''
            num = int(num)
            refs = unite_refs(refs)
            mp = ManuscriptPage()
            if f_name:
                mp.image_url = f'https://storage.googleapis.com/manuscripts.sefaria.org/vienna-tosefta/{f_name}.jpg'
                mp.thumbnail_url = f'https://storage.googleapis.com/manuscripts.sefaria.org/vienna-tosefta/{f_name}_thumbnail.jpg'
            else:
                mp.image_url = f'https://storage.googleapis.com/manuscripts.sefaria.org/erfurt-tosefta/{num+3}_erfurt.jpg'
                mp.thumbnail_url = f'https://storage.googleapis.com/manuscripts.sefaria.org/erfurt-tosefta/{num+3}_erfurt_thumbnail.jpg'
            #if requests.request('get', mp.image_url).status_code != 200:
            #    print('error url', mp.image_url)
            #if requests.request('get', mp.thumbnail_url).status_code != 200:
            #    print('error url', mp.thumbnail_url)
            mp.contained_refs = refs
            if f_name:
                mp.manuscript_slug = 'wien-oesterreichische-nationalbibliothek-46'
            else:
                mp.manuscript_slug = "berlin-staatsbibliothek-or-fol-1220"
            if f_name:
                if num < 214 < num < 642:
                    mp.page_id = f'{num//2}r' if num/2 == num//2 else f'{num//2}v'
                else:
                    mp.page_id = f'{num // 2 + 1}r' if num / 2 == num // 2 else f'{num // 2 + 1}v'
            else:
                mp.page_id = f'{num//2+1}r' if num/2 == num//2 else f'{num//2+1}v'
            mp.set_expanded_refs()
            mp.validate()
            msp.append(mp.contents())
            try:
                mp.save()
            except (DuplicateKeyError, DuplicateRecordError):
                pass

    with open('msp.json', 'w') as fp:
        json.dump(msp, fp)
