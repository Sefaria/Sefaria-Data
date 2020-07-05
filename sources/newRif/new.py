import django
django.setup()
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import requests
import json
import re
import copy
import os
import statistics

server = 'http://localhost:8000'
#server = 'https://glazner.cauldron.sefaria.org'


def cleanspaces(string):
    while any(space in string for space in ['  ', '( ', ' )', ' :', ' .']):
        for space in ['  ', '( ', ' )', ' :', ' .']:
            string = string.replace(space, space.replace(' ', '', 1))
    return string.strip()

def removetags(string, taglist):
    for tag in taglist:
        string = string.replace(tag, '')
    return cleanspaces(string)

def removeinbetween(stringtoclean, sub1, sub2):
    return cleanspaces(re.sub(sub1+'.*?'+sub2, '', stringtoclean))

def hebrewplus(string_to_clean, letters_to_remain=''):
    return cleanspaces(re.sub(r"[^א-ת "+letters_to_remain+"]", '', string_to_clean))

def cleansingles(string):
    return re.sub(' . ', ' ', string)

def netlen(string): #length in words without oher text
    for tag in '346':
        string = removeinbetween(string, '@1'+tag, '@77')
    return cleansingles(hebrewplus(string)).count(' ')+1

def index2page(i):
    i+=1
    if i/2 == round(i/2):
        return '{}b'.format(int(i/2))
    else:
        return '{}a'.format(int(i/2+0.5))

def change_data(func):
    global data
    data = [[func(section) for section in page] for page in data]

def find_section(section):
    for m, page in enumerate(data):
        try:
            return m, page.index(section)
        except:
            print('doesnt find section', section)

def check():
    global data
    #44 - bold. 55 - unbold. 13 - tanakh refs. 14 - in masechet refs. 16 - other refs and notes. 77 - ending of 13, 14, or 16.
    if data.count('@44') != data.count('@55'):
        print('{} @44s and {} @55s'.format(count('@44'), count('@55')))
        if string.count('@13') + string.count('@14') + string.count('@16') != string.count('@77'):
            print('{} @13s, {} @14s, {} @16s and {} @77s'.format(count('@13'), count('@14'), count('@16'), count('@77')))
    #check page number. shiuld have @20s as pages-1 for n the beginning it shuln't appear
    leng = len(Ref('Rif '+masechet).text('he').text)
    if data.count('@20')+1 != len:
        if data.count('@20') == len and '@20' in data[:20]:
            data = data.replace('@20', '', 1)
        else: print('{} pages in rif but {} @20s in data'.format(leng, data.count('@20')))

def divide(): #dividing text to pages and segments
    global data
    data = re.sub('(@00.*?)@', r'\1\n@',data)
    data = data.replace('.', '.A').replace(':', ':A').replace('\n', 'A')
    for note in re.findall('@1[346].*?@77', data):
        data = data.replace(note, note.replace('A', ''))
    data = [page.split('A') for page in data.split('@20')]
    data = [[cleanspaces(section) for section in page if cleanspaces(section)!=''] for page in data]
    #joning short sections, assuming the short one is a mishna quatation
    for m, page in enumerate(data):
        for n, section in enumerate(page):
            if netlen(section) < 6 and n != len(page)-1 and (n > 0 or data[m-1][-1][-1] == ':'):
                if '@00' not in page[n] and '@00' not in page[n+1]:
                    page[n] = page[n] + ' ' + page[n+1]
                    page.pop(n+1)
        data[m] = page
    #sectin length statistics
    sections_length = [netlen(section) for page in data for section in page]
    mean, median, std = statistics.mean(sections_length), statistics.median(sections_length), statistics.pstdev(sections_length)
    regular = len([length for length in sections_length if mean-std <= length <= mean+std])
    long = len([length for length in sections_length if mean+std < length <= mean+2*std])
    short = len([length for length in sections_length if mean-std > length >= mean-2*std])
    verylong = len([length for length in sections_length if mean+2*std < length])
    veryshort = len([length for length in sections_length if mean-2*std > length])
    print(mean, median, std, veryshort, short, regular, long, verylong)

