import django
django.setup()
import re
import json
from data_utilities.util import getGematria
from rif_utils import path, tags_map, maor_tags
from tags_fix_and_check import tags_by_criteria, save_tags
from tags_compare import compare_tags_nums, compare_tags, OrderedCounter
from sg_parser import check_sequence

def clean_garbage(string):
    return re.sub('\ufeff|\u200f', '', strung)

def bold(par):
    if '.' in par and 2 < len(par.split('.')[0]) < 100:
        par = '<b>' + par.replace('.', '.</b>', 1).strip()
    return par

def parse_pages(data, letter_tag):
    splitted = []
    lengths = []
    cou = 0
    for par in data:
        if letter_tag + 'א' in par and letter_tag + 'א]&' not in par:
            if cou:
                lengths.append(cou)
                splitted.append(page_text)
                letters_page = []
            cou = 1
            page_text = []
        else:
            cou += 1
        page_text.append(par)
    lengths.append(cou)
    splitted.append(page_text)
    return splitted, lengths

def nky_bmravad(mefaresh, masechet):
    with open(path+f'/commentaries/{mefaresh}_{masechet}.txt', encoding='utf-8') as fp:
        data = fp.read().replace('\xa0', ' ').replace('\ufeff', '')
    letter = '@11' if mefaresh == 'nky' else '@22'
    data = [letter + par for par in data.split(letter)[1:]]
    data, lengths = parse_pages(data, letter)
    num = 7 if mefaresh == 'nky' else 10
    tags = tags_by_criteria(masechet, value=lambda x: x['referred text']==num)
    newtags, counter = compare_tags_nums(tags, lengths, {}, num)
    tags.update(newtags)
    if len(counter) > 0:
        newdata = [[] for _ in range(max([int(page) for page in counter]) + 1)]
        for page in counter:
            newdata[int(page)] = data.pop(0)
    else:
        print('no pages in tags')
        return
    tags.update(compare_tags(tags, lengths, {}, num))
    save_tags(tags, masechet)
    try:
        check_sequence(newdata, letter)
    except UnboundLocalError:
        print('no newdata')

    newdata = [[re.sub(' +', ' ', re.sub('@11.\]|@|\d', '', par)).strip() for par in page] for page in newdata]
    if mefaresh == 'bmravad':
        newdata = [[bold(par) for par in page] for page in newdata]
    with open(path+f'/commentaries/json/{mefaresh}_{masechet}.json', 'w') as fp:
        json.dump(newdata, fp)

def ravad(masechet):
    with open(path+f'/commentaries/ravad_{masechet}.txt', encoding='utf-8') as fp:
        data = fp.read().replace('\xa0', ' ').replace('\ufeff', '')
    if masechet == 'Ketubot':
        pages = re.findall(r'השגות הראב"ד על הרי"ף מסכת כתובות דף ([א-ס]{1,2}) עמוד ([אב])\n\nהשגות הראב"ד על הרי"ף מסכת כתובות דף \1 עמוד \2', data)
        data = re.split(r'השגות הראב"ד על הרי"ף מסכת כתובות דף [א-ס]{1,2} עמוד [אב]\n\nהשגות הראב"ד על הרי"ף מסכת כתובות דף [א-ס]{1,2} עמוד [אב]', data)[1:]
    elif masechet in ['Gittin', 'Bava Kamma']:
        pages = re.findall('@66([א-נ]{1,2})([.:])', data)
        pages = [(page[0], 'א' if page[1] == '.' else 'ב') for page in pages]
        data = re.split('@66[א-נ]{1,2}[.:]', data)[1:]
    newdata = []
    for page in pages:
        section = getGematria(page[0]) * 2 + getGematria(page[1]) - 3
        while len(newdata) < section: newdata.append([])
        d_page = data.pop(0)
        if masechet == 'Ketubot':
            d_page = re.sub(' +', ' ', d_page.replace(':\n', ':<br>').replace('\n', ''))
            d_page = re.sub('(<br>) +', r'\1', d_page)
            d_page = d_page.split('@')
        elif masechet in ['Gittin', 'Bava Kamma']:
            d_page = re.sub(' +', ' ', d_page.replace(':', ':<br>').replace('\n', ''))
            d_page = re.sub('(<br>) +', r'\1', d_page)
            d_page = ['@11' + par for par in d_page.split('@11')[1:]]
        d_page = [par.strip() for par in d_page]
        d_page = [par[:-4] if par.endswith('<br>') else par for par in d_page]
        newdata.append(d_page)
    temp = newdata
    if masechet == 'Gittin':
        temp = [[par for par in page if re.findall(r'@11.\]', par)] for page in newdata]
    lengths = [len(page) for page in temp if page]
    tags = tags_by_criteria(masechet, value=lambda x: x['referred text']==9)
    tags.update(compare_tags(tags, lengths, {}, 9))
    if masechet == 'Ketubot':
        check_sequence(newdata, '^')
    save_tags(tags, masechet)

    newdata = [[re.sub(' +', ' ', re.sub('@|\d', '', par)).strip() for par in page] for page in newdata]
    newdata = [[bold(par) for par in page] for page in newdata]
    with open(path+f'/commentaries/json/ravad_{masechet}.json', 'w') as fp:
        json.dump(newdata, fp)

def efrayim_bk():
    with open(path+'/commentaries/R_Efrayim_Bava Kamma.txt', encoding='utf-8') as fp:
        data = fp.read().replace('\xa0', ' ').replace('\ufeff', '')
    data = [page.split('@22ב]') for page in data.split('@22א]')[1:]]
    tags = tags_by_criteria('Bava Kamma', value=lambda x: x['referred text']==8)
    lengths = [len(page) for page in data]
    newtags, counter = compare_tags_nums(tags, lengths, {}, 7)
    tags.update(newtags)
    if len(counter) > 0:
        newdata = [[] for _ in range(max([int(page) for page in counter]) + 1)]
        for page in counter:
            newdata[int(page)] = data.pop(0)
    else:
        print('no pages in tags')
    tags.update(compare_tags(tags, lengths, {}, 8))
    newdata = [[bold(par) for par in page] for page in newdata]
    save_tags(tags, 'Bava Kamma')

    newdata = [[re.sub(' +', ' ', re.sub('@|\d', '', par)).strip() for par in page] for page in newdata]
    with open(path+'/commentaries/json/R_Efrayim_Bava Kamma.json', 'w') as fp:
        json.dump(newdata, fp)

def execute():
    print('nky yevamot')
    nky_bmravad('nky', 'Yevamot')
    for masechet in ['Ketubot', 'Gittin', 'Bava Kamma']:
        print('ravad', masechet)
        ravad(masechet)
    print('r efrayim bk')
    efrayim_bk()
    for masechet in maor_tags:
        if maor_tags[masechet]['ravad in tag']:
            print('bm ravad', masechet)
            nky_bmravad('bmravad', masechet)

if __name__ == '__main__':
    execute()
