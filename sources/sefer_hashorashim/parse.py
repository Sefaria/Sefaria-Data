import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import *
import re
from sources.functions import post_index, add_term, post_link
import csv

X=0

def create_lex(name, ind_title):
    if not Lexicon().load({'name': name}):
        l = Lexicon()
        l.name = name
        l.index_title = ind_title
        l.version_lang = l.to_language = 'he'
        l.language = 'heb'
        l.text_categories = []
        l.version_title = 'Sefer HaShorashim, Berlin 1847'
        l.should_autocomplete = True
        l.save()

def create_entry(parent, head, defin, prev, refs, rid):
    entry = LexiconEntry({'headword': head,
     'parent_lexicon': parent,
     'refs': refs,
     'rid': rid,
     'content': {'senses': [{'definition': defin}]}})
    if prev:
        entry.prev_hw = prev
    return entry

def sort_key(word):
    if not word:
        return ''
    word = re.sub('[^א-ת]', '', word)
    if word[-1] == word[-2]:
        word = word[:-1]
    return word

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
    for i in range(1488, 1515):
        letter = chr(i)
        if letter in 'םןץףך':
            continue
        hwm.append([letter, f'{addr}, {headwords.pop(0)}'])
    return hwm

def handle_refs(text):
    global X
    refs = []
    for ref in re.findall(r'\(([^\)]*)\)', text):
        try:
            r = Ref(ref)
        except InputError:
            try:
                new = re.sub('ככ|בב', 'כב', ref)
                r = Ref(new)
                text = text.replace(ref, new)
                ref = new
            except InputError:
                continue
        if not r.text('he').text:
            continue
        text = text.replace(f'({ref})', f'(<a class="refLink" href="{r.url}" data-ref="{r.normal()}">{ref}</a>)')
        refs.append(r.normal())
    return text, refs

if __name__ == '__main__':
    book = 'Sefer HaShorashim'
    bachur = 'Animadversions by Elias Levita on Sefer HaShorashim'
    data = list(csv.DictReader(open('data.csv', encoding='utf-8', newline='')))
    new_text = []
    entries = []
    first_heads = []
    links = []
    ghost = []
    prev = ''
    letter = ''
    create_lex(book, book)
    create_lex(bachur, book)
    run_letter = 0
    for row in data:
        addr, line = row['Index Title'], row[book]
        if 'Sefer HaShorashim, Letter ' in addr or 'Animadversions by Elias Levita, Letter' in addr:
            new_letter = re.findall('Letter (.+) ', addr)[0]
            parent = book if 'Sefer HaShorashim, Letter ' in addr else bachur
            if re.findall('ב(?:ני|ן) (?:ארבע|חמש) אותיות</strong>', line):
                entries[-1].content['senses'][0]['definition'] += f'<br><br>{line}'
                continue
            if 'נשלמה אות' in line:
                entries[-1].content['senses'][0]['definition'] += f'<br>{line}'
                continue
            if '\xa0\xa0\xa0' not in line:
                entries[-1].content['senses'][0]['definition'] += f'<br><br>{line}'
                continue
            head, defin = line.split('\xa0\xa0\xa0')
            head, defin = head.strip(), defin.strip()
            head = re.sub('[a-z\<\>\/]', '', head)
            defin = defin.replace('<strong> </strong>', ' ').replace('<strong></strong>', '').replace('(</strong>', '</strong>(').replace('<strong>)', ')<strong>')
            head, defin = head.strip(), defin.strip()
            defin, refs = handle_refs(defin)
            if new_letter != letter:
                first_heads.append(head)
                run_letter = run_letter % 22 + 1
                run = 0
            run += 1
            ridlen = 3 if parent == book else 2
            rid = f'{chr(run_letter+64)}{str(run).zfill(ridlen)}'
            letter = new_letter
            '''if [prev, head] != sorted([prev, head], key=sort_key):
                print(f'problem in order {head} comes after {prev}')'''
            if prev == head:
                head += '²' #not good for more than 2 identical headwords
            if prev:
                entries[-1].next_hw = head
            entries.append(create_entry(parent, head, defin, prev, refs, rid))
            for ref in refs:
                if Ref(ref).text('he').text:
                    links.append({'type': 'reference',
                           'refs': [f'{parent}, {head} 1', ref],
                           'auto': True,
                           'generated_by': 'sefer hashorashim linker'})
                else:
                    ghost.append([f'{parent}, {head} 1', ref])
            prev = head
        else:
            new_text.append(row)
            prev = ''

    server = 'http://localhost:9000'
    #server = 'https://shorashim.cauldron.sefaria.org'
    add_term(book, 'ספר השרשים', server=server)
    add_term(bachur, 'נימוקי רבי אליהו בחור על ספר השרשים', server=server)

    record = SchemaNode()
    record.add_primary_titles(book, 'ספר השרשים')
    record.append(make_node('Introduction', 'הקדמה'))
    record.append(dict_node('אבב', 'תחרה', map_headwords(first_heads[:22], book), book))
    node = make_node('Biblical Aramaic Lexicon', 'פירוש למילות ארמית בספרי תנ"ך', typ='schema')
    node.append(make_node('Introduction', 'הקדמה'))
    for names in [["Genesis", "בראשית"], ["Jeremiah", "ירמיה"], ["Daniel", "דניאל"], ["Ezra", "עזרא"]]:
        node.append(make_node(*names, depth=3))
    record.append(node)
    record.append(make_node('Conclusion', 'סוף דבר'))
    '''node = make_node('Animadversions by Elias Levita', "נימוקים שהוסיף ר' אליהו אשכנזי", typ='schema')
    node.append(dict_node('אבב', 'תרף', map_headwords(first_heads[22:], f'{bachur}'), bachur))
    record.append(node)'''
    index_dict = {
        "title": book,
        "categories": ['Reference', 'Dictionary'],
        #'lexiconName': 'Sefer HaShorashim',
        #"dependence": "Commentary",
        #'base_text_titles': ['Genesis', 'Jeremiah', 'Daniel', 'Ezra'],
        "schema": record.serialize()}
    post_index(index_dict, server=server)

    record = SchemaNode()
    record.add_primary_titles(bachur, 'נימוקי רבי אליהו בחור על ספר השרשים')
    record.append(dict_node('אבב', 'תרף', map_headwords(first_heads[22:], f'{bachur}'), bachur,))
    index_dict = {
        "title": bachur,
        "categories": ['Reference', 'Dictionary'],
        #"dependence": "Commentary",
        #'base_text_titles': ['Sefer HaShorashim'],
        "schema": record.serialize()}
    post_index(index_dict, server=server)

    for entry in entries:
        if not LexiconEntry().load({'parent_lexicon': entry.parent_lexicon, 'headword': entry.headword}):
            entry.save()

    #post_link(links, server=server, skip_lang_check=False, VERBOSE=False)

    with open('new.csv', 'w', encoding='utf-8', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['Index Title', book])
        w.writeheader()
        for row in new_text:
            w.writerow(row)

    open('ghostlinks.txt', 'w', encoding='utf-8').write('\n'.join(['; '.join(g) for g in ghost]))

print(X)
