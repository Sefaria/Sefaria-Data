import django
django.setup()
import re
import json
from data_utilities.ParseUtil import ParsedDocument, Description, ParseState
from sefaria.utils.talmud import section_to_daf, daf_to_section
from data_utilities.dibur_hamatchil_matcher import match_ref
from rif_utils import remove_metadata, get_hebrew_masechet, tags_map, path, hebrewplus, cleanspaces
from sefaria.model import *

global MASECHET
global MEFARESH
REPORT = []
EMPTIES = {'Pesachim': ['18b'], 'Nedarim': ['4a'], 'Avodah Zarah': ['36a'], 'Menachot': ['10b'], 'Chullin': ['43b', '44a']}
PARSING_STATE = ParseState()

def dh_by_keyword(string: str, keyword: str, max: int, included=True) -> str:
    if keyword in string and string.index(keyword) > 2:
        dh = string.split(keyword, 1)[0]
        if included: dh += keyword
        if len(dh.split()) < max+1: return dh

def find_dh(par, report=True):
    dot_split = par.split('.')[:-1]
    for n, dot in enumerate(dot_split):
        dh = '.'.join(dot_split[:n+1]) + '.'
        if re.findall(r'[\(\[][^\)\]]*\.$', dh) == [] and len(dh.split())<21:  #finding this regex means dot is in parens means ref
            return dh
    for keyword in [[ "וכו'", 20], [ 'כלומר', 8, False]]:
        dh = dh_by_keyword(par, *keyword)
        if dh: return dh
    if report: REPORT.append(par)
    return ''

def split_dh(dh):
    return re.split(" וכו'| כו'", dh)

def base_tokenizer(string):
    string = remove_metadata(string, MASECHET)
    string = re.sub(r'<sup>.*?<\/i>', '', string)
    string = re.sub('<[^>]*>|\([^)]*\)', '', string)
    return string.split()

def parse_pages(doc: str) -> list:
    doc = doc.replace('\u05c3', ':')
    doc = re.sub('[\xa0\u2003\t]', ' ', doc)
    doc = re.sub('\(\*\)|\*\)|@66[א-ת]\)', '', doc)
    doc = re.sub(r'@88\[([^\]]*)\]@55', r'\(\1\)', doc) #@88 mark refs in brackets in some files
    doc = hebrewplus(doc, r'\(\)\[\].:,"\'#@%0123456789\-\*\$')
    for brac in set(re.findall(r'\[([^\[\]]*)\]', doc)): #handling in bracked refs in other files
        if library.get_refs_in_string('(' + brac.replace('דף', '') + ')') != []:
            doc = doc.replace('['+brac+']', '('+brac+')')
    doc = doc.replace('@@', '@@##') #the ## tag for the printed pages which the mefarshim tags numbering depends on
    doc = cleanspaces(doc)
    doc = doc.replace(': @@', ':@@').replace(':', ':A')
    doc = re.sub('(0[^A@]*)@', r'\1A@', doc) #hadran has no colon but marks new segment
    while re.search(r'([\(\[][^\)\]]*)A([^\)\]]*[\)\]])', doc):
        doc = re.sub(r'([\(\[][^\)\]]*)A([^\)\]]*[\)\]])', r'\1\2', doc) #colon in parens or brackets is part of ref
    doc = re.sub('([^A])@@(?![^A]*@@)([^A]*A)', r'\1\2@@', doc) #splitted dh shuld be in its first page
    doc = re.sub(r'@@ ?(0[^A@\d]*[A])', r'\1@@', doc) #hadran shouldnt open a page
    middles = re.findall('.{0,10}[^A@]@@..', doc)
    if middles != []:
        print('@@ in middle of page', middles)
        for middle in middles:
            if '@@@@' not in middle: #that probably mean a one dh on 3 pages, so we need one empty page
                doc = re.sub(middle+'(.*?@@)', middle.replace('@@', '')+r'\1@@', doc)

    pages = doc.split('@@')
    while pages[0] == '': pages.pop(0)
    while pages[-1] == '': pages.pop()
    if MASECHET in EMPTIES: #mefaresh on page without rif is a continiuos dh from prev. page
        if MASECHET == 'Pesachim': #page also has no mefaresh
            pages = pages[:35] + [''] + pages[35:]
        else:
            for daf in reversed(EMPTIES[MASECHET]): #reverse for consicutive empty pages
                daf = daf_to_section(daf) - 1
                pages[daf-1] += ' ' + pages[daf]
                pages[daf] = ''
    return pages

