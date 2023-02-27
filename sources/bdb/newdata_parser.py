from bs4 import BeautifulSoup
import re
import csv
from itertools import chain
import django
django.setup()
from sefaria.model import *

def open_file(file_name):
    with open(file_name) as fp:
        return fp.read()

def find_ref(child):
    books_dict = {
        'Dt': 'Deu',
        'Le': 'Lev',
        'Eze': 'Ezekiel',
        '2Ki': '2 Kings',
        '1Ki': '1 Kings',
        'Zec': 'Zechariah',
        'Is': 'Isaiah',
        'Na': 'Nahum',
        'Am': 'Amos',
        'Ge': 'Gen',
        '2Sa': '2 Samuel',
        '1Sa': '1 Samuel',
        'Je': 'Jeremiah',
        'Joe': 'Joel',
        'Pr': 'Proverbs',
        'La': 'Lamentations',
        'Ho': 'Hosea',
        'Ne': 'Nehemiah',
        'Es': 'Ester',
        'Nu': 'Numbers',
        'Zep': 'Zephaniah',
        'Ru': 'Ruth',
        'So': 'Song of Songs',
        'Da': 'Daniel',
        'Ec': 'Ecclesiastes',
        'Ob': 'Obadiah 1',
        'Sir': 'Ben Sira',
        '1Mac': 'The Book of Maccabees I (Kahana Translation)',
        '2Mac': 'II Macc.',
    }

    ref = re.sub('(.)(\d)', r'\1 \2', child['data-reference'], 1)
    ref = ref.replace('Dt', 'Deu').replace('Jn 4.4', 'Joshua 4.4')
    ref = re.sub('[^\d]*$', '', ref)
    if ref.split()[0] in ['Mk', 'Lk', 'Mt', '1Jn', 'Re', 'Ac', 'Ro', 'Jo', 'Ju', '2Pe', '1Pe', 'Tob', 'Tt', 'Eph',
                          'Jas', '1Co', 'Jn', 'LetJer', 'Heb', 'Jas', 'Jud', 'PsSol', 'Php']:
        return
    try:
        ref = Ref(ref)
    except:
        try:
            book = ref.split()[0]
            ref = Ref(ref.replace(book, books_dict[book]))
        except:
            print(111111, ref, child.string)
    return ref

