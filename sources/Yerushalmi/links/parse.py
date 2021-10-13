import json
import sys

import django
django.setup()
from sefaria.model import *
import tabula
import os
import pandas as pd
import numpy as np
import re
from data_utilities.util import is_abbr_of
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.system.exceptions import InputError
from sources.tosefta_scans.create_objects import unite_refs
from sources.functions import getGematria
from sources.Yerushalmi.yutil import OverlayBuilder
import json
import cProfile
import sys

COLUMNS = ['בבלי', 'מקבילות', "ספ' תנאים", 'מקרא', "תח' ציטוט", "מקום בירו'"]
Y, N, M, F, G = 0, 0, 0, 0, 0
try:
    with open('mappings.json') as fp:
        MAPPINGS = json.load(fp)
except FileNotFoundError:
    MAPPINGS = {}
yer = 'ירושלמי דמע'


def update_json(links):
    try:
        with open('links.json') as fp:
            links += json.load(fp)
    except FileNotFoundError:
        pass
    with open('links.json', 'w') as fp:
        json.dump(links, fp)
    return []

def open_file(fname):
    return tabula.read_pdf(f'pdfs/{fname}', pages='all')

def open_file_csv(fname):
    return pd.read_csv(f'csvs/{fname}')

def open_csv():
    masechtot = {}
    df = pd.read_csv('bad_tables_fix.csv')
    if list(df.columns) != COLUMNS + ['masechet']:
        print('csv has the columns', df.columns)
    for index, row in df.iterrows():
        if row['masechet'] and not pd.isna(row["masechet"]) and not row['masechet'].isdigit():
            mas = row['masechet']
            masechtot[mas] = pd.DataFrame(columns=COLUMNS)
        else:
            row = row.drop('masechet')
            masechtot[mas] = masechtot[mas].append(row)
    return masechtot

def unite_empties(df):
    #takes rows where the loc is empty and wnite them with the previous row
    new = pd.DataFrame(columns=COLUMNS)
    for index, row in df.iterrows():
        if not pd.isna(row["מקום בירו'"]) and not re.search(r'^\(\d\d$', row["מקום בירו'"]):
            if not row["תח' ציטוט"]:
                _, row["מקום בירו'"], row["תח' ציטוט"] = re.split('(^.*?\d,) ', row["מקום בירו'"])
            new = new.append(row)
        else:
            for column in COLUMNS:
                if all(not pd.isna(x) for x in [row[column], new[column].iloc[-1]]) and 'Unnamed' not in row[column]:
                    new[column].iloc[-1] = f'{new[column].iloc[-1].strip()} {row[column].strip()}'
                elif pd.isna(new[column].iloc[-1]) and not pd.isna(row[column]):
                    new[column].iloc[-1] = row[column].strip()
    return new

def change_columns(df):
    #convert the headres to a row under the regular headers
    return pd.DataFrame(np.vstack([df.columns, df]), columns=COLUMNS)

def find_book_abbr(abbr, books):
    return [book for book in books if is_abbr_of(abbr, book)]

def get_book(book, cat, more_books=[]):
    if book in ['עמוד', 'מקום']:
        return
    to_del = library.get_term(cat).get_titles('he')[0]
    if book == "גט'" or book == "גטין":
        book = "גיט'"
    if book == "קד'":
        book = "קיד'"
    if book == "נד'":
        book = "נדר'"
    if book == "זב'":
        book = "זבח'"
    if book == "ער'":
        book = "עיר'"
    if book == "כל'":
        book = "כלא'"
    if book == "מכ'":
        book = "מכש'"
    if book == "תמ'":
        book = "תמו'"
    if book == "מע'":
        book = "מעש'"
    books = library.get_indexes_in_category(cat, full_records=True)
    if cat == 'Bavli':
        books = books[:-14]
    books = find_book_abbr(book, [re.sub(f'{to_del} |תלמוד ', '', index.get_title('he')) for index in books]+more_books)
    if len(books) != 1:
        #print(f'for {book} found books: {books}in {cat}')
        return ''
    return books[0]

def check_ref(ref, text=None):
    try:
        if ref and Ref(ref).text('he').text:
            return True
    except InputError:
        pass
    #if text:
        #print(f'invalid ref "{ref}" for text "{text}"')
    return False

