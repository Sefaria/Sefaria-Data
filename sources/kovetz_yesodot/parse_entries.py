import copy

from bs4 import BeautifulSoup, NavigableString
import re
from collections import OrderedDict
import django
django.setup()
from sefaria.model import *

def has_lexic_order(word1, word2):
    for letter1, letter2 in zip(word1, word2):
        ord1, ord2 = ord(letter1), ord(letter2)
        if ord1 < ord2:
            return True
        if ord2 < ord1:
            return False
    if len(word1) < len(word2):
        return True
    elif len(word2) < len(word1):
        return False
    print(f'identical words? 1: {word1}; 2: {word2}')

def make_string(p_element):
    strings_to_skip = []
    new_element = soup.new_tag('p')
    for sub in list(p_element.descendants):
        if sub.name == 'b' or (sub.name and sub.get('style') == 'font-size:10.0pt'):
            b_tag = soup.new_tag('b')
            for string in list(sub.strings):
                b_tag.append(string)
                strings_to_skip.append(string)
            new_element.append(b_tag)
        elif isinstance(sub, NavigableString) and all(s is not sub for s in strings_to_skip):
            new_element.append(sub)
    line = str(new_element)[3:-4].replace(' ', ' ')
    line = ' '.join(line.split())
    for fn in re.findall('\[(\d+)\]', line):
        note = NOTES.pop(int(fn))
        line = line.replace(f'[{fn}]', f'<sup class="footnote-marker">{fn}</sup><i class="footnote">{note}</i>')
    return line

def join_string(element):
    return ' '.join(''.join(element.strings).replace(' ', ' ').split())


def get_notes(soup):
    notes = {}
    for n, note in enumerate(soup.find(class_='WordSection34').next_sibling.next_sibling.find_all('div'), 1):
        if note['id'] != f'ftn{n}':
            print(f'note should be {n} but has id {note["id"]}')
        text = join_string(note)
        if re.search(f'\[{n}\]', text):
            text = re.sub(f'\[{n}\]', '', text)
        else:
            print(n, note)
        notes[n] = text
        if not notes[n]:
            print(f'nothing in note: {n}')
    return notes

