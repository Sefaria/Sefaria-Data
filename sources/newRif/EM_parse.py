import re
import json
from rif_utils import path, tags_map
from data_utilities.util import getGematria
from tags_fix_and_check import tags_by_criteria, save_tags, next_gem
from tags_compare import compare_tags_nums, compare_tags, OrderedCounter
from sg_parser import check_sequence
from sources.EinMishpat.ein_parser import parse_em

REPORT = []

def parse_em_pars(data, masechet):
    data = re.sub('\ufeff|\u200f', '', data)
    letter_tag = tags_map[masechet]['em_letter']
    data = [letter_tag + par for par in data.split(letter_tag)][1:]
    return data

def fix_file(string):
    replacing = [('פ"ק', 'פ"א'),
        ('טו?ח"מ', 'טור ח"מ'),
        ('טו?או?"ח', 'טור א"ח"'),
        ('טו?י"ד', 'טור י"ד'),
        ('טו?א"ה', 'טור א"ה'),
        ("מאכלו'", 'מאכלות'),
        ('יסודי תורה', 'יסודי התורה'),
        ('א"ת', 'א"ח'),
        ('א"ח"', 'א"ח'),
        ('א"כ', 'א"ח'),
        ('א"ח', 'טור א"ח'),
        ('טור טור', 'טור')]
    for a, b in replacing:
        string = re.sub(a, b, string)
    string = re.sub("עיי'? פ", "מיי' פ", string)
    string = re.sub(r'\([^\)]{1,5}\) \[([^\]]{1,5})\]', r'\1', string)
    return [line for line in string.split('@P') if line]

def find_refs(data):
    newdata = '@P'.join(['@P'.join(page) for page in data if page])
    newdata = fix_file(newdata)
    newdata = parse_em(f'EM', 1, 'emerrors.txt', em_list=newdata)
    mefarshim = ['Rambam', 'Semag', 'Tur Shulchan Arukh']
    newdata = [{mefaresh: item[mefaresh] if item[mefaresh] else [] for mefaresh in mefarshim} for item in newdata]
    for n, page in enumerate(data):
        if page:
            for m, _ in enumerate(page):
                data[n][m] = newdata.pop(0)
    return data

def execute():
    global REPORT
    for masechet in tags_map:
        if masechet == 'Nedarim': continue
        REPORT.append(masechet)
        with open(path+'/commentaries/EM_{}.txt'.format(masechet), encoding='utf-8') as fp:
            data = fp.read()
        page_tag = tags_map[masechet]['em_page']
        letter_tag = tags_map[masechet]['em_letter']
        tags = tags_by_criteria(masechet, value=lambda x: x['referred text']==6)
        unknowns = tags_by_criteria(masechet, key=lambda x:x[0]=='1', value=lambda x: x['referred text']==0 and x['style']==3)
        lengths = []

        if page_tag:
            data = data.split('@88')[1:]
            newdata = []
            for page in data:
                try:
                    daf, amud = re.search('^דף ([א-ס][א-ט]?) ע"([אב])', page).groups()
                    daf_num = getGematria(daf)
                    if amud == 'א': amud = 1
                    elif amud == 'ב': amud = 2
                    else: REPORT.append('amud isnt valid', page[:30])
                    section = daf_num * 2 - 3 + amud
                    while len(newdata) < section: newdata.append([])
                    page = re.sub('דף [א-ס][א-ט]? ע"[אב]', f'@88{daf}{"." if amud==1 else ":"}', page).strip()
                except (ValueError, AttributeError):
                    REPORT.append('daf and amud arent valid', page[:30])
                page = parse_em_pars(page, masechet)
                newdata.append(page)

            lengths = [len(page) for page in newdata if page != []]

        else:
            data = parse_em_pars(data, masechet)
            splitted = []
            cou = 0
            for par in data:
                if letter_tag + 'א' in par:
                    if cou:
                        lengths.append(cou)
                        splitted.append(page_text)
                    cou = 1
                    page_text = []
                else:
                    cou += 1
                page_text.append(par)
            lengths.append(cou)
            splitted.append(page_text)

            newtags, counter = compare_tags_nums(tags, lengths, unknowns, 1)
            tags.update(newtags)
            save_tags(tags, masechet)
            if len(counter) > 0:
                newdata = [[] for n in range(max([int(page) for page in counter]) + 1)]
                for page in counter:
                    newdata[int(page)] = splitted.pop(0)



        tags.update(compare_tags(tags, lengths, unknowns, 1))
        check_sequence(newdata, letter_tag)
        save_tags(tags, masechet)

        newdata = find_refs(newdata)

        with open(path+'/commentaries/json/EM_{}.json'.format(masechet), 'w') as fp:
            json.dump(newdata, fp)

if __name__ == '__main__':
    execute()
    print(REPORT)