def parse_entry(file_name):

    string = open_file(file_name)
    soup = BeautifulSoup(string, 'html.parser')
    new = {'text': '', 'strong_numbers': [], 'GK': [], 'TWOT': [], 'fn': file_name.split('.')[0].split('/')[1].replace(':', '.')}
    rtl = False
    concord = False

    strong = lambda child: (child.span and 'style' in child.span.attrs and 'bold' in child.span['style']) or ('style' in child.attrs and 'bold' in child['style']) or child.name=='strong'
    em = lambda child: child.name == 'em'
    sup = lambda child: ('style' in child.attrs and ':super;' in child['style']) or (child.span and 'style' in child.span.attrs and ':super;' in child.span['style'])
    sub = lambda child: ('style' in child.attrs and ':sub;' in child['style']) or (child.span and 'style' in child.span.attrs and ':sub;' in child.span['style'])
    dir = lambda child: 'style' in child.attrs and 'direction:rtl' in child['style']
    transc = lambda child: 'class' in child.attrs and child['class'] == ['lang-x-tl'] and ':italic;' in child['style']
    bibleref = lambda child: 'class' in child.attrs and child['class'] == ['bibleref']
    bdbref = lambda child: 'href' in child.attrs and 'books/bdb/article/LBDB.' in child['href']
    oldtransc = lambda child: 'class' in child.attrs and child['class'] == ['lang-x-tl']
    styles = [strong, em, sup, sub, dir, transc, bibleref, bdbref]

    for p in soup.find('div', class_='resourcetext').find_all('p'):
        if not p.name:
            new['text'] += f'{child}'
            continue
        for child in p.children:
            if not child.name:
                new['text'] += f'{child}'
                if concord:
                    concord = False
                continue
            if 'data-content' in child.attrs and any(x in child['data-content'] for x in ["Strong’s Concordance", 'Theological Wordbook of the Old Testament', 'Goodrick/Kohlenberger numbering system of the']):
                concord = True
                continue
            if 'style' not in child.attrs or ':super;' not in child['style']:
                concord = False
            if sum([1 if f(child) else 0 for f in styles]) > 1:
                fs = [styles.index(f) for f in styles if f(child)]
                if fs not in [[2,6],[0,5],[3,5],[2,5], [2,4], [0,2],[0,2,5],[0,4]]:
                    print(11111, child)
                    print(new['text'][:500])
                    print(fs, new['fn'])
            if 'class' in child.attrs and child['class'] == ['lang-sam']:
                new['sam'] = True
            if 'href' in child.attrs and 'HebrewStrongs' in child['href']:
                new['strong_numbers'] += list(child.strings)
                concord = new['strong_numbers']
            elif 'href' in child.attrs and 'TWOT.TWOT_No' in child['href']:
                new['TWOT'] += list(child.strings)
                concord = new['TWOT']
            elif 'href' in child.attrs and 'HebrewGK.HGK' in child['href']:
                new['GK'] += list(child.strings)
                concord = new['GK']
            elif sub(child) and bibleref(child):
                ref = find_ref(child)
                if ref:
                    new['text'] += f'<sup><a data-ref="{ref.normal()}" href="/{ref.url()}">{"".join(child.strings)}</a></sup>'
                else:
                    new['text'] += f'<sup>{"".join(child.strings)}</sup>'
            elif sup(child) and dir(child):
                new['text'] += f'<sup><span dir="rtl">{"".join(child.strings)}</span></sup>'
            elif sup(child) and strong(child) and oldtransc(child):
                new['text'] += f'<strong><sup>{"".join(child.strings)}</sup></strong>'
            elif dir(child):
                # if rtl:
                #     new['text'] += f'<span dir="rtl">{"".join(child.strings)}</span>'
                # else:
                #     rtl = True
                new['text'] += "".join(child.strings)
            elif strong(child): #should be before transc
                new['text'] += f'<strong>{"".join(child.strings)}</strong>'
                # if child.name == 'strong' and child.attrs:
                #     print('strong with attrs', child)
            elif em(child):
                # if child.attrs:
                #     print('em with attrs', child)
                new['text'] += f'<em>{"".join(child.strings)}</em>'
            elif sup(child) or (sub(child) and oldtransc(child)): #should be before sub and transc (transc for 2 reasons) - ad hoc
                if concord:
                    concord += [x for x in child.strings if x != ',']
                else:
                    new['text'] += f'<sup>{"".join(child.strings)}</sup>'
            elif sub(child):
                new['text'] += f'<sub>{"".join(child.strings)}</sub>'
            elif transc(child):
                new['text'] += f'<transc>{"".join(child.strings)}</transc>'
            elif bibleref(child):
                ref = find_ref(child)
                if ref:
                    if ref.context_ref() == Ref('Exodus 20'):
                        if len(ref.toSections) > 1:
                            v = int(ref.toSections[1])
                            if 13 < v < 17:
                                v = 13
                            elif v > 16:
                                v -= 3
                            ref = Ref(f'Exodus 20:{v}')
                    if ref.context_ref() == Ref('Deuteronomy 5'):
                        if len(ref.toSections) > 1:
                            v = int(ref.toSections[1])
                            if 17 < v < 21:
                                v = 17
                            elif v > 20:
                                v -= 3
                            ref = Ref(f'Deuteronomy 5:{v}')
                    if ref.context_ref() == Ref('Nehemiah 7'):
                        if len(ref.toSections) > 1:
                            v = int(ref.toSections[1])
                            if v > 20:
                                v -= 1
                            ref = Ref(f'Nehemiah 7:{v}')
                    if ref.normal() == 'Numbers 25:19':
                        ref = Ref('Numbers 26:1')
                    new['text'] += f'<a data-ref="{ref.normal()}" href="/{ref.url()}">{"".join(child.strings)}</a>'
                else:
                    new['text'] += "".join(child.strings)
            elif bdbref(child):
                ref = re.findall('books/bdb/article/LBDB\.(\d+\.\d+)$', child['href'])[0]
                new['text'] += f'<a data-ref="BDB{ref}" href="/BDB{ref}">{"".join(child.strings)}</a>'
            else:
                new['text'] += "".join(child.strings)

    new['text'] = re.sub('\(<transc>.*?</transc>\)', '', new['text'])
    new['text'] = re.sub('<transc>(.*?)</transc>', r'<em>\1</em>', new['text'])

    new['text'] = re.sub(' (</[^>]*>)', r'\1 ', new['text'])
    new['text'] = re.sub('(<[^/>]+>) ', r' \1', new['text'])
    new['text'] = ' '.join(new['text'].split())
    new['text'] = re.sub(r'</([^>]*)>( ?)<\1>', r'\2', new['text'])
    new['text'] = re.sub(r'<([^>]*)>( ?)</\1>', r'\2', new['text'])
    new['text'] = re.sub('</span><span dir="rtl">', '', new['text'])
    new['text'] = re.sub(r'<([^ >]*)([^>]*)>([^<]*)</\1>( ?)<\1\2>([^<]*)</\1>', r'<\1\2>\3\4\5</\1>', new['text'])
    new['text'] = new['text'].replace('||', '‖').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    new['text'] = re.sub(' ([,.:;\)\]])', r'\1', new['text'])
    new['text'] = re.sub('([\(\[]) ', r'\1', new['text'])

    new['text'] = re.sub(r'(<a data-ref="BDB[^>]*>)([^<]*)</a>( *)\1', r'\1\2\3', new['text'])

    if not new['text']:
        print(soup)
    # print(new['text'])
    # print(new)
    return new