def make_objects(entries):
    vtitle = 'Netanya, 2023'
    lex = Lexicon({
        'name': TITLE,
        'to_language': 'he',
        'language': 'heb',
        'version_lang': 'he',
        'index_title': TITLE,
        'version_title': vtitle,
        'text_categories': [],
        'should_autocomplete': True
    })
    # lex.save()

    titles = [
            {
                'lang': "en",
                'primary': True,
            },
            {
                'lang': "he",
                'primary': True,
            }
        ]
    regular_node = {
        'nodeType': 'JaggedArrayNode',
        'depth': 1,
        'addressTypes': [
            "Integer"
        ],
        'sectionNames': [
            "Paragraph"
        ],
        'titles': copy.deepcopy(titles),
    }
    # index = {
    #     'nodes': [
    #         copy.deepcopy(regular_node) for _ in range(22)
    #     ],
    #     'titles': copy.deepcopy(titles),
    #     'toc_zoom': 1
    # }
    index = {
        'nodeType': 'JaggedArrayNode',
        'depth': 2,
        'addressTypes': [
            "Integer", "Integer"
        ],
        'sectionNames': [
            "Section", "Paragraph"
        ],
        'titles': copy.deepcopy(titles),
    }
    index['titles'][0]['text'] = index['key'] = 'Index'
    index['titles'][1]['text'] = 'מפתח'
    # letters = [x for x in 'אבגדהוזחטיכלמנסעפץקרשת']
    # eng_letters = ["Alef", "Bet", "Gimel", "Daled", "Heh", "Vav", "Zayin", "Chet", "Tet", "Yod", "Kaf", "Lamed", "Mem", "Nun", "Samekh",
    #                 "Ayin", "Peh", "Tzadi", "Kof", "Resh", "Shin", "Tav"]
    # for i, node in enumerate(index['nodes']):
    #     node['titles'][0]['text'] = node['key'] = eng_letters[i]
    #     node['titles'][1]['text'] = letters[i]

    intro = copy.deepcopy(regular_node)
    intro['titles'][0]['text'] = intro['key'] = 'Introduction'
    intro['titles'][1]['text'] = 'הקדמה'
    fore = copy.deepcopy(regular_node)
    fore['titles'][0]['text'] = fore['key'] = 'Foreword'
    fore['titles'][1]['text'] = 'מבוא'

    index = Index(
        {
            'title': TITLE,
            'categories': ['Reference', 'Encyclopedic Works'],
            'schema': {'nodes': [
                index,
                intro,
                fore,
                {
                    'nodeType': 'DictionaryNode',
                    'lexiconName': TITLE,
                    'firstWord': list(entries)[0],
                    'lastWord': list(entries)[-1],
                    'headwordMap': headwordMap,
                    'default': True,
                }
            ],
                'titles': [
                    {'text': TITLE, 'lang': 'en', 'primary': True},
                    {'text': 'קובץ יסודות וחקירות', 'lang': 'he', 'primary': True},
                ],
                'key': TITLE
            },
            'lexiconName': TITLE,
        }
    )
    index.save()

    version = Version({
        'title': TITLE,
        'versionTitle': vtitle,
        'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH990050798900205171/NLI',
        'language': 'he',
        'chapter': {'Index': index_text,'Introduction': ['א'], 'Foreword': ['א']}
    })
    # version.save()

    length = len(entries)
    for i, headword in enumerate(entries):
        le = LexiconEntry({
            'headword': headword,
            'content': entries[headword],
            'rid': f'K{str(i).zfill(len(str(length)))}',
            'parent_lexicon': TITLE
        })
        if i != 0:
            le.prev_hw = list(entries)[i-1]
        if i != length - 1:
            le.next_hw = list(entries)[i+1]
        # le.save()

def make_link(shown, inside, scroll=False):
    data_ref = f'{TITLE}, {inside}'
    href = data_ref.replace(' ', '_')
    link_start = f'<a class="refLink" data-ref="{data_ref}" href="{href}"'
    link_end = f'>{shown}</a>'
    return f'{link_start} data-scroll-link="true"{link_end}' if scroll else f'{link_start}{link_end}'

def add_cross_links(line):
    line_for_index = line
    start = '</b>'.join(line[:-1].split('</b>')[:-1])
    linked_hw = [x for x in line[:-1].split('</b>')[-1].split(',')]
    new_hws = []
    new_hws_for_index = []
    for hw in linked_hw:
        if ' בסעיף' in hw:
            hw, hw_suffix = hw.split(' בסעיף')
            hw_suffix = ' בסעיף' + hw_suffix
        else:
            hw_suffix = ''
        hw_prefix = ''
        hw = hw.strip()
        target = hw
        target = target.strip()
        if target not in headwords:
            if target == 'בעל המקח דיין וחיה':
                target = 'בעל המקח, דיין וחיה'
            elif headword == 'חצי אדם':
                new_hws.append(f'{hw}{hw_suffix}')
                new_hws_for_index.append(f'{hw}{hw_suffix}')
                continue
            elif target == 'כל מילתא דאמר רחמנא לא תעביד':
                target = 'כל מילתא דאמר רחמנא לא תעביד אי עביד לא מהני'
            elif target == 'דרבנן שיש לו עיקר מן התורה':
                target = 'דרבנן שיש לו עיקר מהתורה'
            elif target == 'כח':
                target = 'כח כחו'
            elif target == 'מיתה':
                target = 'מיתה בידי שמיים'
            else:
                if '(' in target:
                    hw, suf = target.split('(', 1)
                    hw_suffix = ' (' + suf + hw_suffix
                if 'וערך' in target:
                    hw_prefix, hw = hw.split('וערך')
                    hw_prefix += 'וערך '
                hw = hw.strip()
                target = hw
                if target not in headwords:
                    options = [h for h in headwords if h.startswith(f'{target} (')]
                    if len(options) != 0:
                        target = options[0]
                    else:
                        print(headword, target, options)
                        new_hws.append(f'{hw_prefix}{hw}{hw_suffix}')
                        new_hws_for_index.append(f'{hw_prefix}{hw}{hw_suffix}')
                        continue

        new_hws.append(hw_prefix + make_link(hw, target) + hw_suffix)
        new_hws_for_index.append(make_link(hw_prefix + hw, target, True) + hw_suffix)

    line = start.strip() + ' ' + ', '.join(new_hws) + line[-1]
    line_for_index = start.strip() + ' ' + ', '.join(new_hws_for_index) + line[-1]
    return line, line_for_index