def accurate_ref(text, ref):
    global F,G
    if not text:
        G+=1
        return ref
    ver = 'Wikisource Talmud Bavli' if Ref(ref).is_bavli() else 'Mishnah, ed. Romm, Vilna 1913' if 'Mishnah' in ref else 'Mechon-Mamre' if 'JTmock' in ref else None
    if 'Minor Tractates' in Ref(ref).index.categories:
        ver = None
    match = match_ref(Ref(ref).text('he', ver), [text], base_tokenizer=lambda x: re.sub('[^א-ת ]', '', x).split()
                      , word_threshold=0.55, char_threshold=0.52)["matches"][0]
    if match:
        F+=1
        return match.tref
    else:
        G+=1
        return ref

def fix_text(text):
    if 'Unnamed' in text:
        return ''
    text = re.sub(r"ה ?ש'|b\ע' ", '', text)
    text = re.sub('" ', '"', text)
    return ' '.join(text.split())

def find_zuckermandel(ref):
    with open('../../tosefta_scans/mapping.json') as fp:
        mapping = json.load(fp)
    refs = []
    ref = Ref(ref).normal().split()
    trac = ' '.join(ref[:-1])
    try:
        ch, hal = ref[-1].split(':')
    except ValueError:
        #print(f'error ref: {ref}')
        return []
    for key, value in mapping.items():
        if trac in key:
            fir_ch, fir_hal, las_ch, las_hal = re.split('[:-]', value)
            if (ch == fir_ch and int(hal) >= int(fir_hal)) or (fir_ch < ch < las_ch) or (ch == las_ch and int(hal) <= int(las_hal)):
                refs.append(key)
    return unite_refs(refs)

def get_refs_for_book(book, text, reg):
    return [re.sub('[^א-ת \)\(\-]', '', f'{book} {occur}') for occur in re.findall(reg, text)]

def misnah_and_tosefta(text):
    refs = []
    for book, mas, loc in re.findall("([מת])'? ([^ ]*) ([^ ]*,? [^ ]*)", text):
        book = 'Mishnah' if book == 'מ' else 'Tosefta'
        if mas == 'כלים' and book == 'Tosefta':
            mas, loc = re.findall(f"ת'? כלים ([^ ]*) ([^ ]*,? [^ ]*)", text)[0]
            mas = f'כלים {get_book(mas, book)}'.replace('בבא ', '')
        else:
            mas = get_book(mas, book)
        book = library.get_term(book).get_titles('he')[0]
        ref = re.sub('[^א-ת \-]', '', f'{book} {mas} {loc}')
        if book == 'תוספתא':
            try:
                Ref(re.sub('[^א-ת \)\(\-]', '', f'{book} {mas} (ליברמן)'))
                ref = re.sub('[^א-ת \)\(\-]', '', f'{book} {mas} (ליברמן) {loc}')
            except InputError:
                try:
                    ref = ref.split('-')[0]
                    refs += find_zuckermandel(ref)
                except (KeyError, InputError):
                    #print(f'problem with ref "{ref}" on text "{text}"')
                    pass
                continue
        refs.append(ref)
    return refs

def get_all_chapters_alts(perek):
    ob = OverlayBuilder('Guggenheimer (structured)', 'Venice Columns', '', '', '')
    yerushalmi_chapters = Ref(perek.book).all_subrefs()
    latest_addr = None
    pereks = []
    for yc in yerushalmi_chapters:
        pereks.append(ob.getAddressRangesForPerek(yc, latest_addr))
        latest_addr = pereks[-1][-1]["addr"]
    return pereks

def find_halakha(loc, mas):
    halakha = re.findall('^[^ ]* ([א-ל]{1,2}(?:, | ,)[א-כ]{1,2})', loc)
    if halakha:
        halakha = re.sub('[^א-ת ]', '', halakha[0])
        try:
            halakha = Ref(f'{yer} {mas} {halakha}')
            return halakha  #.top_section_ref() why i did it?
        except InputError:
            print('input error', loc)
            return Ref(f'{yer} {mas}')
    else:
        return Ref(f'{yer} {mas}')