def remove_non_hebrew(string):
    return re.sub(r'[^\u0590-\u05f5 ]', '', string)

def split_sub(hw):
    hw, occur = hw.split('<sub>')
    occur = occur.split('</sub>')[0].strip()
    return hw.strip(), occur

def find_hw(text):
    text = text.replace('\u200d', '')
    hebrew_sequnce = '\\u0590-\\u05f5'
    hebrew = '[\\u0590-\\u05f5 ]'
    dagger = '(?:† ?)'
    double = '(?:‡ ?)'
    num = '(?:i. & ii.|1?[Ii]*[Vv]?I*\.*)'
    nums = f'(?:{num},? ?)*'
    reg = f'^{double}?{dagger}?{nums}?{dagger}?\[? ?{dagger}? ?(?:<strong>)?[א-ת\(]'
    hw = re.findall(reg, text)
    if not hw:
        print('problem with headword', text[:150])
        return
    hw = hw[0]
    ret_dict = {}
    if '‡' in hw:
        ret_dict['peculiar'] = True
        text = text.replace('‡', '', 1).strip()
    if '†' in hw:
        ret_dict['all_cited'] = True
        text = text.replace('†', '', 1).strip()
    nums = [n.strip() for n in re.findall(nums, hw) if n.strip()]
    if nums:
        text = text.replace(nums[0], '', 1)
        ret_dict['ordinal'] = nums[0].upper().replace('1', 'I').strip()
    if 'strong' in hw:
        text = text.replace('<strong>', '', 1).replace('</strong>', '', 1)
    text = ' '.join(text.split())
    if len(text.split()) < 2:
        print('entry is too short', text)
        return
    if '[' in hw:
        in_bra = text.split('[')[1].split(']')[0]
        if len(in_bra.split()) > 10 or len(in_bra.split()) == 1 or ']' in text.split()[0] or ']' not in text:
            ret_dict['brackets'] = 'first_word'
        else:
            ret_dict['brackets'] = 'all'
            text = text.split(']')[1]
            if re.search('[a-z\?]', in_bra):
                ret_dict['headword'], appendix = re.split(f'({hebrew}+)', in_bra, 1)[1:]
                ret_dict['headword_suffix'] = re.sub(f'({hebrew}+)', r'<span dir="rtl">\1</span>', appendix) #dont strip
                if ret_dict['headword'].endswith(' '):
                    ret_dict['headword_suffix'] = f" {ret_dict['headword_suffix']}"
                ret_dict['headword_suffix'] = re.sub('<span dir="rtl"> +', ' <span dir="rtl">', ret_dict['headword_suffix'])
                ret_dict['headword_suffix'] = re.sub(' +', ' ', ret_dict['headword_suffix'])
            else:
                in_bra = remove_non_hebrew(in_bra)
                ret_dict['headword'], alt_headwords = in_bra.split(None, 1)
                ret_dict['alt_headwords'] = [{'word': w} for w in alt_headwords.split()]
            if '<sub>' in ret_dict['headword']:
                ret_dict['headword'], ret_dict['occurrences'] = split_sub(ret_dict['headword'])
            if 'alt_headwords' in ret_dict:
                for alt in ret_dict['alt_headwords']:
                    if 'sub' in alt['word']:
                        alt['word'], alt['occurrences'] = split_sub(alt['word'])
            if re.search(f'^<sub>', text):
                ret_dict['occurrences'] = re.findall('^<sub>(.*?)</sub>', text)[0]
                text = re.sub('^<sub>.*?</sub>', '', text)
            return ret_dict, text
    ret_dict['headword'], text = text.split(None, 1)
    text = text.strip()
    while (re.search(f'{hebrew}$', ret_dict['headword']) or ret_dict['headword'].endswith(')')) and (re.search(f'^{hebrew}', text) or re.search(f'^<sub>', text)):
        tomove, text = text.split(None, 1)
        ret_dict['headword'] += f' {tomove}'
        text = text.strip()
    ret_dict['headword'] = re.sub('[\[\],]', '', ret_dict['headword'])
    if '<sub>' in ret_dict['headword']:
        ret_dict['headword'], ret_dict['occurrences'] = split_sub(ret_dict['headword'])
    if re.search(f'^ *{hebrew}', text):
        alt_headwords, text = re.split(f'((?:[{hebrew_sequnce}, ](?: *<sub>[^<]*?</sub>)?)+)', text, 1)[1:]
        # print(alt_headwords, 11111, text[:50], ret_dict)
        ret_dict['alt_headwords'] = [{'word': w.replace(',', '')} for w in alt_headwords.split()]
        for alt in ret_dict['alt_headwords']:
            if 'sub' in alt['word']:
                alt['word'], alt['occurences'] = split_sub(alt['word'])
            alt['word'] = remove_non_hebrew(alt['word'])
    text = text.strip()
    return ret_dict, text