with open('kovetz.htm') as fp:
    soup = BeautifulSoup(fp.read(), 'html.parser')
word_sections = soup.find_all(class_=re.compile('WordSection\d+'))[11:33]
NOTES = get_notes(soup)
TITLE = 'Kovetz Yesodot VaChakirot'

headwords = OrderedDict()
headwordMap = []
first_iter = True
for word_sec in word_sections:
    first_in_letter = True
    for element in word_sec.children:
        if element.name in ['h2', 'h3']:
            headword = join_string(element).replace('-', '')
            headwords[headword] = {}
            # if not first_iter:
            #     if not has_lexic_order(prev_hw, headword):
            #         print(f'problem with headwords order: {prev_hw}; {headword}')
            first_iter = False
            if first_in_letter:
                headwordMap.append([headword[0], f'{TITLE}, {headword}'])
                first_in_letter = False
        elif element.name == 'p':
            line = make_string(element)
            if not line:
                continue
            if '-' in line:
                line = line.replace(' - ', ' – ')
                line = line.replace('ותקצט-א', 'ותקצט, א')
                while '-' in line:
                    new = re.sub('(?<![א-ת][א-ת][א-ת][א-ת])([א-ת\.\d\):])\-([א-ת\.\d:])(?![א-ת][א-ת][א-ת][א-ת])', r'\1, \2', line)
                    if new == line:
                        break
                    line = new
            if not headwords[headword]:
                title = 'reference'
                headwords[headword][title] = []
                if not line.startswith('<b>עיין'):
                    print(555, headword, line, element)
            if 'ערכים קרובים' in line:
                if not line.startswith('<b>ערכים קרובים</b>:') or title != 'ערכים קרובים':
                    print(headword, line)
                line = re.sub('^<b>ערכים קרובים</b>:', '', line).strip()
            headwords[headword][title].append(line)
        elif element.name == 'div':
            title = join_string(element)
            headwords[headword][title] = []

if NOTES:
    print(f'remaining notes: {list(NOTES)}')

index_text = []
#this promie that all the emtries that starts with reference are only reference of one line
for headword in headwords:
    if not index_text or re.findall('[א-ת]', index_text[-1][-1])[0] != headword[0]:
        index_text.append([])
    if 'reference' in headwords[headword]:
        if len(headwords[headword]) > 1 or len(headwords[headword]['reference']) > 1:
            print(headword, headwords[headword])

        line, line_for_index = add_cross_links(headwords[headword]['reference'][0])
        headwords[headword]['reference'][0] = line
        index_text[-1].append(f"{headword} {re.sub('</?b>', '', line_for_index)}")
    else:
        index_text[-1].append(make_link(headword, headword, True))

    if 'ערכים קרובים' in headwords[headword]:
        if len(headwords[headword]['ערכים קרובים']) != 1:
            print(88888)
        line, _ = add_cross_links(headwords[headword]['ערכים קרובים'][0])
        headwords[headword]['ערכים קרובים'][0] = line

make_objects(headwords)
