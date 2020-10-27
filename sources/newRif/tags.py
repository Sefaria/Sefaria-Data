import re
import csv
import json
import django
django.setup()
from functools import partial
from collections import Counter
from sources.functions import getGematria
from sefaria.utils.talmud import daf_to_section, section_to_daf
from rif_utils import tags_map, remove_meta_and_html, path, maor_tags

def sort_tags(tags_list):
    return sorted(tags_list, key=lambda x: True if any(s not in x for s in '@#*') else False)
    #untaged tags should be in the end for searching the real tags first, e.g. searching @68(a) before (a)

def identify_tag(actual_tag: str, reg_tags: list):
    for tag in sort_tags(reg_tags):
        if re.search(f'^{tag}$', actual_tag): return tag

def rif_tokenizer(string, masechet):
    return remove_meta_and_html(string, masechet).split()

def mefaresh_tokenizer(string):
    return re.sub(r'\(.\)|\[.\]| [א-ת] |<[^>]*>', ' ', string).split()

def check_duplicate(d1, d2):
    if set(d1) & set(d2) != set():
        print(f'duplicate tags {set(d1) & set(d2)}')

def paragraph_tags(text: str, regex: str, id6dig: str, tokenizer=lambda x: x.split(), word_range=5):
    #word range is safe to adjust
    tags_dict = {}
    n = 0
    new_par = 9900
    while re.search(regex, text):
        id8dig = id6dig + str(n).zfill(2)
        a, b = re.split(regex, text, 1)
        change_page = re.findall(r'%-?\d{1,2}%', b[:5]) #that marks the tag should be moved to another page
        if change_page:
            new_p = int(id8dig[1:4]) + int(change_page[0][1: -1]) #1:-1 because of the % signs
            id8dig = id8dig[0] + str(new_p).zfill(3) + str(new_par)  #9900 or more for identifying
            new_par += 1
            b = re.sub(r'%-?\d{1,2}%', '', b, 1)
        a, b = tokenizer(a), tokenizer(b)
        context = ' '.join(a[-word_range:] + b[:word_range])
        word_index = len(a)
        tags_dict[id8dig] = {'word_index': word_index, 'context': context, 'original': re.search(regex, text).group()}
        text = re.sub(regex, f' ${id8dig} ', text, 1)
        n+=1
    return text, tags_dict

def page_tags(page: list, reg_tags: list, id4dig: str, tokenizer=lambda x: x.split()):
    new_page, tags_dict, tags_count = [], {}, Counter(reg_tags)
    regex = '|'.join(sort_tags(reg_tags))
    for n, par in enumerate(page):
        id6dig = f'{id4dig}{str(n).zfill(2)}'
        text, tags = paragraph_tags(par, regex, id6dig, tokenizer=tokenizer)
        new_page.append(text)
        for value in tags.values():
            tag = identify_tag(value['original'], reg_tags)
            value['num_in_page'] = tags_count[tag]
            tags_count[tag] += 1
        check_duplicate(tags_dict, tags)
        tags_dict.update(tags)
    return new_page, tags_dict

def rif_tags(masechet):
    with open(f'{path}/rif_gemara_refs/rif_{masechet}.csv', encoding='utf-8', newline='') as fp:
        rows = list(csv.DictReader(fp))
        data = []
        last_page = daf_to_section(rows[-1]['page.section'].split(':')[0])
        for n in range(last_page):
            data.append([row['content'] for row in rows if row['page.section'].split(':')[0] == section_to_daf(n+1)])
    mefarshim_tags = {tags_map[masechet]['Shiltei HaGiborim']: 1,
        tags_map[masechet]['Chidushei An"Sh']: 2,
        tags_map[masechet]['Bach on Rif']: 3,
        tags_map[masechet]['Hagaot Chavot Yair']: 4,
        tags_map[masechet]['Hagaot meAlfas Yashan']: 5,
        tags_map[masechet]['Ein Mishpat Rif']: 6,
        tags_map[masechet]['Nuschaot Ktav Yad']: 7,
        tags_map[masechet]['Rabbenu Efrayim']: 8,
        tags_map[masechet]['Ravad on Rif']: 9}
    for tag in [r'\(.\)', r'\[.\]', r'(?:^| )[א-ת](?:$| )(?![^<]*<\/i>)(?![^\(]*\))']:
        if tag not in mefarshim_tags:
            mefarshim_tags[tag] = 0 #0 for unknown

    tokenizer = partial(rif_tokenizer, masechet=masechet)
    newdata, tags_dict = [], {}
    for n, page in enumerate(data):
        id4dig = '1' + str(n).zfill(3) #1 for rif
        page, tags = page_tags(page, [tag for tag in mefarshim_tags if tag], id4dig, tokenizer=tokenizer)
        newdata.append(page)
        check_duplicate(tags_dict, tags)
        tags_dict.update(tags)

    for value in tags_dict.values():
        value['status'] = 1 #1 for base text
        value['gimatric number'] = getGematria(value['original'])
        if value['gimatric number'] == 0: print('gimatria 0', value)
        tag = identify_tag(value['original'], list(mefarshim_tags))
        value['referred text'] = mefarshim_tags[tag]
        value['style'] = 1 if '(' in value['original'] else 2 if '[' in value['original'] else 4 if ']' in value['original'] else 3

    return newdata, tags_dict

