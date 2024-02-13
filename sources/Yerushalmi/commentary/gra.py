import django
django.setup()
from sefaria.model import *
from docx import Document
import os
import re
from sources.functions import getGematria
import json
from sefaria.utils.talmud import section_to_daf, daf_to_section
from sources.tosefta_scans.zuckermandel import unite_refs
from linking_utilities.dibur_hamatchil_matcher import match_ref
import csv

YERUSHALMI = 'Jerusalem Talmud'
HEB_YER = 'תלמוד ירושלמי'
try:
    with open('vilna_mapping.json') as fp:
        VILNA_MAPPING = json.load(fp)
except FileNotFoundError:
    VILNA_MAPPING = {'Jerusalem Talmud Niddah 4, 12b': 'Jerusalem Talmud Niddah 4:1', 'Jerusalem Talmud Niddah, 12b': 'Jerusalem Talmud Niddah 3:5-4:1'}
VILNA_MAPPING['Jerusalem Talmud Shabbat 21, 92a'] = 'Jerusalem Talmud Shabbat 21'
VILNA_MAPPING['Jerusalem Talmud Shabbat 22, 92a'] = 'Jerusalem Talmud Shabbat 22'
VILNA_MAPPING['Jerusalem Talmud Shabbat, 92a'] = 'Jerusalem Talmud Shabbat 20:5:3-23:1:1'
VILNA_MAPPING['Jerusalem Talmud Shabbat 24, 92b'] = 'Jerusalem Talmud Shabbat 24'
VILNA_MAPPING['Jerusalem Talmud Shabbat, 92b'] = 'Jerusalem Talmud Shabbat 23-24'
VILNA_MAPPING['Jerusalem Talmud Bava Kamma 4, 17a'] = 'Jerusalem Talmud Bava Kamma 4:1:1'
VILNA_MAPPING['Jerusalem Talmud Bava Kamma 9, 37a'] = 'Jerusalem Talmud Bava Kamma 9:1:1'
VILNA_MAPPING['Jerusalem Talmud Berakhot 3, 21a'] = 'Jerusalem Talmud Berakhot 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Berakhot 7, 50b'] = 'Jerusalem Talmud Berakhot 7:1:1'
VILNA_MAPPING['Jerusalem Talmud Bikkurim 2, 6a'] = 'Jerusalem Talmud Bikkurim 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Chagigah 3, 14b'] = 'Jerusalem Talmud Chagigah 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Demai 3, 11a'] = 'Jerusalem Talmud Demai 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Demai, 6b'] = 'Jerusalem Talmud Demai 1:4:7-8'
VILNA_MAPPING['Jerusalem Talmud Eruvin 2, 13a'] = 'Jerusalem Talmud Eruvin 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Eruvin 7, 50b'] = 'Jerusalem Talmud Eruvin 7:10:3-4'
VILNA_MAPPING['Jerusalem Talmud Eruvin 9, 55b'] = 'Jerusalem Talmud Eruvin 9:1:1'
VILNA_MAPPING['Jerusalem Talmud Gittin 3, 14a'] = 'Jerusalem Talmud Gittin 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Gittin 6, 33b'] = 'Jerusalem Talmud Gittin 6:1:1'
VILNA_MAPPING['Jerusalem Talmud Ketubot 2, 8b'] = 'Jerusalem Talmud Ketubot 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Ketubot 7, 42b'] = 'Jerusalem Talmud Ketubot 7:1:1'
VILNA_MAPPING['Jerusalem Talmud Ketubot 10, 57b'] = 'Jerusalem Talmud Ketubot 10:1:1'
VILNA_MAPPING['Jerusalem Talmud Kilayim 2, 5b'] = 'Jerusalem Talmud Kilayim 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Maasrot 2, 6b'] = 'Jerusalem Talmud Maasrot 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Maasrot 3, 12a'] = 'Jerusalem Talmud Maasrot 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Maasrot 4, 18a'] = 'Jerusalem Talmud Maasrot 4:1:1'
VILNA_MAPPING['Jerusalem Talmud Maasrot 5, 20b'] = 'Jerusalem Talmud Maasrot 5:1:1'
VILNA_MAPPING['Jerusalem Talmud Moed Katan 2, 7a'] = 'Jerusalem Talmud Moed Katan 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Nedarim 8, 25b'] = 'Jerusalem Talmud Nedarim 8:1:1'
VILNA_MAPPING['Jerusalem Talmud Orlah 2, 8a'] = 'Jerusalem Talmud Orlah 2:1:1'
VILNA_MAPPING['Jקרודשךצ Tשךצוג Pesachim 3, 19a'] = 'Jerusalem Talmud Pesachim 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Pesachim 4, 24b'] = 'Jerusalem Talmud Pesachim 4:1:1'
VILNA_MAPPING['Jerusalem Talmud Sanhedrin 5, 23b'] = 'Jerusalem Talmud Sanhedrin 5:1:1'
VILNA_MAPPING['Jerusalem Talmud Sanhedrin 8, 41a'] = 'Jerusalem Talmud Sanhedrin 8:1:1'
VILNA_MAPPING['Jerusalem Talmud Sanhedrin 10, 48b'] = 'Jerusalem Talmud Sanhedrin 10:1:1'
VILNA_MAPPING['Jerusalem Talmud Shabbat 3, 20b'] = 'Jerusalem Talmud Shabbat 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Shabbat 7, 39b'] = 'Jerusalem Talmud Shabbat 7:1:1'
VILNA_MAPPING['Jerusalem Talmud Shabbat 8, 53b'] = 'Jerusalem Talmud Shabbat 8:1:1'
VILNA_MAPPING['Jerusalem Talmud Shekalim 4, 14b'] = 'Jerusalem Talmud Shekalim 4:1:1'
VILNA_MAPPING['Jerusalem Talmud Sheviit 7, 18a'] = 'Jerusalem Talmud Sheviit 7:1:1'
VILNA_MAPPING['Jerusalem Talmud Shevuot 7, 33a'] = 'Jerusalem Talmud Shevuot 7:1:1'
VILNA_MAPPING['Jerusalem Talmud Shevuot 3, 10b'] = 'Jerusalem Talmud Shevuot 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Yevamot 2, 9a'] = 'Jerusalem Talmud Yevamot 2:1:1'
VILNA_MAPPING['Jerusalem Talmud Yoma 5, 24a'] = 'Jerusalem Talmud Yoma 5:1:1'
VILNA_MAPPING['Jerusalem Talmud Kilayim 3, 12b'] = 'Jerusalem Talmud Kilayim 3:1:1'
VILNA_MAPPING['Jerusalem Talmud Niddah, 13a'] = 'Jerusalem Talmud Kilayim 4:6-7'