FN_DICT = {}

def handle_vlinks(text):
    for ref in re.findall('<a data-ref="BDB(.*?)" href="/BDB.*?">', text):
        hw = FN_DICT[ref]
        lex = 'BDB' if float(ref) < 2258.44 else 'BDB Aramaic'
        text = re.sub(f'(<a data-ref=")BDB{ref}(" href="/)BDB.*?(">)', r'\1{}, {}\2{},_{}", dir="rtl\3'.format(lex, hw, lex, hw), text)
    return text

def parens(text):
    if text in ['מָטָר))', 'הֵבִיא אֶל־))']:
        return text[:-2]
    opens = text.count('(')
    closes = text.count(')')
    bopens = text.count('[')
    bcloses = text.count(']')
    if text.endswith(')'):
        if opens == closes - 1:
            return text[:-1]
        else:
            if opens != closes:
                print('no balance in parens', text)
            return text
    if text.endswith(']'):
        if bopens == bcloses - 1:
            return text[:-1]
        else:
            if bopens != bcloses:
                print('no balance in parens', text)
            return text
    if text.startswith('('):
        if opens - 1 == closes:
            return text[1:]
        else:
            if opens != closes:
                print('no balance in parens', text)
            return text
    if text.endswith('['):
        if bopens - 1 == bcloses:
            return text[1:]
        else:
            if bopens != bcloses:
                print('no balance in parens', text)
            return text
    if text.count('(') != text.count(')'):
        print('no balance in parens', text)
    return text

def fix_semitics(texts):
    new = []
    remain = ''
    for t, text in enumerate(texts):
        if t // 2 == t / 2:
            new.append(f'{remain}{text}')
            remain = ''
        else:
            if (len(re.findall('[\[\(]', text)) != len(re.findall('[\]\)]', text))) or (re.search('^[\(\{]', text) and re.search('\]\)$', text)):
                to_add = re.split('( *[\[\]\(\)]+ *)', text)
                to_add = [x for x in to_add if x]
                if re.search('[\[\]\(\)]', to_add[0]):
                    new[-1] += to_add.pop(0)
                new += to_add[:-1]
                if re.search('[\[\]\(\)]', to_add[-1]):
                    remain = to_add[-1]
                else:
                    new.append(to_add[-1])
            else:
                new.append(text)
    if len(new) % 2 != len(texts) % 2:
        print(55555, new, texts)
    return new

