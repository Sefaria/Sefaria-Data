import json
import django
django.setup()
from sefaria.model import *
import csv
import os
import re
from sources.functions import getGematria
# from sources.Yerushalmi.yutil import OverlayBuilder
from sources.tosefta_scans.zuckermandel import unite_refs
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.utils.talmud import section_to_daf, daf_to_section
from docx import Document

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

def find_coms():
    with open('masechtot.csv', encoding='utf-8', newline='') as fp:
        data = csv.DictReader(fp)
        fields = data.fieldnames
        return {row['ירושלמי']: [f for f in fields if row[f].isdigit()] for row in data}

def get_details():
    with open('commentaries.csv', encoding='utf-8', newline='') as fp:
        return {row['he']: row for row in csv.DictReader(fp)}

def get_com_data(mas, com):
    with open('trans.csv', encoding='utf-8', newline='') as fp:
        trans = {row['he']: row['en'] for row in csv.DictReader(fp)}
    def transliter(letter):
        try:
            return trans[letter]
        except KeyError:
            if letter == ' ':
                return letter
            else:
                return ''

    # encom = ''.join([transliter(l) for l in com])
    # for root, dirs, files in os.walk('data/'):
    #     files = [file for file in files if mas in file]
    #     exact = [file for file in files if encom in file
    #              and (com!='עמודי ירושלים' or all(w not in file for w in ['btra', 'tnyna']))
    #              and (com!='ביאור הגר"א' or 'ktb' not in file)]
    #     if len(exact) == 0:
    #         regexes = ['h(fnym)', 'ry(dbz)', '(tws)fwt ryd', 'syy(ry )']
    #         for reg in regexes:
    #             encom = re.sub(reg, r'\1', encom)
    #         if encom == 'byawr hgra ktb yd':
    #             encom = 'ktb yd'
    #         encom = encom.replace('hghwt yfm', 'mhrm yfm')
    #         encom = encom.replace('hghwt rda', 'rda')
    #         encom = encom.replace('mhrm dy lwnzanw', ' lw')
    #         encom = encom.replace('chydwsy rag', 'ra_g')
    #         encom = encom.replace('mhra grydts', 'gry')
    #         exact = [file for file in files if encom in file]
    #         if len(exact) == 0:
    #             encom = encom.replace('mhrm yfm', 'mhrm yfym')
    #             encom = encom.replace('rda', 'rd_a')
    #             encom = encom.replace('ra_g', 'rag')
    #             encom = encom.replace(' lw', 'dylw')
    #             exact = [file for file in files if encom in file]
    # if len(exact) == 1:
    #     return open(f'data/{exact[0]}', encoding='utf-8').read()
    # elif len(exact) == 0:
    #     print(f'doesnt find com {com}-{encom} on {mas}. all files on masechet:', files)
    # else:
    #     print(f'more than on file for commentary {com} on {mas}:', exact)
    for root, dirs, files in os.walk('data/'):
        file = [file for file in files if mas in file][0]
        if '.doc' in file:
            doc = Document(f'data/{file}')
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            return open(f'data/{file}').read()

def find_tags(text):
    base_tag = r'^(?:@\d\d|\d|\$|~|&)'
    return {'page': '^(?:@\d\d|\d|\$|~|&)? ?\(? ?(?:דף|שם ע"ב)|^(?:@\d\d|\d|\$|~|&)\(?שם', 'perek': base_tag + '(?:פרק |פ")([א-כ]"?[א-ט]?)(?: |\'|$)',
            'halakha': base_tag + '(?:הלכה |ה")([א-בד-וח-כ]"?[א-ט]?|[גז](?!.{10,}))(?: |\'|$)', 'hadran': base_tag + '(?:הדרן|סליק)'}
    '''reg = r'[\d@#$%^&\*!\?\{\}]+'
    tags = set(re.findall(reg, text))
    for tag in tags:
        tag_re = re.escape(tag)
        if text.count(f'{tag}פרק') + text.count(f'{tag}פ"') > 3:
            perek_tag = tag
        elif text.count(f'{tag}הלכה') > 10:
            halakha_tag = tag
        elif text.count(f'{tag}דף') > 10:
            page_tag = tag
        elif len(re.findall(f'{tag_re}(?:הדרן|סליק)', text)) > 3:
            hadran_tag = tag
        else:
            if text.count(f'{tag}פרק')'''

def del_trash(text):
    return text.replace('\ufeff', '').strip()

def split_pages(text, tags):
    text = re.split(f'({tags["page"]})', text)
    '''if text[0].strip():
        print(text[0])'''
    text[1] = text[0] + text[1]
    text = [text[i] + text[i+1] for i in range(len(text)) if i % 2 != 0]