def del_trash(text):
    return text.replace('\ufeff', '').strip()

def parse_text(text, mas, com_name):
    tags = {'page': r'^(?:@\d\d|\d|\$|~|&)? ?\(? ?(?:דף|שם ע"ב|ע"ב)|^(?:@\d\d|\d|\$|~|&)\(?שם',
         'perek': r'^(?:@\d\d|\d|\$|~|&)(?:פרק |פ")([א-כ]"?[א-ט]?)(?: |\'|$)',
         'halakha': r'^(?:@\d\d|\d|\$|~|&)(?:הלכה |ה")([א-בד-וח-כ]"?[א-ט]?|[גז](?!.{10,}))(?: |\'|$)',
         'hadran': '^(?:@\\d\\d|\\d|\\$|~|&)(?:הדרן|סליק)'}
    text = del_trash(text)
    arrayed = [[[]]]
    comments = []
    perek = 1
    halakha = 0
    daf = 0
    amud = 0
    prev = False
    mid = False
    ordinals = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'ששי', 'שביעי', 'שמיני', 'תשיעי', 'עשירי', 'אחד עשר']
    ore_reg = '|'.join(ordinals)
    ordinals = {k: v for v, k in enumerate(ordinals, 1)}

    for line in text.split('\n'):
        line = ' '.join(line.split())
        line = re.sub("(.{,3}מתני'|גמ'):", r'\1', line)
        if not line:
            continue

        #perek
        perek_search = re.search(f'@\d\d.*?פרק ({ore_reg})$', line)
        if perek_search:
            perek = ordinals[perek_search.group(1)]
            if len(arrayed) < perek:
                arrayed += [[[]] for _ in range(perek-len(arrayed))]
            continue

        #halakha
        if re.findall(tags['halakha'], line):
            halakha = getGematria(re.findall(tags['halakha'], line)[0])
            if halakha == 5 and len(arrayed[-1]) == 7:
                halakha = 8
            elif halakha == 1 and arrayed[-1] != [[]]:
                arrayed += [[[]]]
                perek += 1
            if len(arrayed[-1]) + 1 == halakha:
                arrayed[-1] += [[]]
            elif len(arrayed[-1]) == 1 and halakha == 1:
                pass
            else:
                #print('*', perek, len(arrayed[-1]), halakha)
                arrayed[-1] += [[] for _ in range(halakha-len(arrayed[-1]))]
            line = re.split(tags['halakha'], line)[-1].strip()
            if len(line) < 4:
                prev = line.strip()
                continue

        #page
        if re.findall(tags['page'], line):
            line = line.replace('דף יו"ד', 'דף י')
            tag = re.findall(tags['page'], line)[0]
            if 'דף' in tag:
                page = re.findall('דף ([א-צ]"?\'?[א-ט]?) "?ע"*([אב])', line)
                if page:
                    page = page[0]
                    daf = getGematria(page[0])
                    amud = 'a' if page[1] == 'א' else 'b'
                else:
                    page = re.findall('דף ([א-צ]"?\'?[א-ט]?) ב?(מתני|גמ)', line)
                    if page:
                        temp_daf = getGematria(page[0][0])
                        if temp_daf != daf:
                            amud = 'a'
                        daf = temp_daf
                    else:
                        print('cant find page in page tag')
            elif 'ע"ב' in tag:
                amud = 'b'
            continue

        if re.search("^.{0,5}(?:גמ'|מתני')\.?$", line):
            prev = line.strip()
            continue

        if line:
            for comment in re.split('(?<=:)(?![^\(]*\))', line):
                comment = comment.strip()
                if not comment:
                    continue
                if mid:
                    comments[-1]['comment'] += f' {comment}'
                    mid = True if not comment.strip().endswith(':') and dh else False
                    continue

                if re.findall(tags['hadran'], comment):
                    dh = None
                else:
                    dh = ' '.join(comment.split()[:7])
                    dh = re.split("\.| פי'", dh)[0]
                    dh = re.sub('[^"\' א-ת]', '', dh)
                if prev:
                    comment = f'{prev.strip()} {comment}'
                    prev = False
                comments.append({'masechet': mas, 'commentary': com_name, 'perek': perek, 'halakha': halakha, 'page': f'{daf}{amud}', 'comment': comment, 'dh': dh})
                mid = True if not comment.strip().endswith(':') and dh else False

    return comments

