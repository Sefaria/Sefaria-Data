import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import *
from sources.functions import post_index, add_term, post_link, post_text
from bs4 import BeautifulSoup

LETTERS = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ', 'ק', 'ר', 'שׂ',
           'שׁ', 'ת']


def make_node(name, hname, typ='ja', depth=1):
    node = JaggedArrayNode() if typ == 'ja' else SchemaNode()
    node.add_primary_titles(name, hname)
    if typ == 'ja':
        if depth == 1:
            node.addressTypes = ['Integer']
            node.sectionNames = ['Paragraph']
        else:
            node.addressTypes = ['Integer', 'Integer', 'Integer']
            node.sectionNames = ["Chapter", "Verse", 'Paragraph', ]
        node.depth = depth
    node.validate()
    return node

def dict_node(first, last, hwm, name, titles=None):
    node = DictionaryNode({'lexiconName': name,
                           'firstWord': first,
                           'lastWord': last,
                           'headwordMap': hwm,
                           })
    if not titles:
        node.default = True
    else:
        node.add_primary_titles(*titles)
    return node

def map_headwords(headwords, addr):
    hwm = []
    print(headwords)
    for letter in LETTERS:
        hwm.append([letter, f'{addr}, {headwords.pop(0)}'])
    return hwm

if __name__ == '__main__':
    book = 'BDB'
    hebrew = 'בראון-דרייבר-בריגס'
    server = 'http://localhost:9000'
    # server = 'https://bdb.cauldron.sefaria.org'
    add_term(book, hebrew, server=server)

    record = SchemaNode()
    record.add_primary_titles(book, hebrew)
    first_heads = []
    i = 0
    for le in LexiconEntrySet({'parent_lexicon': 'BDB Dictionary'}):
        if le.headword and le.headword == LETTERS[i]:
            first_heads.append(le.headword)
            i += 1
            if i == 23:
                break
    record.append(dict_node('א', 'תִּשְׁעִים', map_headwords(first_heads, book), 'BDB Dictionary'))
    record.append(make_node('Preface', 'הקדמה'))
    record.append(make_node('Abbrevations', 'רשימת קיצורים'))
    index_dict = {'lexiconName': 'BDB Dictionary',
        "title": book,
        "categories": ['Reference', 'Dictionary'],
        "schema": record.serialize()}
    post_index(index_dict, server=server)

    abook = 'BDB Aramaic'
    ahebrew = 'בראון-דרייבר-בריגס ארמית'
    add_term(abook, ahebrew, server=server)
    record = SchemaNode()
    record.add_primary_titles(abook, ahebrew)
    first_heads = []
    i = 0
    for le in LexiconEntrySet({'parent_lexicon': 'BDB Aramaic Dictionary'}):
        if le.headword[0] == LETTERS[i][0] and LETTERS[i][-1] in le.headword[:3]:
            first_heads.append(le.headword)
            i += 1
            if i == 23:
                break
    node = dict_node('אָב', 'תַּתְּנַי', map_headwords(first_heads, abook), 'BDB Aramaic Dictionary')
    record.append(node)
    record.append(make_node('Abbrevations', 'רשימת קיצורים'))
    index_dict = {'lexiconName': 'BDB Aramaic Dictionary',
        "title": abook,
        "categories": ['Reference', 'Dictionary'],
        "schema": record.serialize()}
    post_index(index_dict, server=server)

    with open('01-preface.html') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
    text = [p.decode_contents() for p in soup.find_all('p')]
    text = [' '.join([re.sub('^(.*?)(\)?[;\.,]?)$', r'<span dir ="rtl">\1</span>\2', word) if re.search('[א-ת]', word) else word for word in par.split()]) for par in text]
    text_version = {
            'versionTitle': 'BDB Dictionary',
            'versionSource': '',
            'language': 'en',
            'text': text}
    post_text(f'{book}, Preface', text_version, server=server, index_count='on')
    with open('02-abbr.html') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
    text = [p.decode_contents() for p in soup.find_all('p')] + [l.decode_contents() for l in soup.find_all('li')]
    text_version = {
            'versionTitle': 'BDB Dictionary',
            'versionSource': '',
            'language': 'en',
            'text': text}
    post_text(f'{book}, Abbrevations', text_version, server=server, index_count='on')
    post_text(f'{abook}, Abbrevations', text_version, server=server, index_count='on')

    links = []
    for le in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*? Dictionary'}}):
        for i, par in enumerate(le.as_strings(), 1):
            bref = f'{abook if "Aramaic" in le.parent_lexicon else book}, {le.headword}:{i}'
            for ref in set(re.findall(r'<a (?:href|data-ref)="(.*?)"', par)):
                try:
                    ref = Ref(ref.replace('/', '').replace('_', ' ')).normal()
                except InputError:
                    print(f'problem in {le.headword} with ref', ref.replace('/', '').replace('_', ' '))
                else:
                    links.append({'refs': [bref, ref],
                                  'auto': True,
                                  'type': 'reference',
                                  'generated_by': 'bdb parser'})
    for l in range(len(links) // 10000 + 1):
        post_link(links[l*10000:(l+1)*10000], server=server, skip_lang_check=False, VERBOSE=False)
