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

server = 'http://localhost:8000'
#server = 'https://glazner.cauldron.sefaria.org'

def findCommentary(stringslist):
    for root, dirs, files in os.walk(os.getcwd()+'/commentaries'):
        for file in files:
            if any(string in file for string in stringslist):
                return root + '/' + file

def createindex(masechet):
    ind = requests.get("https://www.sefaria.org/api/v2/raw/index/Rif_" + masechet).json()
    #library.get_index('Rif ' + masechet).delete()
    return ind

def index2page(i):
    i+=1
    if i/2 == round(i/2):
        return '{}b'.format(int(i/2))
    else:
        return '{}a'.format(int(i/2+0.5))

def create_alts(masechet, starts, ends):
    nodes = []
    for n in range(len(starts)):
        node = ArrayMapNode()
        node.depth = 0
        node.wholeRef = "Rif {} {}:{}-{}:{}".format(masechet, index2page(starts[n][0]), starts[n][1]+1, index2page(ends[n][0]), ends[n][1]+1)
        node.includeSections = False
        node.add_primary_titles('Chapter {}'.format(n+1), starts[n][2])
        nodes.append(node.serialize())
    return nodes

def cleanspaces(string):
    while any(space in string for space in ['  ', '( ', ' )', ' :', ' .']):
        for space in ['  ', '( ', ' )', ' :', ' .']:
            string = string.replace(space, space.replace(' ', '', 1))
    return string.strip()

def big(string):
    if string.count('@44') != string.count('@55'):
        print('{} @44s and {} @55s'.format(count('@44'), count('@55')))
    return string.replace('@44', '<big><b>').replace('@55', '</big></b>')

def removehtml(string):
    return re.sub(r'\<.*?\>', '', string)

def base_tokenizer(string):
    return removehtml(string).split()

def clean_string(string):
    string = re.sub(r'\(.*?\)', '', removehtml(string))
    return re.sub(r"[^א-ת'\" ]", '', string)

def getGemaraRefs(string):
    refs = re.findall('@13[^@]*?@77', string)
    if any(len(ref) > 15 for ref in refs):
        print('long ref', ref)
    return re.sub('@13[^@]*?@77', 'B', string).replace(' B ', ' B'), refs

def getComments(string):
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
    return string, comments

def handleMikraRefs(string):
    comments = re.findall('@16[^@]*?@77', string)
    if any(len(comment) > 20 for comment in comments):
        print('long ref', comment)
    return re.sub('@16([^@]*?)@77', r'(\1)', string).replace('()', '').replace('( )', '')

def notes(string):
    if string.count('@13') + string.count('@14') + string.count('@16') != string.count('@77'):
        print('{} @13s, {} @14s, {} @16s and {} @77s'.format(count('@13'), count('@14'), count('@16'), count('@77')))
    string, gemararefs = getGemaraRefs(string)
    string, comments = getComments(string)
    string = handleMikraRefs(string)
    return string, gemararefs, comments

def markSections(string):
    string = re.sub('(@00[^@]*?)@', r'\1\n@', string)
    string = string.replace('.', '.A').replace(':', ':A').replace('\n', 'A')
    for note in re.findall('@1[346][^@]*?@77', string):
        string = string.replace(note, note.replace('A', ''))
    return string

def getLinks(pageindex, sectionindex, section):
    global links
    global link
    global gemararefs
    while 'B' in section:
        ref = cleanspaces(gemararefs.pop(0).replace('@13', '').replace('@77', ''))
        if ref != '':
            if 'דף' in ref and ref.count(' ') == 1 and (ref[-1] == '.' or ref[-1] == ':'):
                link = '{} {}a'.format(masechet, functions.getGematria(ref.split()[1])) if ref[-1] == '.' else '{}b'.format(functions.getGematria(ref.split()[1]))
            elif ref != 'שם':
                print('error ref', ref)

            links.append({
                    "refs": [link,
                    'Rif {} {}:{}'.format(masechet, index2page(pageindex), sectionindex+1)],
                    "type": "Commentary",
                    "auto": True,
                    "generated_by": 'rif'
                    })
        section = section.replace('B', '', 1)
    return section

def shiltei(data):
    shilteiLetters = {}
    for n, page in enumerate(data):
        shilteiLetters[index2page(n)] = re.findall('@11[^ ]*? ', page)
        data[n] = re.sub('@11[^ ]*? ', 'S', page)
    return data