def is_halakhot_nember_equal(comments):
    pereks = {com['perek'] for com in comments}
    fixed_halakhot = {}
    for perek in pereks:
        halakhot = {com['halakha'] for com in comments if com['perek'] == perek}
        last_halkha = max(halakhot)
        yer_halakhot = len(Ref(f'{YERUSHALMI} {comments[0]["masechet"]} {perek}').all_subrefs())
        fixed_halakhot[perek] = True if last_halkha == yer_halakhot else False
        if last_halkha != yer_halakhot:
            print('not equal halakhot', comments[0]["masechet"], perek, halakhot, yer_halakhot)
    return fixed_halakhot

def find_vilna_page(ref, page, mas):
    perek = 0
    pages = []
    try:
        return VILNA_MAPPING[f'{ref}, {page}']
    except KeyError:
        pass
    yer = YERUSHALMI
    alts = library.get_index(f'{yer} {mas}').alt_structs['Vilna']['nodes']
    if not ref.is_book_level():
        perek = int(ref.normal().split()[-1])
        alts = [alts[perek-1]]
    for p, alt in enumerate(alts):
        start = daf_to_section(alt['startingAddress'])
        for i, r in enumerate(alt['refs']):
            pages.append({'addr': section_to_daf(start+i), 'ref': r})
    addrs = set(p['addr'] for p in pages)
    for addr in addrs:
        refs = [p['ref'] for p in pages if p['addr'] == addr]
        if len(refs) == 0:
            page_ref = refs[0]
        else:
            page_ref = f'{refs[0].split("-")[0]}-{Ref(refs[-1]).all_segment_refs()[-1].normal().split()[-1]}'
        Ref(page_ref)
        VILNA_MAPPING[f'{ref}, {addr}'] = page_ref
    return VILNA_MAPPING[f'{ref}, {page}']

