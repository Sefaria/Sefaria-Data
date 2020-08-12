import re
import json
from functools import partial
from colections import Counter
from sources.functions import getGematria
from rif_utils import tags_map, remove_meta_and_html, path

def sort_tags(tags_list):
    untags = [r'\(.\)', r'\[.\]']
    return sorted(tags_list, key=lambda x: True if x in untags else False)
    #untaged tags should be in the end for searching the real tags first, e.g. searching @68(a) before (a)

def identify_tag(actual_tag: str, reg_tags: list):
    for tag in sort_tags(reg_tags):
        if re.search(f'^{tag}$', actual_tag): return tag

def rif_tokenizer(string, masechet):
    return remove_meta_and_html(string, masechet).split()

def mefaresh_tokenizer(string):
    return re.sub(r'\(.\)|\[.\]| . |<[^>]*>', ' ', string).split()

def paragraph_tags(text: str, regex: str, id5dig: str, tokenizer=lambda x: x.split(), word_range=5):
    #word range is safe to adjust
    tags = re.findall(reg_tag, text)
    tags_dict = {}
    for n, tag in enumerate(tags):
        id7dig = id5dig + str(n).zfill(2)
        a, b = text.split(tag, 1)
        a, b = tokenizer(a), tokenizer(b)
        context = ' '.join(a[-word_range:] + b[:word_range])
        word_index = len(a)
        text = text.replace(tag, f' ${id7dig} ', 1)
        tags_dict[id7dig] = {'word_index': word_index, 'context': context, 'original': tag}
    return text, tags_dict

def page_tags(page: list, reg_tags: list, id3dig: str, tokenizer=lambda x: x.split()):
    new_page, tags_dict, tags_count = [], {}, Counter(reg_tags)
    regex = '|'.join(sort_tags(reg_tags))
    for n, par in enumerate(page):
        id5dig = f'{id3dig}{str(n).zfill(2)}'
        text, tags = paragraph_tags(par, regex, id5dig, tokenizer=tokenizer)
        new_page.append(text)
        for value in tags.values():
            tag = identify_tag(value['original'], reg_tags)
            value['num_in_page'] = tags_count[tag]
            tags_count[tag] += 1
        if set(tags_dict) & set(tags) != set():
            print(f'duplicate tags {set(tags_dict) & set(tags)}')
        tags_dict.update(tags)
    return new_page, tags_dict

def rif_tags(masechet):
    #data = get data as a ja. i don't sure if it will be from csv or json
    mefarshim_tags = {tags_map[masechet]['Shiltei HaGiborim']: 3,
        tags_map[masechet]['Chidushei An"Sh']: 4,
        tags_map[masechet]['Bach on Rif']: 5,
        tags_map[masechet]['Hagaot Chavot Yair']: 6,
        tags_map[masechet]['Hagaot meAlfas Yashan']: 7,
        tags_map[masechet]['Ein Mishpat Rif']: 8}
    for tag in [r'\(.\)', r'\[.\]', ' . ']:
        if tag not in mefarshim_tags:
            mefarshim_tags[tag] = 0 #0 for unknown

    tokenizer = partial(rif_tokenizer, masechet=masechet)
    newdata, tags_dict = [], {}
    for n, page in enumerate(data):
        id3dig = '1' + str(n).zfill(2) #1 for rif
        page, tags = page_tags(page, [tag for tag in mefarshim_tags if tag], id3dig, tokenizer=tokenizer)
        newdata.append(page)
        if set(tags_dict) & set(tags) != set():
            print(f'duplicate tags {set(tags_dict) & set(tags)}')
        tags_dict.update(tags)

    for value in tags_dict.values():
        value['status'] = 1 #1 for base text
        value['gimatric number'] = getGematria(value['original'])
        tag = identify_tag(value['original'], list(mefarshim_tags))
        value['referred text'] = mefarshim_tags[tag]
        value['style'] = 1 if '(' in tag else 2 if '[' in tag else 3

    return newdata, tags_dict

def mefaresh_tags(masechet):
    with open(path+'/Mefaresh/json/{}.json'.format(masechet)) as fp:
        data = json.load(fp)
    mefarshim_tags = {r'\(.\)': 5, r'\[.\]': 6, ' . ': 0}
    newdata, tags_dict = [], {}
    for n, page in enumerate(data):
        id3dig = '2' + str(n).zfill(2) #2 for mefaresh
        page, tags = page_tags(page, mefarshim_tags, id3dig, tokenizer=mefaresh_tokenizer)
        newdata.append(page)
        if set(tags_dict) & set(tags) != set():
            print(f'duplicate tags {set(tags_dict) & set(tags)}')
        tags_dict.update(tags)

    for value in tags_dict.values():
        value['status'] = 1 #1 for base text
        value['gimatric number'] = getGematria(value['original'])
        value['style'] = 1 if '(' in tag else 2 if '[' in tag else 3
        value['referred text'] = 0 if value['style'] == 3 else value['style']+4

    return newdata, tags_dict