def rtl(text):
    text = text.replace('ܢܶܟ̄ܣܶܐ', 'ܢܶܟܵܣܶܐ')
    arabic_block = range(1536, 1792)
    heb_block = range(1424, 1525)
    samaritan_block = range(2048, 2111)
    syr_block = range(1792, 1872)
    semitic_letter = ''.join([chr(x) for x in chain(arabic_block, heb_block, syr_block)]) + '̱'
    semitic_start = semitic_letter + '\[\('
    semitic_end = semitic_letter + "'\]\)'"
    semitic_space = semitic_letter + " \[\('\]\)—\-"
    text = re.split('(<a .*?</a>)', text)
    for ind in range(0, len(text), 2):
        hebs = re.split(f'([{semitic_start}][{semitic_space}]*[{semitic_end}]|{semitic_letter}(?![^{semitic_letter}]))', text[ind])
        hebs = fix_semitics(hebs)
        for i in range(1, len(hebs), 2):
            hebs[i] = f'<span dir="rtl">{parens(hebs[i])}</span>'
        text[ind] = ''.join(hebs)
        #this is the old way"
        # for x in re.findall(f'([{semitic_start}][{semitic_space}]*[{semitic_end}])', text[ind]):
        #     x = parens(x)
        #     text[ind] = re.sub(f'({re.escape(x)})', r'<span dir="rtl">\1</span>', text[ind], 1)

    # syr_space = syr_block + ' '
    # for ind in range(0, len(text), 2):
    #     for x in re.findall(f'([{syr_block}][{syr_space}]*[{syr_block}])', text[ind]):
    #         text[ind] = re.sub(f'({re.escape(x)})', r'<span dir="rtl">\1</span>', text[ind])
    text = ''.join(text)
    for x, y in [('<span dir="rtl">בִּן־נוּן (ישׁוע</span>, <span dir="rtl">הושׁע) יהושׁע)</span>', '<span dir="rtl">יהושׁע (הושׁע, ישׁוע) בִּן־נוּן</span>)'),
                 ('((سوج', '(سوج'),
                 ('<span dir="rtl">((فور)</span>, <span dir="rtl">فَارَ</span>)', '<span dir="rtl">(فور)</span>, <span dir="rtl">فَارَ</span>')]:
        text = text.replace(x, y)
    return text

