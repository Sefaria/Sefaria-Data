import re
import copy
import requests
import json
from collections import OrderedDict
import django
django.setup()
from sefaria.model import *
from sources.functions import getGematria, post_index
from sefaria.utils.talmud import section_to_daf

def missings(nums):
    if nums:
        return set(range(min(nums), max(nums)+1)) - set(nums)

index = library.get_index('Zohar TNG')
index.versionState().refresh()
oldbook = book = None
parashot = {}
refs = {}
rjson = []
for segment in Ref('Zohar TNG').all_segment_refs():
    if segment.sections[1:] == [1, 1]:
        oldbook = book = None
    text = segment.text('he').text
    if segment == Ref('Zohar TNG.19.3.1'):
        book = oldbook = 'saba'
    # if segment == Ref('Zohar TNG.38.1.1'):
    #     book = oldbook = 'idra raba'
    if segment == Ref('Zohar TNG.40.12.1'):
        book = oldbook = 'rav metivta'
    if segment in [Ref('Zohar TNG.44.61.8'), Ref('Zohar TNG.44.88.1'), Ref('Zohar TNG.37.18.1')]:
        book = oldbook = 'raya'
    elif segment in [Ref('Zohar TNG.20.12.25'), Ref('Zohar TNG.34.12.5'), Ref('Zohar TNG.2.47.6')]:
        book = oldbook = None

    for closed in re.findall('\(([^)]*)\)', text):
        if closed.startswith('דף '):
            continue

        if 'רעיא מהימנא' in closed and not any(word in closed for word in ['עד כאן', 'ע"כ', 'ע"ד']):
            book = 'raya'
        elif 'רזא דרזין' in closed:
            book = 'raza'
        elif closed in ['סתרי תורה', 'סתרי - תורה', 'גליון'] and not any(word in closed for word in ['עד כאן', 'ע"כ', 'ע"ד']):
            book = 'sitrei'
        elif 'תוספתא' in closed and not any(word in closed for word in ['עד כאן', 'ע"כ', 'ע"ד']):
            book = 'tosefta'
        elif 'אידרא דמשכנא' in closed:
            book = 'idra demishkena'
        elif 'מדרש הנעלם' in closed and not any(word in closed for word in ['עד כאן', 'ע"כ', 'ע"ד']):
            book = 'neelam'
        elif any(word in closed for word in ['עד כאן', 'ע"כ', 'ע"ד', 'עכ"מ']) and closed not in ['עד כאן ד"א']:
            refs[segment] = book
            book = None
        else:
            continue
        if book and oldbook:
            print('new book before ad kan of previous', text, segment)
        if not book and not oldbook:
            print('ad kan without starting', text)
        oldbook = book

    if segment not in refs:
        refs[segment] = book

page = 0
refsdaf = {}
for i, parasha in enumerate(Ref('Zohar TNG').all_subrefs(), 1):
    parashot[i] = {'guf': OrderedDict()}
    for segment in parasha.all_segment_refs():
        if segment.sections[1:] == [1, 1]:
            oldbook = 'guf'
        refsdaf[segment] = []
        text = segment.text('he').text
        book = refs[segment]
        book = book if book else 'guf'

        dapim = re.findall('\((דף [^)]*)\)', text)
        if dapim:
            if re.sub('\(.*?\)|\(|\)', '', re.split('\((דף [^)]*)\)', text)[0]).strip():
                if book in parashot[i] and parashot[i][book]:
                    if page in parashot[i][book]:
                        parashot[i][book][page].append(segment)
                    else:
                        parashot[i][book][page] = [segment]
                else:
                    parashot[i][book] = OrderedDict({page: [segment]})
            for closed in dapim:
                if not re.search('^דף ["\'א-ת]{,4} ע"[אב]', closed):
                    print('problem with daf', segment, closed)
                    continue
                daf, amud = re.findall('^דף (["\'א-ת]{,4}) ע"([אב])', closed)[0]
                page = getGematria(daf) * 2 - 2 + getGematria(amud)
                if book in parashot[i] and parashot[i][book]:
                    if page < next(reversed(parashot[i][book])):
                        print(f'problem with pages. page {page} in {book} in {segment} comes after {next(reversed(parashot[i][book]))}')
                    if page in parashot[i][book]:
                        parashot[i][book][page].append(segment)
                    else:
                        parashot[i][book][page] = [segment]
                else:
                    parashot[i][book] = OrderedDict({page: [segment]})
                if re.sub('\(.*?\)|\(|\)' ,'', text.split(closed)[0]).strip():
                    refsdaf[segment].append(oldpage)
                oldpage = page
        elif book != oldbook:
            if book in parashot[i]:
                if page in parashot[i][book]:
                    parashot[i][book][page].append(segment)
                else:
                    parashot[i][book][page] = [segment]

            else:
                parashot[i][book] = OrderedDict({page: [segment]})
        else:
            if page in parashot[i][book]:
                parashot[i][book][page].append(segment)
            else:
                parashot[i][book][page] = [segment]
        oldbook = book
        refsdaf[segment].append(page)
        rjson.append({'ref': segment.normal(), 'book': book, 'page': page})

