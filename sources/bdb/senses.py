import re
import csv
from bs4 import BeautifulSoup
import django
django.setup()
from sefaria.model import *
from collections import OrderedDict
from newdata_parser import rtl

MANUAL = []

def strip_things(text):
    num = 1
    stripped = {}
    while re.search('\([^\(\)]*\)', text):
        for occ in re.findall('\([^\(\)]*\)', text):
            key = f'#{num}'
            text = text.replace(occ, key, 1)
            stripped[key] = occ
            num += 1
    for occ in re.findall('sub\.? *<strong>[^<]*?</strong>', text):
        key = f'#{num}'
        text = text.replace(occ, key, 1)
        stripped[key] = occ
        num += 1
    for occ in re.findall('<strong>[^<]*?</strong> *infr\.?', text):
        key = f'#{num}'
        text = text.replace(occ, key, 1)
        stripped[key] = occ
        num += 1
    return text, stripped

def reloace_stripped(text, stripped):
    if type(text) == list:
        for i, t in enumerate(text):
            text[i], stripped = reloace_stripped(t, stripped)
    else:
        while '#' in text:
            for occ in re.findall('(#\d*)', text):
                text = re.sub(f'{occ}(?!\d)', stripped.pop(occ), text, 1)
    return text, stripped

def check_breaks(breaks):
    if not breaks:
        return True
    if type(breaks[0]) != str:
        breaks = [b[1].groups()[0] for b in breaks]
    roman = '^V?I{1,3}|I?V'
    letter = '^[a-j]'
    digit = '^\d\d?'
    let = fir_let = '`'
    num = fir_num = '0'
    rom = fir_rom = ''
    binyanim = []
    for br in breaks:
        br = br.replace('.', '')
        if re.search(roman, br):
            if num == '1' or let == 'a':
                return
            let = fir_let
            num = fir_num
            if br == rom + 'I' or rom == 'I' + br or (rom == 'III' and br == 'IV'):
                rom = br
            else:
                return
        elif re.search(digit, br):
            if let == 'a':
                return
            if int(br) != int(num) + 1:
                return
            let = fir_let
            num = br
        elif re.search(letter, br):
            if ord(br) != ord(let) + 1:
                return
            let = br
        else:
            if rom == 'I' or num == '1' or let == 'a':
                return
            rom = fir_rom
            let = fir_let
            num = fir_num
            binyanim.append(br)
    for bin in binyanim:
        if binyanim.count(bin) > 1:
            return
    if rom == 'I' or num == '1' or let == 'a':
        return
    return True

def texts_to_dict(texts, regex):
    if re.search(regex, texts[0]):
        dic = OrderedDict()
        key = None
    else:
        dic = OrderedDict({'': []})
        key = ''
    for text in texts:
        if re.search(regex, text):
            if key in dic and dic[key] == []:
                dic.pop(key)
                key = f'{key} {text}'
            else:
                key = text
            if key in dic:
                print('error. duplicate key', key, texts)
            dic[key] = []
        else:
            dic[key].append(text)
    return dic