def parse_text(text, mas, com_name):
    tags = find_tags(text)
    text = del_trash(text)
    arrayed = [[[]]]
    comments = []
    perek = 1
    halakha = 0
    daf = 0
    amud = 0
    prev = False
    mid = False
    for line in text.split('\n'):
        line = ' '.join(line.split())
        line = re.sub("(.{,3}מתני'|גמ'):", r'\1', line)
        if not line:
            continue

        #perek
        if re.findall(tags['perek'], line):
            perek = getGematria(re.findall(tags['perek'], line)[0])
            if len(arrayed) < perek:
                arrayed += [[[]] for _ in range(perek-len(arrayed))]
            line = re.split(tags['perek'], line)[-1].strip()
            if len(line) < 4:
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
                    page = re.findall('דף ([א-צ]"?\'?[א-ט]?) ב?(מתני|גמ)', line)[0]
                    if page:
                        temp_daf = getGematria(page[0][0])
                        if temp_daf != daf:
                            amud = 'a'
                        daf = temp_daf
                    else:
                        print('cant find page in page tag')
                if '(' in tag:
                    if ')' in line[:25]:
                        line = line.split(')', 1)[1].strip()
                    else:
                        if len(line) < 20:
                            prev = line.strip()
                            continue
                        else:
                            print("problem with splitting line", line)
                else:
                    line = re.split(f'{tag} [א-צ]"?\'?[א-ט]? [^ ]*(?: |$)', line, 1)[1].strip()
            elif 'שם' in tag:
                if 'שם ע"ב' in line[:13]:
                    amud = 'b'
                if '(' in tag:
                    line = line.split(')', 1)[1].strip()
                else:
                    line = re.split(f'{tag}(?: [^ ]*(?: |$))?', line, 1)[1].strip()
            if len(line) < 10:
                prev = line.strip()
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

def find_vilna_page(ref, page):
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
    if page and page != '00':
        page_ref = find_vilna_page(ref, page)
    elif halakha: #halakha w/o page
        return f'{mas} {perek}:{halakha}'
    else: #perek w/o page
        return ref
    if halakha: #halakha and page
        refs = unite_refs([r.normal() for r in ref.all_segment_refs() if r in Ref(page_ref).all_segment_refs()])
        if len(refs) != 1:
            print('problem with finding page', refs)
        return refs[0]
    else: #page q/o halakha
        return page_ref

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
        matches = match_ref(text, dhs, lambda x: x.split())['matches']
        for com in pack:
            if com['dh']:
                ref = matches.pop(0)
            com['base text ref'] = ref
    return [com for pack in packs for com in pack]

def match_between_refs(comments):
    prev, next = '', ''
    for i, com in enumerate(comments):
        if com['base text ref']:
            prev = com['base text ref']
            next = ''
        else:
            if not next:
                for c in comments[i+1:]:
                    if c['base text ref']:
                        next = c['base text ref']
                        break
            if prev == next:
                com['base text ref'] = prev
            elif re.search("^.{0,5}(?:גמ')\.?$", com['comment']) and next[-2:] == (':2'):
                com['base text ref'] = next
                prev = com['base text ref']
                print(111, com)
            elif re.search("^.{0,5}(?:מתני')\.?$", com['comment']) and next[-2:] in [':2', ':1']:
                com['base text ref'] = next[:-2] + ':1'
                prev = com['base text ref']
                print(222, com)
        if com['base text ref']:
            com['base text'] = com['base text ref'].text('he', 'Mechon-Mamre').text
        else:
            com['base text'] = None
    return comments

def parse_com(com_name, mas, he_mas):
    com = coms_details[com_name]
    text = get_com_data(he_mas, com_name)
    comments = parse_text(text, mas, com_name)
    comments = match_base(comments)
    comments = match_between_refs(comments)
    return comments

if __name__ == '__main__':
    coms_map = find_coms()
    coms_details = get_details()
    indexes = [ind for ind in library.get_indexes_in_category('Yerushalmi') if 'Jerusalem Talmud' in ind]
    for ind in indexes:
        library.get_index(ind).versionState().refresh()
        mas = ind.replace(f'{YERUSHALMI} ', '')
        he_mas = library.get_index(ind).get_title('he').replace(f'{HEB_YER} ', '')
        print(he_mas)
        coms = coms_map[he_mas]
        for com_name in coms:
            if com_name not in coms_details:
                continue
            en_com = coms_details[com_name]['en']
            fname = f'csvs/{en_com}/{mas}.csv'
            '''if os.path.isfile(fname):
                continue'''
            if 'ביאור' not in com_name:
                continue
            print(com_name)
            comments = parse_com(com_name, mas, he_mas)

            try:
                os.mkdir(f'{os.getcwd()}/csvs/{en_com}')
            except FileExistsError:
                pass

            with open(fname, 'w', encoding='utf-8', newline='') as fp:
                writer = csv.DictWriter(fp, fieldnames=['masechet', 'commentary', 'perek', 'halakha', 'page', 'comment', 'dh', 'base text ref', 'base text'])
                writer.writeheader()
                for row in comments:
                    writer.writerow(row)

        with open('vilna_mapping.json', 'w') as fp:
            json.dump(VILNA_MAPPING, fp)