def einmishpat(data):
    einLetters = {}
    for n, page in enumerate(data):
        einLetters[index2page(n)] = re.findall('@[12]2[^ ]*? ', page)
        data[n] = re.sub('@[12]2[^ ]*? ', 'E', page)
    return data

def bach(data):
    bachLetters = {}
    for n, page in enumerate(data):
        page = page.replace('(#@68', '(@68').replace('$@', '@').replace('$', '@68')
        bachLetters[index2page(n)] = re.findall(r'\(@68[^\)]*?\)', page)
        data[n] = re.sub(r'\(@68[^\)]*?\)', 'X', page).replace(' X ', ' X')
    return data

def choi(data):
    choiLetters = {}
    for n, page in enumerate(data):
        page = re.sub('@66(.) ', '(\1)', page)
        choiLetters[index2page(n)] = re.findall(r'\(.\)', page) #assuming there is no more than 10 per pageindex
        data[n] = re.sub(r'\(.\)', 'Y', page).replace(' Y ', ' Y')
    return data

def mai(data):
    maiLetters = {}
    for n, page in enumerate(data):
        maiLetters[index2page(n)] = re.findall(r'\[.\]', page) #assuming there is no more than 10 per pageindex
        data[n] = re.sub(r'\[.\]', 'M', page).replace(' M ', ' M')
    return data

def anshei(data):
    ansheiLetters = {}
    for n, page in enumerate(data):
        page = page.replace('#', '@67').replace('$@67', '@67')
        ansheiLetters[index2page(n)] = re.findall(r'\(@67[^\)]*?\)', page)
        data[n] = re.sub(r'\(@67[^\)]*?\)', 'N', page).replace(' N ', ' N')
    return data

def commentaries(data):
    data = shiltei(data)
    data = einmishpat(data)
    for tag in ['@15', '@17', '@18', '@19', '*?']:
        data = [page.replace(tag, '') for page in data]
    data = bach(data)
    data = choi(data)
    data = mai(data)
    data = anshei(data)
    data = [cleanspaces(page) for page in data]
    return data

def parse_text(masechet):
    with open(masechet+'.txt', encoding = 'utf-8') as file:
        data = file.read()

    global links
    global gemararefs
    links = []
    data = cleanspaces(data.replace('@99', '').replace('?*', ''))
    if '*' in data: print('* in data')
    data = markSections(data)
    data, gemararefs, comments = notes(data)
    data = big(data)
    data = data.split('@20')[1:]
    data = commentaries(data)
    if re.findall(r'@(.[^0]|[^0]0)', ' '.join(data)) != []:
        print('@ still in data', re.findall(r'@(.[^0]|[^20]0)', ' '.join(data)))
    for letter in '#$%&^?123456789':
        if letter in ' '.join(data): print(letter, 'in data')
    starts = []
    ends = []
    for m, amud in enumerate(data):
        amud = amud.split('A')
        amud = [section for section in amud if section != '']
        for n, section in enumerate(amud):
            if '@00' in section:
                starts.append([m,n, section.replace('@00', '').strip()])
                amud[n] = section.replace('@00', '<b>') + '</b>'
            elif section.count(' ') < 6 and n != len(amud)-1 and (n > 0 or data[m-1][-1][-1] == ':'):
                if '@00' not in amud[n+1]:
                    amud[n] = cleanspaces(amud[n] + ' ' + amud[n+1])
                    amud.pop(n+1)
            amud[n] = getLinks(m, n, amud[n])
        data[m] = amud
    for m,n,o in starts[1:]:
        if n==0: ends.append([m-1, len(data[m-1])-1])
        else: ends.append([m, n-1])
    ends.append([len(data), len(data[-1])])
    ind = createindex(masechet)
    ind["alt_structs"] = {'Chapters': {'nodes': create_alts(masechet, starts, ends)}}

    functions.post_index(ind, server = server)
    version = {
        'versionTitle': 'Vilna Edition',
        'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH001300957/NLI',
        'language': 'he',
        'text': data
    }
    functions.post_text('Rif '+masechet, version, server=server)
    functions.post_link(links, server = server)

global masechet
masechet = 'Berakhot'
heb_masechet = Ref(masechet).index.get_title('he')
parse_text(masechet)
