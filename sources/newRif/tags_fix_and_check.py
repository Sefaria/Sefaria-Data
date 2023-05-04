import json
import django
django.setup()
from collections import OrderedDict
from sefaria.utils.talmud import section_to_daf
from parsing_utilities.util import getGematria, he_char_ord, he_ord, inv_gematria
from rif_utils import path, tags_map

inv_he_char = {}
for key in he_char_ord:
    inv_he_char[he_char_ord[key]] = key

def num_to_gem(num):
    return getGematria(inv_he_char[int(num)])

def gem_to_num(gem):
    if gem == 0: return 0
    else: return he_ord(inv_gematria[gem])

def next_gem(gem, cycle=True):
    if gem == 0: return 1
    num = gem_to_num(gem) + 1
    if num > 22:
        if cycle:
            next = num % 22
        else:
            raise ValueError('No letter after 22')
    else:
        next = num_to_gem(num)
    return next

def open_tags(masechet):
    with open(path+'/tags/tags_{}.json'.format(masechet)) as fp:
        data = json.load(fp)
    return data

def save_tags(tags, masechet):
    old = open_tags(masechet)
    old.update(tags)
    with open(path+'/tags/tags_{}.json'.format(masechet), 'w') as fp:
        json.dump(old, fp)

def mefaresh_tags(tags_dict, mefaresh):
    return {tag: tags_dict[tag] for tag in tags_dict if tags_dict[tag]['referred text'] == mefaresh}

def page_tags(tags_dict, page: int):
    return {tag: tags_dict[tag] for tag in tags_dict if int(tag[1:4]) == page}

def tags_by_criteria(tags_or_masechet, key=lambda x: True, value=lambda x: True):
    if type(tags_or_masechet) == str:
        tags = open_tags(tags_or_masechet)
    else:
        tags = tags_or_masechet
    return {tag: tags[tag] for tag in tags if key(tag) and value(tags[tag])}

def pages_range(tags_dict):
    pages = [int(tag[1:4]) for tag in tags_dict]
    return range(min(pages), max(pages)+1)

def generate_mefaresh_and_page(tags_dict, mefarshim=range(0,10)):
    for page in pages_range(tags_dict):
        page_dict = page_tags(tags_dict, page)
        for mefaresh in mefarshim:
            yield mefaresh_tags(page_dict, mefaresh)

def out_of_orders(lis: list):
    if len(lis) < 2: return []
    out_indexes = []
    gap = 2
    exp_lis = [0] + lis + [next_gem(lis[-2])] #last element for checking the original last element
    for n, num in enumerate(lis):
        if gem_to_num(exp_lis[n+gap]) - gem_to_num(exp_lis[n+gap-2]) == 1 and num != exp_lis[n+gap] and num != exp_lis[n+gap-2]:
            if n == 0 and num == 1: continue #in this case it can be just omission of the first
            if n == len(lis)-1 and num >= lis[-2]: continue # when > it can be omission before the last (especiall when Ran has one tag with gap of tags in Rashi). When = we can't know what tag is the redundant
            out_indexes.append(n)
            exp_lis.pop(n+gap-1)
            gap -= 1
    if out_indexes == []: return []
    elif out_indexes[-1] == len(lis) - 1 and gem_to_num(lis[-1]) - gem_to_num(lis[-2]) == 2: #in that case it can be a missing tag
        return out_indexes[:-1]
    return out_indexes

def exclude_redundant(tags_dict):
    #if tag is out of ordered, changes the 'refered text' to unknown and returns the new dict
    for subdict in generate_mefaresh_and_page(tags_dict, mefarshim=range(1,10)):
        tags_list = sorted(subdict.items(), key = lambda x: int(x[0]))
        for redundant in out_of_orders([tag[1]['gimatric number'] for tag in tags_list]):
            tags_dict[tags_list[redundant][0]]['referred text'] = 0
    return tags_dict