def mefaresh_tags(masechet):
    with open(path+'/Mefaresh/json/{}.json'.format(masechet)) as fp:
        data = json.load(fp)
    #resplit the data by the original pages
    data_len = len(data)
    data = '@G'.join(['@R'.join(l) for l in data])
    data = [l.split('@R') for l in data.split('##')]
    if len(data) != data_len and masechet != 'Pesachim': #in Pesachin there's an empty page
        data.pop(0)
    elif masechet == 'Pesachim':
        data = data[:35] + [''] + data[35:]

    mefarshim_tags = {r'\(.\)': 3, r'\[.\]': 5, '%22.': 1}
    if any(masechet == m for m in ['Berakhot', 'Shabbat', 'Eruvin', 'Pesachim', 'Sukkah', 'Rosh Hashanah', 'Beitzah', 'Taanit', 'Megillah', 'Moed Katan', 'Yevamot', 'Ketubot', 'Kiddushin', 'Bava Kamma', 'Bava Metzia', 'Bava Batra', 'Sanhedrin', 'Makkot', 'Shevuot', 'Avodah Zarah', 'Menachot']):
        mefarshim_tags[r'\(\*.\)'] = 2
    if masechet in ['Yoma', 'Moed Katan', 'Bava Batra']:
        mefarshim_tags[r'\(#.\)'] = 4
    if any(masechet == m for m in ['Berakhot', 'Shabbat', 'Rosh Hashanah', 'Beitzah', 'Taanit', 'Gittin', 'Bava Kamma', 'Bava Metzia', 'Sanhedrin', 'Makkot', 'Avodah Zarah', 'Menachot']):
        mefarshim_tags[r'\(#.\)'] = 3
        mefarshim_tags[r'\(\$.\)'] = 4
        mefarshim_tags[r'\[#.\]'] = 5
        if masechet == 'Gittin':
            mefarshim_tags[r'\(.\)'] = 2
        elif masechet == 'Bava Kamma':
            mefarshim_tags[r'\(.\)'] = 3
        else:
            mefarshim_tags[r'\(.\)'] = 4
    if masechet == 'Yevamot':
        mefarshim_tags[tags_map[masechet]['Nuschaot Ktav Yad']] = 7

    newdata, tags_dict = [], {}
    for n, page in enumerate(data):
        id4dig = '2' + str(n).zfill(3) #2 for mefaresh
        page, tags = page_tags(page, [tag for tag in mefarshim_tags if tag], id4dig, tokenizer=mefaresh_tokenizer)
        newdata.append(page)
        check_duplicate(tags_dict, tags)
        tags_dict.update(tags)

    newdata = '##'.join(['@R'.join(l) for l in newdata])
    newdata = [l.split('@R') for l in newdata.split('@G')]

    for value in tags_dict.values():
        value['status'] = 1 #1 for base text
        value['gimatric number'] = getGematria(value['original'])
        if value['gimatric number'] == 0: print('gimatria 0', value)
        value['style'] = 1 if '(' in value['original'] else 2 if '[' in value['original'] else 3
        tag = identify_tag(value['original'], list(mefarshim_tags))
        value['referred text'] = mefarshim_tags[tag]

    return newdata, tags_dict

