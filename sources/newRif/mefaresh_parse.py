import django
django.setup()
import re
from data_utilities.ParseUtil import ParsedDocument, Description, ParseState
from sefaria.utils.talmud import section_to_daf
from data_utilities.dibur_hamatchil_matcher import match_ref
from rif_utils import remove_metadata, get_hebrew_masechet

global masechet_paragraph_parser
global mefaresh

def find_dh(par):
    try:
        return re.findall(r'^[^\.]*\.', par)[0][:-1]
    except IndexError:
        print('no dh', dh)

def base_tokenizer(string):
    string = remove_metadata(string, masechet)
    string = re.sub(r'<sup>.*?<\/i>', '', string)
    string = re.sub('<[^>]*>|\([^)]*\)', '', string)
    return string.split()

def parse_pages(doc: str) -> list:
    doc = hebrewplus(doc, '()[].:,"\'#@')
    doc = re.sub(':[ \n]+@@', ':@@', doc)
    doc = re.sub('[^:]@@(?![^:]*@@)([^:]*:)', r'\1@@', doc)
    middles = re.findall('[^:@]@@', doc)
    if middles != []:
        print('@@ in middle of page', middles)
    pages = doc.split('@@')
    while pages[0] == '': pages.pop(0)
    while pages[-1] == '': pages.pop()
    return pages

def parse_paragraphs(page: str) -> list, list:
    page = page.replace('@', '')
    pars = [par + ':' if par != '' else '' for par in page.split(':')]
    daf = section_to_daf(parsing_state.get_ref('page')+1)
    rif_text = Ref('Rif {} {}'.format(masechet, daf)).text('he')

    links = []
    if page != ['']:
        matches = match_ref(rif_text, pars, base_tokenizer, dh_extract_method=find_dh)["matches"]
        for n, match in enumerate(matches):
            links.append({
            "refs": ["{} on Rif {} {}:{}".format(mefaresh, masechet, daf, n+1), match],
            "type": "Commentary",
            "auto": True,
            "generated_by": 'rif mefaresh matcher'
            })

    pars = [re.sub(r'(^[^\.]*\.)', r'<b>\1</b>', par) for par in pars]
    pars = [pair for pair in zip(pars, links)]

    return pars

descriptors = [
    Description('page', parse_pages),
    Description('paragraph', parse_paragraphs)
]

for masechet in tags_map:
    mefresh = [mef for mef in ['Ran', 'Nimmukei Yosef', 'R. Yehonatan of Lunel', 'Talmidei Rabenu Yonah'] if tags_map[masechet][mef] == 'Digitized'][0]
    hmefarshim = {'Ran': 'ר"ן', 'Nimmukei Yosef': 'נימוקי יוסף', 'R. Yehonatan of Lunel': "ר' יהונתן מלוניל", 'Talmidei Rabenu Yonah': 'תלמידי רבינו יונה'}
    hmasechet = get_hebrew_masechet(masechet)
    hmefaresh = hmefarshim[mefresh]
    title = '{} on Rif {}'.format(mefaresh, masechet)
    htitle = '{} על רי"ף {}'.format(hmefaresh, hmasechet)
    with open(path+'/Mefaresh/splted/{}.txt'.format(masechet), encoding='utf-8') as fp:
        data = fp.read()

    parsing_state = ParseState()
    parsed_doc = ParsedDocument(title, htitle, descriptors)
    parsed_doc.attach_state_tracker(parsing_state)
    parsed_doc.parse_document(data)
    data = parsed_doc.get_ja
    text, links = [item[0] for item in data], [item[1] for item in data]