for parasha in parashot:
    if not parashot[parasha]['guf']:
        parashot[parasha].pop('guf')

for parasha in parashot:
    allm = missings([x for y in parashot[parasha] for x in parashot[parasha][y]])
    if allm:
        print(f'missings in {parasha}:', allm)
    gufm = missings(parashot[parasha].get('guf'))
    if gufm:
        print(f'missings in {parasha} in guf:', gufm)

book = 'guf'
daf = '0'
for segment in refs:
    if refs[segment] != book:
        book = refs[segment]
    else:
        if refsdaf[segment][0] - daf not in [0, 1]:
            print(f'in {segment} going from {daf} to {refsdaf[segment][0]}')
    daf = refsdaf[segment][0]
    for d in refsdaf[segment][1:]:
        if d - daf not in [0, 1]:
            print(f'in {segment} going from {daf} to {d}')
        daf = d

book = 'guf'
page = 0
for segment in refs:
    vs = [v for v in segment.version_list() if 'Sulam' in v['versionTitle']]
    if len(vs) != 1:
        if len(vs) == 0: continue
        print('number of version is not 1', segment)
    tc = segment.text('he', vtitle=vs[0]['versionTitle'])
    text = tc.text
    for ref in re.findall('\(דף [^)]*\)', text):
        daf, amud = re.findall('^\(דף (["\'א-ת]{,4}) ע"([אב])', ref)[0]
        newpage = getGematria(daf) * 2 - 2 + getGematria(amud)
        if page != newpage:
            text = re.sub(f'{re.escape(ref)} *', f'<i data-overlay="Vilna Pages" data-value="{section_to_daf(newpage)}"></i>', text)
            if refs[segment] != book:
                if newpage - page == 0:
                    print('redundant page', segment)
                book = refs[segment]
            page = newpage
        else:
            text = re.sub(re.escape(ref), f'', text)
    tc.text = text
    tc.save(force_save=True)

def combine_ref(refs):
    if len(refs) == 1:
        return refs[0].normal()
    return Ref(f'{refs[0]}-{refs[-1].normal().replace("Zohar TNG", "")}').normal()

def set_skip(nums, node):
    rang = range(min(nums),  max(nums) + 1)
    rate = len(nums) / len(rang)
    if rate < .5:
        node['addresses'] = list(nums)
    elif rate < 1:
        node['skipped_addresses'] = [x for x in rang if x not in nums]

def make_node(i, book):
    nums = parashot[i][book]
    print(11111, nums)
    node = {'nodeType': 'ArrayMapNode', 'depth': 1, 'addressTypes': ['Talmud'], 'sectionNames': ['Daf']}
    node['startingAddress'] = section_to_daf(min(nums))
    node['refs'] = [combine_ref(parashot[i][book][page]) for page in parashot[i][book]]
    node['wholeRef'] = combine_ref([ref for page in parashot[i][book] for ref in parashot[i][book][page]])
    set_skip(nums, node)
    print(22222, node)
    return node


def alt_pages(i, node):
    book_dict = {'guf': ('גוף הזהר', 'Body'),
                 'sitrei': ('סתרי תורה', 'Sitrei Torah'),
                 'neelam': ('מדרש הנעלם', "Midrash HaNe'elam"),
                 'tosefta': ('תוספתא', 'Tosefta'),
                 'raza': ('רזא דרזין', 'Raza DeRazin'),
                 'saba': ('סבא דמשפטים', 'Saba DeMishpatim'),
                 'yenuka': ('ינוקא', 'Yenuka'),
                 'rav metivta': ('רב מתיבתא', 'Rav Metivta'),
                 'idra demishkena': ('אדרא דמשכנא', 'Idra DeMishkena'),
                 'raya': ('רעיא מהימנא', "Ra'ya Mehemna")}
    books = [x for x in parashot[i]]
    if books == ['guf']:
        newnode = make_node(i, books.pop())
        newnode['titles'] = node['titles']
    else:
        newnode = {'titles': node['titles'], 'nodes': []}
        for book in book_dict:
            if book in books:
                subnode = make_node(i, book)
                if book == 'guf':
                    subnode['default'] = True
                else:
                    subnode['titles'] = [{'lang': 'en', 'primary': True, 'text': book_dict[book][1]},
                                         {'lang': 'he', 'primary': True, 'text': book_dict[book][0]}]
                newnode['nodes'].append(subnode)
    return newnode

nodes = []
i = 1
alts = copy.deepcopy(index.alt_structs['Paragraph'])
boo = False
for chumash, _ in enumerate(alts['nodes']):
    if i == 1:
        alts['nodes'][chumash] = alt_pages(i, alts['nodes'][chumash])
        i += 1
    else:
        for parasha, _ in enumerate(alts['nodes'][chumash]['nodes']):
            alts['nodes'][chumash]['nodes'][parasha] = alt_pages(i, alts['nodes'][chumash]['nodes'][parasha])
            i += 1

server = 'http://localhost:9000'
index = requests.get('http://localhost:9000/api/v2/raw/index/Zohar_TNG').json()
index['alt_structs']['Pages'] = alts
post_index(index, server=server)

with open('sulam_map.json', 'w') as fp:
    json.dump(rjson, fp)