def find_page(mas, loc, halakha):
    loc = fix_text(loc)
    if not halakha:
        return
    perek = halakha.top_section_ref() if not halakha.is_book_level() else halakha
    page_reg = '\(([א-פ][א-י]? ע"[א-ד])' if halakha.normal() != Ref(f'{yer} {mas}').normal() else '^[^ ]* ([א-פ][א-י]? ע"[א-ד])'
    page = re.findall(page_reg, loc)
    if page:
        page = page[0]
    else:
        print('no page', loc, halakha.normal(), page_reg, Ref(f'{yer} {mas}').normal(), halakha.normal()==Ref(f'{yer} {mas}').normal(), len(halakha.normal()), len(Ref(f'{yer} {mas}').normal()))
        return
    try:
        return MAPPINGS[mas][f'{page}, {perek}']
    except KeyError:
        pass
    daf, amud = page.split()
    daf = getGematria(daf)
    amud = chr(getGematria(amud[-1]) + 96)
    page = f'{daf}{amud}'
    pereks = get_all_chapters_alts(perek)
    if not perek.is_book_level():
        pereks = [pereks[int(perek.normal().split()[-1])-1]]
    matches = []
    for per in pereks:
        for p in per:
            if page == p['addr']:
                matches.append(p)
    if not matches:
        print(f'doesnt find page {page} in {mas}')
        return
    try:
        MAPPINGS[mas]
    except KeyError:
        MAPPINGS[mas] = {}
    MAPPINGS[mas][f'{page}, {perek}'] = f'{matches[0]["start"].tref}-{matches[-1]["end"].tref.split()[-1]}'
    return f'{matches[0]["start"].tref}-{matches[-1]["end"].tref.split()[-1]}'

def get_yerushalmi(emas, loc, start=None, page=None):
    loc = fix_text(loc)
    mas = get_book(loc.split()[0].replace("ביכ'", "בכורי'").replace('גט', 'גיט'), 'Yerushalmi')
    if page:
        ref = Ref(page)
    else:
        halakha = find_halakha(loc, mas)
        ref = find_page(mas, loc, halakha)
        if ref:
            ref = Ref(ref)
        else:
            return
    if not ref.text('he').text:
        if page:
            return None, None
        else:
            return
    if start:
        ops = []
        for seg in ref.all_segment_refs():
            textv = re.sub('[^א-ת ]', '', seg.text('he', 'Venice Edition').text)
            textg = re.sub('[^א-ת ]', '', seg.text('he').text)
            start = re.sub('[^א-ת ]', '', start)
            if re.findall(f'\\b{start}\\b', textv) or re.findall(f'\\b{start}\\b', textg):
                ops.append(seg)
                words = re.split(f'\\b{start}\\b', textv, 0)[1] if re.findall(f'\\b{start}\\b', textv) else re.split(f'\\b{start}\\b', textg, 1)[1]
        if len(ops) == 0:
            ops = match_ref(ref.text('he'), [start], base_tokenizer=lambda x: re.sub('[^א-ת ]', '', x).split(),
                      word_threshold=0.2, char_threshold=0.2)
            if not ops['matches'] or not ops['matches'][0]:
                return None, None
            words = ops['match_text'][0][0]
            seg_text = ops['matches'][0].text('he').text
            if type(seg_text) == list:
                seg_text = ' '.join(seg_text)
            seg_text = re.sub('[^א-ת ]', '', seg_text)
            words = ' '.join(words.split())
            seg_text = ' '.join(seg_text.split())
            words = re.split(f'\\b{words}\\b', seg_text, 1)[1]
            ops = ops['matches']
        if len(ops) > 1:
            return None, None
        else:
            return ops[0], f'{start} {words}'
    return ref.normal()

def tanakh(text):
    heb = '[א-ת]'
    refs = []
    if pd.isna(text) or not text:
        return []
    text = re.sub('^(.) +', r'\1', text)
    text = fix_text(text)
    text = re.sub('^(.) +', r'\1', text)
    text = text.replace('תהלים', 'תהילים').replace('שיר השירים', 'שה"ש')
    while text:
        book = get_book(text.split()[0], 'Tanakh', ['Ben Sira'])
        if book:
            text = ' '.join(text.split()[1:])
            loc = re.findall(f'^({heb}*), ({heb}*)(?:\s|$)', text)
            if loc:
                ch, vr = loc[0]
                ref = f'{book} {ch} {vr}'
                if check_ref(ref):
                    refs.append(ref)
                    text = ' '.join(text.split()[2:])
                    continue
        break
    return refs

def tanaitic(text):
    refs = []
    if pd.isna(text) or not text:
        return []
    text = fix_text(text)
    text = text.replace('מדר ', 'מדר')
    if text:
        refs += misnah_and_tosefta(text)
        for book, reg in [('ספרי במדבר', '(?:ס"ב|ספרי במ[^ ]*) ([^ ]*)'), ('ספרי דברים', '(?:ס"ד|ספרי דב[^ ]*) ([^ ]*)'),
                          ('סדר עולם', 'ס"ע ([^ ]*)'), ("שמ' ([^ ]* [^ ]*)", 'מסכת שמחות'), ('ב"ס ([^ ]* [^ ]*)', 'בן סירא')]:
            refs += get_refs_for_book(book, text, reg)
    new = []
    for ref in refs:
        if check_ref(ref):
            new.append(ref)
    return new