def texts_to_senses(texts):
    texts = [text.strip() for text in texts]
    texts = [text for text in texts if text]
    binyanim = ['Poʿlel', 'Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    other = 'Plur'
    form = '|'.join(binyanim + [other])
    roman = 'V?I{1,3}|I?V'
    letter = '[a-j]'
    num = '\d\d?'
    break_mark = f'(?:{roman}|{letter}|{num}|{form})'
    form = f'(?:{form})'
    roman = f'(?:{roman})'
    sub = '(?:<sub>\d+</sub>)'
    senses = []
    if not re.search(f'^†?{break_mark}\.?{sub}?$', texts[0]):
        if len(texts) == 1:
            return [{'definition': texts[0]}]
        senses.append({'definition': texts[0]})
        texts.pop(0)

    regexes = set()
    if texts:
        for regex in [form, roman, num, letter]:
            if any(re.search(f'^†?{regex}\.?{sub}?$', text) for text in texts):
                regexes.add(regex)
        for regex in [form, roman, num, letter]:
            if regex in regexes:
                texts = texts_to_dict(texts, f'^†?{regex}\.?{sub}?$')
                for key in texts:
                    subsense = texts_to_senses(texts[key])
                    name = 'definition' if type(subsense) == str else 'senses'
                    sense = {name: subsense}
                    if '†' in key:
                        sense['all_cited'] = True
                    if '<sub>' in key:
                        sense['occurrences'] = re.findall('<sub>(\d+)</sub>', key)[0]
                    if key == '':
                        pass
                    elif regex == form:
                        sense['form'] = re.sub('<sub>\d+</sub>', '', key.replace('†', ''))
                    else:
                        sense['num'] = re.sub('<sub>\d+</sub>', '', key.replace('†', ''))
                    senses.append(sense)
                break
    return senses

def destroy_senses(senses):
    for s in senses:
        if 'definition' in s:
            s['definition'] = ''
        else:
            s['senses'] = destroy_senses(s['senses'])
    return senses

def senses(text):
    text = ' '.join(text.replace('#xa7;', '§').split())
    text = re.sub('(<span dir="rtl"> *)+', r'\1', text)
    text = re.sub('(</span> *)+', r'\1', text)

    if '#' in text:
        print('removing # in text', text)
        text = text.replace('&#', '')
    text, stripped = strip_things(text)

    binyanim = ['Poʿlel', 'Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    roman = 'V?I{1,3}|I?V'
    letter = '[a-j]'
    num = '(?<!#)\d\d?'
    other = 'Plur'
    break_mark = f'{roman}|{letter}|{num}|{other}'
    if text.startswith('vb.') or text.startswith('<strong>vb.'):
        break_mark += '|' + '|'.join(binyanim)
    break_mark = r'\b' + f'((?:{break_mark})\.?)(?: |$)'

    soup = BeautifulSoup(text, 'html.parser')
    strongs = soup.find_all('strong')
    breaks = []
    for s in strongs:
        if not isinstance(s.next, str):
            continue
        for b in re.finditer(break_mark, s.next):
            breaks.append([s, b])
    if breaks and not check_breaks(breaks):
        breaks = [b for b in breaks if 'f' not in b[1].groups()[0]]
    if breaks and not check_breaks(breaks):
        options = []
        for i in range(len(breaks)):
            temp = breaks[:]
            temp.pop(i)
            if check_breaks(temp):
                options.append(temp)
        if len(options) == 1:
            breaks = options[0]

    if not breaks:
        text, _ = reloace_stripped(text, stripped)
        if '#' in text:
            print('failed to relocate', text)
        return [{'definition': text}]
    if breaks and not check_breaks(breaks):
        for tag, match in breaks:
            tag.replace_with(soup.new_tag('br'), tag, soup.new_tag('br'))
        text = str(soup).replace('&amp;', '$').replace('&lt;', '<').replace('&gt;', '>')
        text, _ = reloace_stripped(text, stripped)
        text = re.sub('<br/?>', '\n', text)
        if '#' in text:
            print('failed to relocate', text)
        global MANUAL
        MANUAL.append(text)
        # if len(text) > 2200:
        #     print([b[1].groups()[0] for b in breaks])
        #     return True
        return False

    new_breaks = []
    for tag, match in breaks:
        if new_breaks and new_breaks[-1][0] == tag:
            new_breaks[-1][1].append(match)
        else:
            new_breaks.append([tag, [match]])
    for tag, matches in new_breaks:
        tagtext = str(tag.next)
        indexes = [i for match in matches for i in match.span(1)]
        new_texts = []
        for i, j in zip([0] + indexes, indexes + [None]):
            new_texts.append(tagtext[i:j])
        new = []
        for i, t in enumerate(new_texts):
            if t:
                if i % 2 == 0:
                    if t.strip():
                        new_tag = soup.new_tag('strong')
                        new_tag.string = t
                        new.append(new_tag)
                    else:
                        new.append(' ')
                else:
                    new.append(f'%%%{t}%%%')
        tag.replace_with(*new)

    text = str(soup).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text, _ = reloace_stripped(text, stripped)
    if '#' in text:
        print('failed to relocate', text)
    text = re.sub('† *%%%', '%%%†', text)
    text = text.strip()
    if text.endswith('%%%'):
        text = re.sub('%%%([^%]*)%%%$', r'\1', text)

    texts = text.split('%%%')
    for t, text in enumerate(texts):
        if text.startswith('<sub>'):
            texts[t-1] += re.findall('^<sub>\d+</sub>', text)[0]
            texts[t] = re.sub('^<sub>\d+</sub>', '', text)
    return texts_to_senses(texts)

def prepare_after_manual(text):
    texts = [t.strip() for t in text.split('\n')]
    binyanim = ['Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    roman = 'V?I{1,3}|I?V'
    letter = '[a-j]'
    num = '(?<!#)\d'
    other = 'Plur'
    break_mark = f'{roman}|{letter}|{num}|{other}'
    break_mark += '|' + '|'.join(binyanim)
    break_mark = f'(?:{break_mark})\.?'
    for i, text in enumerate(texts):
        texts[i] = re.sub(f'^<strong>({break_mark})</strong>', r'\1', text)
    return texts

def texts_to_senses_after_manual(texts, hw):
    binyanim = ['With other prepositions:—', 'With preps', 'Pl', 'Peʿîl', 'Hithpōʿ', 'Puʿl', 'Hithpōʿl', 'Pōʿl', 'Poʿlēl', 'Poʿlel', 'Poʿlal', 'Hithpoʿl', 'Pōʿ', 'Pōʿlēl', 'Pōʿlal', 'Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    form = '|'.join(binyanim)
    roman = '(?:Especially )?V?I{1,3}|I?V'
    letter = '(?:Especially )?†?[a-z]'
    caps = '[AB]'
    num = '(?<!#)(?:For |Sg. usually †|Hence )?\d\d?'
    break_mark = f'{roman}|{letter}|{num}|{caps}'
    break_mark += '|' + '|'.join(binyanim)
    break_mark = f'(?:{break_mark})'
    form = f'(?:{form})'
    roman = f'(?:{roman})'
    sub = '(?:<sub>\d+</sub>)'
    senses = []

    if not re.search(f'^†?{break_mark}\.?{sub}?$', texts[0]):
        if len(texts) == 1:
            return [{'definition': texts[0]}]
        senses.append({'definition': texts[0]})
        texts.pop(0)

    regexes = set()
    order = [form, caps, roman, num, letter]
    if hw == 'צָרַר':
        order = [caps, form, roman, num, letter]
    elif hw == 'לֵוִי²':
        order = [num, caps, letter]
    elif hw in ['בְּלִי', 'בַּ֫יִן']:
        order = [num, form, letter]
    elif hw == 'רָגַן':
        order = [num, form]

    if texts:
        for regex in order:
            if any(re.search(f'^†?{regex}\.?{sub}?$', text) for text in texts):
                regexes.add(regex)
        for regex in order:
            if regex in regexes:
                texts = texts_to_dict(texts, f'^†?{regex}\.?{sub}?$')
                for key in texts:
                    subsense = texts_to_senses_after_manual(texts[key], hw)
                    name = 'definition' if type(subsense) == str else 'senses'
                    sense = {name: subsense}
                    if '†' in key:
                        sense['all_cited'] = True
                    if '<sub>' in key:
                        sense['occurrences'] = re.findall('<sub>(\d+)</sub>', key)[0]
                    if key == '':
                        pass
                    elif regex == form:
                        sense['form'] = re.sub('<sub>\d+</sub>', '', key.replace('†', ''))
                    else:
                        if ' ' in key:
                            sense['pre_num'] = ' '.join(key.split()[:-1])
                        sense['num'] = re.sub('<sub>\d+</sub>', '', key.replace('†', '').split()[-1])
                    senses.append(sense)
                break
    return senses

def get_breaks(row):
    print(row['headword'])
    text = row['text']
    br = None
    dagger = False
    breaks = []
    texts = []
    binyanim = ['Peʿîl', 'Hithpōʿ', 'Puʿl', 'Hithpōʿl', 'Pōʿl', 'Poʿlēl', 'Poʿlel', 'Poʿlal', 'Hithpoʿl', 'Pōʿ', 'Pōʿlēl', 'Pōʿlal', 'Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    form = '|'.join(binyanim)
    roman = 'V?I{1,3}|I?V'
    letter = '[a-z]'
    caps = '[AB]'
    num = '(?<!#)\d\d?'
    break_mark = f'{roman}|{letter}|{num}|{caps}'
    break_mark += '|' + '|'.join(binyanim)
    for line in text.split('\n'):
        line = line.strip()
        nline = re.sub('</?strong>', '', line).strip()
        if not nline:
            continue
        if re.search(f'^†?(?:{break_mark})\.?$', nline):
            breaks.append(nline)
            if dagger:
                nline = '†' + nline
                dagger = False
            texts.append(nline)
            br = True
        else:
            if br == False:
                print('two not breaks line', row['headword'], line)
            br = False
            if line.endswith('†'):
                line = line[:-1].strip()
                dagger = True
            if line.startswith('<sub>'):
                if not re.search('^<sub>\d+</sub>', line):
                    print('problem with sub', line)
                else:
                    texts[-1] += re.findall('^<sub>\d+</sub>', line)[0]
                    line = re.sub('^<sub>\d+</sub>', '', line).strip()
                line = re.sub('^([^<]*</strong>)', r'<strong>\1', line)
                line = re.sub('(<strong>[^<]*)$', r'\1</strong>', line)
            texts.append(line)

    senses = texts_to_senses_after_manual(texts, row['headword'])
    # if breaks:
    #     if not check_breaks([x.replace('†', '') for x in breaks]):
    #         print(row['headword'], )#senses)

    return senses


if __name__ == '__main__':
    # strongs = set()
    # hebrew_binyanim = ['Poï‘lel', 'Pu', 'Pi', 'Piel', 'Hithpa', 'Pual', 'Qal', 'Hiph', 'Hithp', 'Hoph']
    # aramaic_binyanim = ['Hithpe', 'Hithpa', 'Pa', 'Pō‘l', 'Hiph', 'Pō‘', 'Pe‘îl', 'Ishtaph', 'Hithpō‘l', 'Hêphal', 'Hoph', 'Hilph', 'Pₑ‘îl', 'Haph', 'Ithpa']
    # with open('tens.txt') as fp:
    #     hws = fp.read().split('\n')
    # for headword in hws:
    #     for entry in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*?Dictionary'}, 'headword': headword}):
    #         print(entry.headword)
    #         new = senses(entry.as_strings()[0])
    #         print(new)
    #         if new:
    #             entry.content['senses'] = new
    #             entry.save()
    #         elif new == False:
    #             MANUAL[-1] = {'lexicon': entry.parent_lexicon, 'headword': entry.headword, 'rid': entry.rid, 'text': MANUAL[-1]}
    #
    # # the current file is in use!
    # with open('manual tens break.csv', 'w', newline='', encoding='utf-8') as fp:
    #     w = csv.DictWriter(fp, fieldnames=['lexicon', 'headword', 'rid', 'text'])
    #     w.writeheader()
    #     for row in MANUAL:
    #         w.writerow(row)

    # after manual
    import sys
    csv.field_size_limit(sys.maxsize)
    # with open('manual break fixed.csv', newline='', encoding='utf-8') as fp:
    #     new = list(csv.DictReader(fp))
    # with open('manual break.csv', newline='', encoding='utf-8') as fp:
    #     old = list(csv.DictReader(fp))
    with open('manual tens break.csv', newline='', encoding='utf-8') as fp:
        new = list(csv.DictReader(fp))
    # for rn, ro in zip(new, old):
    #     na_tags = re.findall('<a[\s\S]*?</a>', rn['text'])
    #     oa_tags = re.findall('<a.*?</a>', ro['text'].replace('\n', ''))
    #     if len(na_tags) != len(oa_tags):
    #         print('different a tags number', rn['headword'], ro['headword'], len(na_tags), len(oa_tags))
    #         for x in range(len(na_tags)):
    #             if na_tags[x] != oa_tags[x]:
    #                 print(x, na_tags[x], oa_tags[x])
    #     new_pieces = re.split('<a[\s\S]*?</a>', rn['text'])
    #     new_pieces = [rtl(re.sub('<span dir="rtl">|</span>', '', x)) for x in new_pieces]
    #     if len(new_pieces) != len(oa_tags) + 1:
    #         print(8888)
    #     result = [None] * (len(new_pieces) + len(oa_tags))
    #     result[::2] = new_pieces
    #     result[1::2] = oa_tags
    #     rn['text'] = ''.join(result).replace('$', '&')
    #     rn['text'] = re.sub('(<span dir="rtl"> *)+', r'\1', rn['text'])
    #     rn['text'] = re.sub('(</span> *)+', r'\1', rn['text'])

    for row in new:
        hw = row['headword']
        if row['headword'] == 'עָפְרָה':
            hw = 'עְפִרָה'
        entry = LexiconEntry().load({'parent_lexicon': row['lexicon'], 'headword': hw, 'rid': row['rid']})
        entry.content['senses'] = get_breaks(row)
        if row['headword'] == 'עָפְרָה':
            entry.headword = 'עָפְרָה'
        entry.save()
