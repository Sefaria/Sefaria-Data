import re
from functools import partial
from sources.functions import getGematria
from rif_utils import tags_map, remove_metadata

def two_digit(num):
    return '0' + str(num) if num < 10 else str(num)

def sort_tags(tags_list):
    untags = [r'\(.\)', r'\[.\]']
    return [tag for tag in reg_tags if tag not in untags] + [tag for tag in reg_tags if tag in untags]
    #untaged tags should be in the end for searching the real tags first, e.g. searching @68(a) before (a)

def identify_tag(actual_tag: str, reg_tags: list) -> str:
    reg_tags = sort_tags(reg_tags)
    for tag in reg_tags:
        if re.search('^'+tag+'$', actual_tag): return tag

def rif_tokenizer(string, masechet):
    return remove_metadata(string, masechet).split()

def paragraph_tags(text: str, regex: str, id5dig: str, tokenizer=lambda x: x.split()):
    tags = re.findall(reg_tag, text)
    tags_dict = {}
    for n, tag in enumerate(tags):
        id = id5dig + two_digit(n)
        a, b = text.split(tag, 1)
        a, b = tokenizer(a), tokenizer(b)
        context = ' '.join(a[-5:] + b[:5])
        word_index = len(a)
        text = text.replace(tag, ' $'+id+' ', 1)
        tags_dict[id] = {'word_index': word_index, 'context': context, 'original': tag}
    return text, tags_dict

def page_tags(page: list, reg_tags: list, id3dig: str, tokenizer=lambda x: x.split()):
    new_page = []
    tags_dict = {}
    tags_count = {tag: 1 for tag in reg_tags}
    regex = '|'.join(sort_tags(reg_tags))
    for n, par in enumerate(page):
        id5dig = id3dig + two_digit(n)
        text, tags = paragraph_tags(par, regex, id5dig, tokenizer=tokenizer)
        new_page.append(text)
        for id in tags:
            tag = identify_tag(tags[id]['original'], reg_tags)
            tags[id]['num_in_page'] = tags_count[tag]
            tags_count[tag] += 1
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
        id3dig = '1' + two_digit(n) #1 for rif
        page, tags = page_tags(page, list(mefarshim_tags), id3dig, tokenizer=tokenizer)
        newdata.append(page)
        tags_dict.update(tags)

    for id in tags_dict:
        tags_dict[id]['status'] = 1 #1 for base text
        tags_dict[id]['gimatric number'] = getGematria(tags_dict[id]['original'])
        tag = identify_tag(tags_dict[id]['original'])
        tags_dict[id]['referred text'] = mefarshim_tags[tag]
        tags_dict[id]['style'] = 1 if '(' in tag else 2 if '[' in tag else 3

    return newdata, tags_dict