def parallel(text):
    refs = []
    if pd.isna(text) or not text:
        return []
    text = fix_text(text)
    if text:
        #yerushalmi
        for yer in re.findall(r'[^, ]{1,} [^ ]+?, [^ ]* \)[^ ]* ע"[א-ד] \(\d', text) + re.findall(r'[^ ;\)\(]+ [^ \)\(]+ ע"[א-ד]', text): #TODO find also refs after ;
            mas = yer.split()[0].replace("ביכ'", "בכורי'").replace('גט', 'גיט')
            if mas == 'שם' or mas == 'דף':
                continue
            mas = get_book(mas, 'Yerushalmi').replace('בכורי', 'ביכורי')
            if not mas:
                continue
            mas = Ref(mas).normal().replace('Mishnah ', '')
            refs.append(get_yerushalmi(mas, yer))
        #rabba
        for occur in re.findall('([^ ]*?"ר) ([^ ]* [^ ]*)', text):
            book = get_book(occur[0].replace('ב"ר', 'בר"ר'), 'Midrash Rabbah')
            loc = re.sub(r"[^\-א-ת ]", "", occur[1])
            if book:
                refs.append(f'{book}, {loc}')
        for reg, book in [("שמ(?:'|חות) ([^ ]* [^ ]*)", 'מסכת שמחות'), ("כות(?:'|ים) ([^ ]* [^ ]*)", 'מסכת כותים'),
                          ("כלה ([^ ]* [^ ]*)", 'מסכת כלה'), ("סופ'? ([^ ]* [^ ]*)", 'מסכת סופרים'), ("עבדים ([^ ]* [^ ]*)", 'מסכת עבדים'),
                          ('ד"א ([^ ]* [^ ]*)', 'מסכת דרך ארץ זוטא'), ('דא"ר ([^ ]* [^ ]*)', 'מסכת דרך ארץ רבה'),
                          ('מת"ה ([^ ]* [^ ]*)', 'מדרש תהילים'), ('תנ"ב ([^ ]* [^ ]*)', 'תנחומא בובר'),
                          ('תנ"ו ([^ ]* [^ ]*)', 'תנחומא'), ('ס"ע ([^ ]*)', 'סדר עולם'),
                          ('פס"ר ([^ ]*)', 'פסיקתא רבתי'), ('פד"א ([^ ]*)', 'פרקי דרבי אליעזר'),
                          ('אדר"נ (נו"א [^ ]*|[^ ]* נו"א)', 'אבות דרבי נתן')]:
            refs += get_refs_for_book(book, text, reg)
    new = []
    for ref in refs:
        if not ref:
            continue
        ref = ref.replace(' נוא', '')
        if 'תנחומא' in ref:
            ref = re.sub('(תנחומא(?: בובר)?)', r'\1,', ref).replace('חוקת', 'חקת').replace('תשא', 'כי תשא').replace('אחרי', 'אחרי מות').replace('לך', 'לך לך')
        if check_ref(ref, text):
            new.append(ref)
    return new

def bavli(text):
    refs = []
    if pd.isna(text) or not text:
        return []
    text = fix_text(text)
    if text:
        for book, loc in re.findall(r'([^ ]*) ([^ ]* ע"[אב])', text):
            book = get_book(book, 'Bavli')
            if book:
                refs.append(f'{book} {loc}')
    new = []
    for ref in refs:
        if check_ref(ref, text):
            new.append(ref)
    return new

def refresh_vstates():
    for fname in os.listdir('csvs'):
        mas = fname[:-4]
        Ref(f'JTmock {mas}').index.versionState().refresh()

def check_sequence(rows):
    for a, b in zip(rows[:-1], rows[1:]):
        if b['ref'].follows(a['ref']):
            print('sequence problem {} found on {} but {} found on {}'.format(a["row"]["תח\' ציטוט"], a["ref"], b["row"]["תח\' ציטוט"], b["ref"]))