def parse_paragraphs(page: str) -> list:
    if page == '': return [{'text': '', 'link': {}}]
    page = re.sub('[0@]', '', page)
    pars = page.split('A')
    while pars[-1] == '': pars.pop()

    daf = section_to_daf(PARSING_STATE.get_ref('page')+1)
    rif_text = Ref('Rif {} {}'.format(MASECHET, daf)).text('he')
    if rif_text.text == []: print(daf)
    links = []
    if pars != ['']:
        matches = match_ref(rif_text, pars, base_tokenizer, dh_extract_method=find_dh, char_threshold=0.24, dh_split=split_dh)["matches"]
        for n, match in enumerate(matches):
            if match:
                links.append({
                "refs": ["{} {}:{}".format(title, daf, n+1), match.tref],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'rif mefaresh matcher'
                })
            else:
                links.append({})
    else:
        links.append({})
    while len(pars) > len(links): #a bug in match_ref
        print(daf, len(pars), len(links), matches)
        links.append({}) #temporal patch for the text. lnks stll can be off

    pars = [{'text': pair[0], 'link': pair[1]} for pair in zip(pars, links)]

    for n, par in enumerate(pars):
        dh = find_dh(par['text'], report=False).strip()
        if dh != '':
            if '.' not in dh:
                pars[n]['text'] = pars[n]['text'].replace(dh, '<b>'+dh+'.</b>')
            else:
                pars[n]['text'] = pars[n]['text'].replace(dh, '<b>'+dh+'</b>')
        else:
            pars[n]['link'] = {}

    return pars

descriptors = [
    Description('page', parse_pages),
    Description('paragraph', parse_paragraphs)
]

for MASECHET in tags_map:
    print(MASECHET)
    REPORT.append(MASECHET)
    MEFARESH = [mef for mef in ['Ran', 'Nimmukei Yosef', 'Rabbenu Yehonatan of Lunel', 'Rabbenu Yonah'] if tags_map[MASECHET][mef] == 'Digitized' or tags_map[MASECHET][mef] == 'shut'][0]
    hmefarshim = {'Ran': 'ר"ן', 'Nimmukei Yosef': 'נימוקי יוסף', 'Rabbenu Yehonatan of Lunel': "ר' יהונתן מלוניל", 'Rabbenu Yonah': 'תלמידי רבינו יונה'}
    hmasechet = get_hebrew_masechet(MASECHET)
    hmefaresh = hmefarshim[MEFARESH]
    title = '{} on Rif {}'.format(MEFARESH, MASECHET)
    htitle = '{} על רי"ף {}'.format(hmefaresh, hmasechet)
    with open(path+'/Mefaresh/splited/{}.txt'.format(MASECHET), encoding='utf-8') as fp:
        data = fp.read()

    parsed_doc = ParsedDocument(title, htitle, descriptors)
    parsed_doc.attach_state_tracker(PARSING_STATE)
    parsed_doc.parse_document(data)
    data = parsed_doc.get_ja()
    text = [[item['text'] for item in page] for page in data]
    links = [item['link'] for page in data for item in page if item['link']!={}]

    with open(path+'/Mefaresh/json/{}.json'.format(MASECHET), 'w') as fp:
        json.dump(text, fp)
    with open(path+'/Mefaresh/json/{}_links.json'.format(MASECHET), 'w') as fp:
        json.dump(links, fp)

with open('mefaresh_report.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(REPORT))
