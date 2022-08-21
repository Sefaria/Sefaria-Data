import re
import csv
from bs4 import BeautifulSoup
import django
django.setup()
from sefaria.model import *
from collections import OrderedDict

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
    breaks = [b[1].groups()[0] for b in breaks]
    roman = '^V?I{1,3}|I?V'
    letter = '^[a-j]'
    digit = '^\d'
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
    binyanim = ['Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    other = 'Plur'
    form = '|'.join(binyanim + [other])
    roman = 'V?I{1,3}|I?V'
    letter = '[a-j]'
    num = '\d'
    break_mark = f'(?:{roman}|{letter}|{num}|{form})'
    form = f'(?:{form})'
    roman = f'(?:{roman})'
    senses = []
    if not re.search(f'^†?{break_mark}\.?$', texts[0]):
        if len(texts) == 1:
            return texts[0]
        senses.append({'definition': texts[0]})
        texts.pop(0)

    regexes = set()
    if texts:
        for regex in [form, roman, num, letter]:
            if any(re.search(f'^†?{regex}\.?$', text) for text in texts):
                regexes.add(regex)
        for regex in [form, roman, num, letter]:
            if regex in regexes:
                texts = texts_to_dict(texts, f'^†?{regex}\.?$')
                for key in texts:
                    subsense = texts_to_senses(texts[key])
                    name = 'definition' if type(subsense) == str else 'senses'
                    sense = {name: subsense}
                    if '†' in key:
                        sense['all_cited'] = True
                    if key == '':
                        pass
                    elif regex == form:
                        sense['form'] = key.replace('†', '')
                    else:
                        sense['num'] = key.replace('†', '')
                    senses.append(sense)
                break
    return senses

def destroy_senses(senses):
    print(1, senses)
    for s in senses:
        if 'definition' in s:
            s['definition'] = ''
        else:
            s['senses'] = destroy_senses(s['senses'])
    return senses

def senses(text):
    text = ' '.join(text.replace('#xa7;', '§').split())
    if '#' in text:
        print('removing# in text', text)
        text = text.replace('#', '')
    text, stripped = strip_things(text)

    binyanim = ['Hithp', 'Poï1', 'Peï‘alï', 'Pil', 'Hithpa‘lēl', 'Pu', 'Hithpa', 'Hitph', 'Po‘al', 'Pōï‘', 'Hêphal', 'Pₑ‘îl', 'Hithpō‘l', 'Pe‘îl', 'Pō‘', 'Pilp', 'Haph', 'Pual', 'Poï‘ēl', 'Hithpe', 'Pôï‘lēl', 'Piï‘lēl', 'Hithpō‘', 'Pôl‘el', 'Hoph', 'Piïlel', 'Qal', 'Hilph', 'Hithpoïl', 'Pol', 'Po', 'Pilpēl', 'Poïlal', 'Poeï‘l', 'Poō‘lal', 'Ishtaph', 'Pa', 'Hithpo', 'Pōï‘l', 'Hothp', 'Hithpōl', 'Hithpōï‘', 'Po‘lal', 'Polel', 'Piel', 'Pi', 'Polp', 'Hithpoïlel', 'Ithpa', 'Po‘ēl', 'Poïlel', 'Hithpol', 'Paul', 'Nithp', 'Ithpe', 'Po‘el', 'Po‘l', 'Qa1', 'Hithpalp', 'Poïel', 'Pilïel', 'Shaph', 'Pie1', 'Niph', 'Po‘lel', 'Pe', 'Tiph', 'Hiph', 'Poï', 'Pōï‘al', 'Hiphp']
    roman = 'V?I{1,3}|I?V'
    letter = '[a-j]'
    num = '(?<!#)\d'
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
        return
    if breaks and not check_breaks(breaks):
        # if len(text) > 2200:
        #     print([b[1].groups()[0] for b in breaks])
        #     return True
        return

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
        for i, j in zip([0] + indexes, indexes + [-1]):
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

    text = str(soup).replace('&amp;', '$').replace('&lt;', '<').replace('&gt;', '>')
    text, _ = reloace_stripped(text, stripped)
    if '#' in text:
        print('failed to relocate', text)
    text = re.sub('† *%%%', '%%%†', text)
    text = text.strip()
    if text.endswith('%%%'):
        text = re.sub('%%%([^%]*)%%%$', r'\1', text)

    return texts_to_senses(text.split('%%%'))

if __name__ == '__main__':
    strongs = set()
    hebrew_binyanim = ['Poï‘lel', 'Pu', 'Pi', 'Piel', 'Hithpa', 'Pual', 'Qal', 'Hiph', 'Hithp', 'Hoph']
    aramaic_binyanim = ['Hithpe', 'Hithpa', 'Pa', 'Pō‘l', 'Hiph', 'Pō‘', 'Pe‘îl', 'Ishtaph', 'Hithpō‘l', 'Hêphal', 'Hoph', 'Hilph', 'Pₑ‘îl', 'Haph', 'Ithpa']
    for entry in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*?Dictionary'}}):
        # print(entry.headword)
        new = senses(entry.content['senses'][0]['definition'])
        if new:
            entry.content['senses'] = new
        entry.save()