def find_ref(mas, perek, halakha, page):
    if perek:
        ref = Ref(f'{YERUSHALMI} {mas} {perek}')
    else:
        ref = Ref(f'{YERUSHALMI} {mas}')
    if page and page not in ['00', '0']:
        page_ref = find_vilna_page(ref, page, mas)
    elif halakha: #halakha w/o page
        return f'{mas} {perek}:{halakha}'
    else: #perek w/o page
        return ref
    if halakha: #halakha and page
        refs = unite_refs([r.normal() for r in ref.all_segment_refs() if r in Ref(page_ref).all_segment_refs()])
        if len(refs) != 1:
            print('problem with finding page', refs)
        if refs:
            return refs[0]
    else: #page q/o halakha
        return page_ref

def match_base(comments):
    has_halakha = True if 2 in [com['halakha'] for com in comments] else False
    has_perek = True if 2 in [com['perek'] for com in comments] or has_halakha else False
    has_page = True if any([com['page'] for com in comments]) else False
    if has_halakha:
        fixed_halakhot = is_halakhot_nember_equal(comments)
    mas = comments[0]['masechet']
    packs = []
    for com in comments:
        equal_halachot = True if com['perek'] and has_halakha and fixed_halakhot[com['perek']] else False
        if not packs:
            packs = [[com]]
        elif com['perek'] == perek and (com['halakha'] == halakha or not equal_halachot) and com['page'] == page:
            packs[-1].append(com)
        else:
            packs.append([com])
        perek, halakha, page = com['perek'], com['halakha'], com['page']
    for pack in packs:
        perek = pack[0]['perek'] if has_perek else None
        equal_halachot = True if perek and has_halakha and fixed_halakhot[perek] else False
        halakha = pack[0]['halakha'] if has_halakha and equal_halachot else None
        page = pack[0]['page'] if has_page else None
        gen_ref = find_ref(mas, perek, halakha, page)
        if type(gen_ref) != str:
            gen_ref = gen_ref.normal()
        gen_ref = gen_ref.replace('JTmock', YERUSHALMI)
        text = Ref(gen_ref).text('he', 'Mechon-Mamre')
        dhs = [com['dh'] for com in pack if com['dh']]
        if not text.text:
            print(f'no text for {gen_ref}')
            continue
        matches = match_ref(text, dhs, lambda x: x.split())['matches']
        for com in pack:
            if com['dh']:
                ref = matches.pop(0)
            com['base text ref'] = ref
    return [com for pack in packs for com in pack]

def match_between_refs(comments):
    prev, next = '', ''
    for i, com in enumerate(comments):
        if com.get('base text ref', None):
            prev = com['base text ref']
            next = ''
        else:
            if not next:
                for c in comments[i+1:]:
                    if c.get('base text ref', None):
                        next = c['base text ref']
                        break
            if prev == next:
                com['base text ref'] = prev
                com['match by context'] = 'X'
            elif re.search("^.{0,5}(?:גמ')\.?$", com['comment']) and next[-2:] == (':2'):
                com['base text ref'] = next
                prev = com['base text ref']
                com['match by context'] = 'X'
            elif re.search("^.{0,5}(?:מתני')\.?$", com['comment']) and next[-2:] in [':2', ':1']:
                com['base text ref'] = next[:-2] + ':1'
                prev = com['base text ref']
                com['match by context'] = 'X'
        if com.get('base text ref', None):
            com['base text'] = Ref(com['base text ref']).text('he', 'Mechon-Mamre').text
        else:
            com['base text'] = None
    return comments

if __name__ == '__main__':
    all = []
    for root, dirs, files in os.walk('data/'):
        for file in files:
            if 'docx' not in file:
                continue
            doc = Document(f'data/{file}')
            print(file)
            data = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            he_mas = file.split('הגרא')[1].split('.')[0].split('כתב יד')[0].strip()
            mas = Ref(he_mas).normal().split('Mishnah ')[1]
            if he_mas == 'פאה':
                data = data.replace('@22(דל"ד ע"ב)', '@22(דף ל"ד ע"ב)')
                data = re.sub('(@22\(דף \S*)\)', r'\1 ע"ב)', data)
            comments = parse_text(data, mas, 'Beur HaGra')
            comments = match_base(comments)
            to_add = match_between_refs(comments)
            for row in to_add:
                row['file'] = file
            all += to_add

    with open('gra.csv', 'w', encoding='utf-8', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=['file', 'masechet', 'commentary', 'perek', 'halakha', 'page', 'comment', 'dh',
                                                'base text ref', 'match by context', 'base text'])
        writer.writeheader()
        for row in all:
            writer.writerow(row)
    with open('vilna_mapping.json', 'w') as fp:
        json.dump(VILNA_MAPPING, fp)