def sg_tags(masechet):
    with open(path+'/commentaries/json/SG_{}.json'.format(masechet)) as fp:
        data = json.load(fp)

    mefarshim_tags = {tags_map[masechet]['sg_in_tag']: 3, r'\[.\]': 5}
    try:
        mefarshim_tags[''] #i.e. there's a bach tag
        mefarshim_tags[r'\(.\)'] = 3
    except KeyError:
        mefarshim_tags[r'\(.\)'] = 4
    if not tags_map[masechet]['Hagaot meAlfas Yashan']:
        mefarshim_tags[r'\[.\]'] = 0
    if masechet == 'Shabat':
        mefarshim_tags[r'@77\[.\]|\[.\]'] = 5

    newdata, tags_dict = [], {}
    for n, page in enumerate(data):
        id4dig = '3' + str(n).zfill(3) #3 for sg
        page, tags = page_tags(page, [tag for tag in mefarshim_tags if tag], id4dig, tokenizer=mefaresh_tokenizer)
        newdata.append(page)
        check_duplicate(tags_dict, tags)
        tags_dict.update(tags)

    for value in tags_dict.values():
        value['status'] = 1 #1 for base text
        value['gimatric number'] = getGematria(value['original'])
        if value['gimatric number'] == 0: print('gimatria 0', value)
        value['style'] = 1 if '(' in value['original'] else 2 if '[' in value['original'] else 3
        tag = identify_tag(value['original'], list(mefarshim_tags))
        value['referred text'] = mefarshim_tags[tag]

    return newdata, tags_dict

def maor_milchemet(masechet, mefaresh):
    with open(f'{path}/commentaries/json/{mefaresh}_{masechet}.json') as fp:
        data = json.load(fp)
    data = ' @G '.join([' @R '.join(l) for l in data])
    data = data.split('##')
    pre, data = data[0], data[1:]
    last = daf_to_section(data[-1].split()[0])
    newdata = ['' for _ in range(last)]
    for page in data:
        num = daf_to_section(page.split()[0]) - 1
        newdata[num] = page
    data = [page.split(' @R ') for page in newdata]

    if mefaresh == 'maor':
        mefarshim_tags = {maor_tags[masechet]['bach']: 3, maor_tags[masechet]['ravad']: 9}
        data = [[' ' + par for par in page] for page in data] #for catching ravad tags in paragraph start
    else:
        mefarshim_tags = {maor_tags[masechet]['bach tag in milchemet']: 3}
    mefarshim_tags[r'\(.\)'] = 3

    newdata, tags_dict = [], {}
    i0 = '4' if mefaresh == 'maor' else '5'
    for n, page in enumerate(data):
        if page:
            id4dig = i0 + str(n).zfill(3) #4 for maor 5 for milchemet
            page, tags = page_tags(page, [tag for tag in mefarshim_tags if tag], id4dig, tokenizer=mefaresh_tokenizer)
            newdata.append(page)
            check_duplicate(tags_dict, tags)
            tags_dict.update(tags)

    for value in tags_dict.values():
        value['status'] = 1 #1 for base text
        value['gimatric number'] = getGematria(value['original'])
        if value['gimatric number'] == 0: print('gimatria 0', value)
        value['style'] = 1 if '(' in value['original'] else 4
        tag = identify_tag(value['original'], list(mefarshim_tags))
        value['referred text'] = mefarshim_tags[tag]

    newdata = [page for page in newdata if page]
    newdata = pre + '##'.join([' @R '.join(l) for l in newdata])
    newdata = [l.split(' @R ') for l in newdata.split(' @G ')]
    newdata = [[re.sub('##+', '##', par) for par in page] for page in newdata]

    return newdata, tags_dict

def execute():
    for masechet in tags_map:
        print(masechet)
        rif, tags = rif_tags(masechet)
        mefaresh, mtags = mefaresh_tags(masechet)
        check_duplicate(tags, mtags)
        tags.update(mtags)
        if masechet != 'Nedarim':
            sg, sgtags = sg_tags(masechet)
            check_duplicate(tags, sgtags)
            tags.update(sgtags)
        if masechet not in ['Nedarim', 'Menachot']:
            maor, maortags = maor_milchemet(masechet, mefaresh='maor')
            check_duplicate(tags, maortags)
            tags.update(maortags)
            mil, miltags = maor_milchemet(masechet, mefaresh='milchemet')
            check_duplicate(tags, miltags)
            tags.update(miltags)
        print(len(tags))

        with open(path+'/tags/rif_{}.json'.format(masechet), 'w') as fp:
            json.dump(rif, fp)
        with open(path+'/tags/mefaresh_{}.json'.format(masechet), 'w') as fp:
            json.dump(mefaresh, fp)
        with open(path+'/tags/sg_{}.json'.format(masechet), 'w') as fp:
            json.dump(sg, fp)
        with open(path+'/tags/maor_{}.json'.format(masechet), 'w') as fp:
            json.dump(maor, fp)
        with open(path+'/tags/milchemet_{}.json'.format(masechet), 'w') as fp:
            json.dump(mil, fp)
        with open(path+'/tags/tags_{}.json'.format(masechet), 'w') as fp:
            json.dump(tags, fp)

if __name__ == '__main__':
    execute()