def createindex():
    ind = requests.get("https://www.sefaria.org/api/v2/raw/index/Rif_" + masechet).json()
    #library.get_index('Rif ' + masechet).delete()
    return ind

def findalts():
    starts = []
    ends = []
    for page in data:
        for section in page:
            if '@00' in section:
                starts.append([data.index(page), page.index(section), section.replace('@00', '').strip()])
    for m,n,o in starts[1:]:
        if n==0: ends.append([m-1, len(data[m-1])-1])
        else: ends.append([m, n-1])
    ends.append([len(data), len(data[-1])])
    return starts, ends

def create_alts():
    starts, ends = findalts()
    nodes = []
    for n in range(len(starts)):
        node = ArrayMapNode()
        node.depth = 0
        node.wholeRef = "Rif {} {}:{}-{}:{}".format(masechet, index2page(starts[n][0]), starts[n][1]+1, index2page(ends[n][0]), ends[n][1]+1)
        node.includeSections = True
        node.add_primary_titles('Chapter {}'.format(n+1), starts[n][2])
        nodes.append(node.serialize())
    return nodes

def postindex():
    ind = createindex()
    ind["alt_structs"] = {'Chapters': {'nodes': create_alts()}}
    functions.post_index(ind, server = server)

def posttext():
    version = {
        'versionTitle': 'Vilna Edition',
        'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH001300957/NLI',
        'language': 'he',
        'text': data
    }
    functions.post_text('Rif '+masechet, version, server=server)

def hande_simple_tags(string):
    #notice some changes should be done in a specific step of the code
    string = removetags(string, ['@15', '@17', '@18', '@19', '@99', '?*'])
    #99-hadran ?* - printed asreisks that has no comment. 15 18 19 - notes we havn't. 17 - old dafs
    string = string.replace('@44', '<big><b>').replace('@55', '</big></b>')
    if '@00' in string: string = string.replace('@00', '<b><big>')+'</b></big>' #should be after postindex (for @00 are needed for lt structs)
    return string

def handle77(string):
    #handle @13
    refs = re.findall('@13[^@]*?@77', string)
    if list([ref for ref in refs if ref[3:5]!='דף']) != []: print('ref withno daf', [ref for ref in refs if ref[3:5]!='דף'])
    string = re.sub('@13דף(.*?)@77', r'(ברכות\1)', string)
    #handle @16
    refs = re.findall('@16[^@]*?@77', string)
    for ref in refs:
        try:
            Ref(hebrewplus(ref))
        except:
            if 'שם' not in ref: print(ref, 'is not a ref')
    string = re.sub('@16(.*?)@77', r'(\1)', string)
    #handle @14
    comments = re.findall('@14[^@]*?@77', string)
    if any(len(comment) > 150 for comment in comments):
        print('long comment', comment)
    while re.findall('@14[^@]*?@77', string) != []:
        first = re.findall('@14[^@]*?@77', string)[0].replace('@14', '').replace('@77', '')
        try:
            Ref(first)
            string = re.sub('@14([^@]*?)@77',r'(\1)', string, 1).replace('()', '')
        except:
            if 'דף' in first or 'שם' in first:
                string = re.sub('@14([^@]*?)@77',r'(\1)', string, 1).replace('()', '')
            else:
                string = re.sub('@14([^@]*?)@77', r'<sup>*</sup><i class="footnote">\1</i>', string, 1).replace(' C ', ' C')
    return string

def map_links(section):
    '''
    any link has an id which is his index in linkmap and dict:
    mefaresh
    base_text: rif, main_mefaresh, None
    finded: True when finded in the or None
    page
    section: section index in page
    index: index in section
    order: the number of the note according to the tag order (first tag in page is 1)
    number: the number of note according to the gematria of letter in text
    original_tag: e.g. @22א or (#ב). the original would replaced by $id$ in both texts
    '''
    global linkmap


def parse_text(masechet):
    global data
    with open(masechet+'.txt', encoding = 'utf-8') as file:
        data = file.read()
    check()
    divide()
    postindex()
    change_data(hande_simple_tags)
    change_data(handle77)
    change_data(map_links)
    posttext()

global masechet
masechet = 'Berakhot'
heb_masechet = Ref(masechet).index.get_title('he')
parse_text(masechet)