if __name__ == '__main__':
    #refresh_vstates()
    links = []
    try:
        with open('done.json') as fp:
            done = json.load(fp)
    except FileNotFoundError:
        done = []
    '''for fname in os.listdir('pdfs'):
        pages = open_file(fname)
        mas = fname[:-4].replace("'", '').replace('Q', 'K').replace('q', 'k').replace('Ha', 'Cha').replace('Bez', 'Beitz').replace('Mez', 'Metz').replace('ubb', 'ub').replace(' Cha', ' Ha')
        print(mas)
        report = ''
        csv_data = open_csv()
        pages += [csv_data[mas]]
        report += f'{mas}\n'
        Ref(f'Jerusalem Talmud {mas}')
        for page in pages:
            if list(page.columns) != COLUMNS:
                if len(page.columns) != 6:
                    report += f'{page.to_csv()}\n\n'
                    continue
                page = change_columns(page)
            page = unite_empties(page)
            refs = []
            for index, row in page.iterrows():'''
    with open('rep.txt', 'w') as fp:
        fp.write('hi')
    for fname in os.listdir('csvs'):
        df = open_file_csv(fname)
        mas = fname[:-4]
        if mas in done:
            continue
        print(mas)
        Ref(f'JTmock {mas}').index.versionState().refresh()
        try:
            MAPPINGS[mas]
        except KeyError:
            MAPPINGS[mas] = {}

        #sort df to pages
        pages = {}
        for index, row in df.iterrows():
            hmas = get_book(row["מקום בירו'"].split()[0].replace("ביכ'", "בכורי'").replace('גט', 'גיט'), 'Yerushalmi')
            ref = find_halakha(row["מקום בירו'"], hmas)
            page = find_page(hmas, row["מקום בירו'"], ref)
            try:
                pages[page].append(row)
            except KeyError:
                pages[page] = [row]

        for page in pages:
            '''for row in pages[page]:
                if re.findall(r'\d+', row["מקום בירו'"])[0] == '':
                    print(row["מקום בירו'"])'''
            rows = sorted(pages[page], key=lambda x: int(re.findall(r'\d+', x["מקום בירו'"])[0]))
            newpage = []
            for row in rows:
                yer_ref, yer_text = get_yerushalmi(mas, row["מקום בירו'"], row["תח' ציטוט"], page)
                newpage.append({'ref': yer_ref, 'text': yer_text, 'row': row})
            succes = len([r for r in newpage if r['ref']])
            while len(newpage) != succes:
                start, end = 0, 0
                for i, item in enumerate(newpage):
                    if item['ref']:
                        start = item['ref']
                    else:
                        for row in newpage[i+1:]:
                            if row['ref']:
                                end = row['ref']
                                break
                        if start and end:
                            ref = f'{start.normal()}-{end.normal().split()[-1].split("-")[-1]}'
                            try:
                                ref = Ref(ref)
                            except InputError:
                                print('problem with ref', start, end)
                                continue
                        elif start:
                            ref = start
                        elif end:
                            ref = end
                        else:
                            continue
                        newref, newtext = get_yerushalmi(mas, item['row']["מקום בירו'"], item['row']["תח' ציטוט"], ref.tref)
                        if newref:
                            newpage[i]['ref'], newpage[i]['text'] = newref, newtext
                        elif len(ref.all_segment_refs()) < 4:
                            newpage[i]['range'] = ref
                if len([r for r in newpage if r['ref']]) == succes:
                    break
                succes = len([r for r in newpage if r['ref']])
            Y+=succes
            N+=(len(newpage)-succes)
            check_sequence([[r for r in newpage if r['ref']]])

            for row in newpage:
                yer_ref, yer_text = row['ref'], row['text']
                refs = []
                if not yer_ref:
                    try:
                        yer_ref, yer_text = row['range'], None
                    except KeyError:
                        continue
                row = row['row']
                refs += tanakh(row['מקרא'])
                refs += tanaitic(row["ספ' תנאים"])
                refs += parallel(row['מקבילות'])
                refs += bavli(row['בבלי'])
                for ref in refs:
                    if (not Ref(ref).is_segment_level() or '-' in ref) and yer_text:
                        ref = accurate_ref(yer_text, Ref(ref).normal())
                    links.append({'refs': [yer_ref.normal(), Ref(ref).normal()],
                                 'type': '',
                                  'auto': True,
                                  'generated_by': 'yerushalmi tables'})
                if sys.getsizeof(links) > 10**4:
                    links = update_json(links)

        with open('mappings.json', 'w') as fp:
            json.dump(MAPPINGS, fp)
        done.append(mas)
        with open('done.json', 'w') as fp:
            json.dump(done, fp)
    update_json(links)

    print(Y,N,M)
    print(F,G)
    print(len(links))
    #with open('bad_tables.csv', 'w', encoding='utf-8', newline='') as fp:
    #    fp.write(report)