def add_from_unknowns(tags_dict):
    for page in pages_range(tags_dict):
        page_dict = page_tags(tags_dict, page)
        for mefaresh in range(1,10):
            m_dict = mefaresh_tags(page_dict, mefaresh)
            m_dict = OrderedDict(sorted(m_dict.items(), key=lambda x: int(x[0])))
            prev, prev_key = 0, 0
            for tag in m_dict:
                if tags_dict[tag]['gimatric number'] == num_to_gem((prev + 1) % 22 + 1):
                    optionals = []
                    unk_dict = mefaresh_tags(page_dict, 0)
                    for key, value in unk_dict.items():
                        if value['style'] == tags_dict[tag]['style'] and value['gimatric number'] == num_to_gem((prev) % 22 + 1) and prev_key < int(key) < int(tag):
                            optionals.append(key)
                    if len(optionals) == 1:
                        tags_dict[optionals[0]]['referred text'] = mefaresh
                if tags_dict[tag]['gimatric number'] != 0:
                    prev = gem_to_num(tags_dict[tag]['gimatric number'])
                prev_key = int(tag)
    return tags_dict

def check_sequence(tags_dict, masechet):
    with open(f'{path}/tags_exceptions.txt', encoding='utf-8') as fp:
        exceptions = fp.read()
    exceptions = exceptions.split('&')
    exceptions = [e for e in exceptions if masechet in e]
    if exceptions: exceptions = exceptions[0]
    tags_dict = OrderedDict(sorted(tags_dict.items(), key=lambda x: int(x[0])))
    prev = 0
    check = True
    for tag in tags_dict:
        if tag[0] == '2' and tags_dict[tag]['num_in_page'] == 1: #jump between if and mefaresh is allowed (for Rashi)
            if tags_dict[tag]['gimatric number'] <= prev:
                p = 'page {} last tag in Rif is {} and first in mefaresh is {} (mefaresh={})'.format(
                    section_to_daf(int(tag[1:4])+1), prev, tags_dict[tag]['gimatric number'], tags_dict[tag]['referred text'])
                if p not in exceptions:
                    print(p)
        elif tags_dict[tag]['gimatric number'] != next_gem(prev):
            if prev == 0:
                p = 'page {} first tag is {} tag {} (mefaresh={}) {}'.format(
                    section_to_daf(int(tag[1:4])+1), tags_dict[tag]['gimatric number'], tags_dict[tag]['original'], tags_dict[tag]['referred text'], tag)
                if p not in exceptions:
                    print(p)
            else:
                p = 'page {}: {} comes after {} in {} tag  {} (mefaresh={}) {}'.format(
                    section_to_daf(int(tag[1:4])+1), tags_dict[tag]['gimatric number'], prev, 'Rif' if tag[0]=='1' else 'SG' if tag[0]=='3' else 'mefaresh', tags_dict[tag]['original'], tags_dict[tag]['referred text'], tag)
                if p not in exceptions:
                    print(p)
        prev = tags_dict[tag]['gimatric number']

def ad_hocs(tags, masechet):
    for tag in tags_by_criteria(tags, value=lambda x: x['referred text']==0 and x['style']==2):
        tags[tag]['referred text'] = 5
    if masechet == 'Pesachim':
        tags['20341000']['referred text'] = 2
    elif masechet == 'Sukkah':
        tags['30040100']['referred text'] = 3
    elif masechet == 'Beitzah':
        tags['30049900']['referred text'] = 3
        tags['30059900']['referred text'] = 3
    elif masechet == 'Yevamot':
        tags['40480000']['referred text'] = 3
    elif masechet == 'Kiddushin':
        tags['30089900']['referred text'] = 3
    elif masechet == 'Bava Kamma':
        tags['20431000']['referred text'] = 2
    return tags

def execute():
    for masechet in tags_map:
        print(masechet)
        data = open_tags(masechet)
        data = exclude_redundant(data)
        data = add_from_unknowns(data)
        for subdict in generate_mefaresh_and_page(data, range(1,11)):
            check_sequence(subdict, masechet)
        data = ad_hocs(data, masechet)
        save_tags(data, masechet)

if __name__ == '__main__':
    execute()