def parse_lang(lang):
    start = 1 if lang == 'heb' else 2258
    end = 2259 if lang == 'heb' else 2542
    y = 0 if lang == 'heb' else 43
    headwords = []
    entries = []
    rid = 1
    global FN_DICT
    for x in range(start, end):
        while True:
            if lang == 'heb' and x == 2258 and y == 43:
                break
            # if x == 1795 and y == 1:
            #     y += 1
            #     continue #does not exist in original bdb
            fn = f'{x}:{y}.html'
            # if fn not in ['1494:9.html', '2292:0.html']: continue
            try:
                entry = parse_entry(f'newdata/{fn}')
            except FileNotFoundError:
                y = 0
                break
            # print(fn)
            # if fn=='1902:0.html':
            #     print(11111, entry['text'])
            entry['rid'] = 'BDB' + str(rid).zfill(5) if lang == 'heb' else 'BDBA' + str(rid).zfill(4)
            rid += 1
            new, entry['text'] = find_hw(entry['text'])
            entry['parent_lexicon'] = 'BDB Dictionary' if lang == 'heb' else 'BDB Aramaic Dictionary'
            entry.update(new)
            entry['headword'] = entry['headword'].strip()
            entry['headword'] = re.sub('\.$', '', entry['headword'])
            print(entry['headword'])
            headwords.append(entry['headword'])
            chw = headwords.count(entry['headword'])
            if chw > 1:
                entry['headword'] += ''.join(dict(zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")).get(c) for c in str(chw))
            FN_DICT[fn.split('.')[0].replace(':', '.')] = entry['headword']
            if (y == 0 and len(entry['headword']) > 1) or (x == 1490 and y ==8):
                entry['root'] = True
            if entries: #ARAMAIC
                entry['prev_hw'] = entries[-1]['headword']
                entries[-1]['next_hw'] = entry['headword']

            entries.append(entry)
            # print(new, entry['fn'])
            # print(entry['text'])
            y += 1

    bad_refs = []
    for e in entries:
        if 'Hagga2.22' in e['text']: print(9, e['fn'])
        bads = []
        for ref in re.findall('href="/(?:<sup>)?([^<]*?)["<]', e['text']):
            if 'BDB' in ref:
                continue
            if not Ref(ref.replace('_', ' ')).text('he').text:
                bads.append(ref)
        if bads:
            bad_refs.append({'rid': e['rid'], 'headword': e['headword'], 'text': e['text'], 'bad refs': bads})
    with open(f'bad refs {lang}.csv', 'w', newline='', encoding='utf-8') as fp:
        w = csv.DictWriter(fp, fieldnames=['rid', 'headword', 'text', 'bad refs'])
        w.writeheader()
        for x in bad_refs:
            w.writerow(x)

    return entries

def ref_sups():
    with open('asups.csv') as fp:
        data = list(csv.DictReader(fp))
    for row in data:
        pl = 'BDB Dictionary' if len(row['rid']) == 6 else 'BDB Aramaic Dictionary'
        le = LexiconEntry().load(({'parent_lexicon': pl, 'headword': row['hw']}))
        if not le:
            # print(pl, row['rid'], row['hw'])
            continue
        text = le.content['senses'][0]['definition'].strip()
        prev = re.escape(f'{row["prevprev"]}')
        if not prev.endswith('strong>'):
            prev += re.escape(row["prev"])
        if not re.search('strong> *$', prev):
            prev = re.sub(r'(\\ *)$', r'</strong>\1', prev, 1)
        ref = re.escape(row['sup'].strip())
        sups = re.findall(f'{prev} *<a[^>]*>{ref}</a>', text)
        if len(sups) == 1:
            le.content['senses'][0]['definition'] = re.sub(f'({prev}) *(<a[^>]*>{ref}</a>)', r'\1<sup>\2</sup>', text)
            le.save()

def samaritan():
    with open('samaritan - samaritan.csv') as fp:
        data = list(csv.DictReader(fp))
    for row in data:
        les = LexiconEntrySet({'headword': row['headword'], 'rid': row['rid']})
        if len(les) != 1:
            print(1111)
            continue
        le = les[0]
        text = le.content['senses'][0]['definition']
        sams = re.findall('(.{,10})(?:<span dir="rtl">)?~(.*?)~(?:</span>)?(.{,10})', row['text'])
        if not sams:
            print(1.5, row['headword'])
        for before, sam, after in sams:
            before, after = re.escape(before), re.escape(after)
            if len(sam) > 10:
                print(2222, sam)
            matches = re.findall(f'{before}(?:<span dir="rtl">)?.*?(?:</span>)?{after}', text)
            if len(matches) != 1:
                print(3333)
            new = ''.join(dict(zip("אבגדהוזחטיכלמנסעפצקרשת", "ࠀࠁࠂࠃࠄࠅࠆࠇࠈࠉࠊࠋࠌࠍࠎࠏࠐࠑࠒࠓࠔࠕ")).get(c, c) for c in sam)
            text = re.sub(f'({before})(?:<span dir="rtl">)?.*?(?:</span>)?({after})',
                          r'\1<span dir="rtl">{}</span>\2'.format(new), text)
        le.content['senses'][0]['definition'] = text
        # print(le.content['senses'][0]['definition'])
        le.save()


def parse():
    entries = parse_lang('heb')
    entries += parse_lang('ara')
    samaritanl = []
    for e in entries:
        e['quotes'] = []
        e['text'] = handle_vlinks(e['text'])
        e['text'] = rtl(e['text'])
        if 'sam' in e:
            e.pop('sam')
            samaritanl.append({'headword': e['headword'], 'rid': e['rid'], 'text': e['text'], 'parent': e['parent_lexicon'],
                              'url': f'bdb.cauldron.sefaria.org/{"BDB Aramaic" if "Aramaic" in e["parent_lexicon"] else "BDB"}, {e["headword"]}'})
        e['content'] = {'senses': [{'definition': e.pop('text')}]}
        e.pop('fn')
        e = LexiconEntry(e)
        e.save()
    ref_sups()
    samaritan()
    with open('samaritan.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['parent', 'headword', 'rid', 'text', 'url'])
        w.writeheader()
        for row in samaritanl:
            w.writerow(row)

if __name__ == '__main__':
    parse()

