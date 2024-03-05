import os
import re
import shutil
from collections import OrderedDict

from bs4 import BeautifulSoup, Tag, NavigableString
import django
django.setup()
from sources.functions import post_text

#can be used for manual inspecting of data
TOOL = set()
ENDNOTE_NUM = 0
TITLE = 'Tikkunei Zohar'
COMMENTRATOR = 'Endnotes'
FIRST_IMAGE_NUM = 40

MARKERS = {
    'infinity': {'class': 'infinity', 'original_regex': '∞', 'new_symbol': '∞'},
    'triangle': {'class': 'triangle', 'original_regex': '(?:|r)', 'new_symbol': '△'},
    'sefira': {'class': 'stars', 'original_regex': '', 'new_symbol': '☉'},
    'letter': {'class': 'stars', 'original_regex': '', 'new_symbol': '❖'},
}
def replace_marker(old):
    for marker in MARKERS:
        if re.search(MARKERS[marker]['original_regex'], old):
            return MARKERS[marker]['new_symbol']

def get_class(element):
    if isinstance(element, Tag):
        return element.get('class', None)

def strip_whitespaces_without_breaks(nav_strings):
    remove_first_space = True
    for i, string in enumerate(nav_strings):
        if not string or string.decomposed:
            continue
        new_string = ' '.join(string.split())
        if string.startswith(' ') and not remove_first_space:
            new_string = f' {new_string}'
        if string.endswith(' '):
            remove_first_space = True
            if string != ' ':
                new_string = f'{new_string} '
        else:
            remove_first_space = False
        new = NavigableString(new_string)
        string.replace_with(new)
        nav_strings[i] = new
    for string in nav_strings[::-1]:
        new_string = string.rstrip()
        string.replace_with(NavigableString(new_string))
        if string != '':
            break

def strip_whitespaces(tag, p_tag=True):
    def is_stringy(e):
        return isinstance(e, NavigableString) or e.name == 'br'
    elements = []
    for element in tag.descendants:
        if not is_stringy(element):
            continue
        if p_tag and element.name in ['sup', 'i']: #footnote or inline
            continue
        if element.name == 'br':
            strip_whitespaces_without_breaks(elements)
            elements = []
        else:
            elements.append(element)
    strip_whitespaces_without_breaks(elements)

def has_class(element, class_names):
    return any(clas in class_names for clas in element.get('class', []))

def is_grey(element):
    grey_classes = ['grey-text', 'grey-text-italic', 'hebrew-grey', 'CharOverride-13', 'CharOverride-23', 'CharOverride-26', 'CharOverride-39', 'CharOverride-43', 'grey-dot-italic']
    return has_class(element, grey_classes)

def is_italic(element, vol):
    has_explicit_italic = any('it-text' in class_ for class_ in element.get('class', [])) or any('italic' in class_ for class_ in element.get('class', []))
    other_italic_classes = ['RS_I---footnote-text']
    italic_by_vol = {2: [f'CharOverride-{x}' for x in [3, 5, 8, 14, 23, 37]]}
    return has_explicit_italic or has_class(element, other_italic_classes+italic_by_vol.get(vol, []))

def is_bold(element, vol):
    has_explicit_bold = any('bd' in class_ for class_ in element.get('class', []))
    bold_by_vol = {2: [f'CharOverride-{x}' for x in [8, 9, 37]]}
    return has_explicit_bold or has_class(element, bold_by_vol.get(vol, []))

def is_big(element, vol):
    has_explicit_big = any('large' in class_ for class_ in element.get('class', []))
    big_by_vol = {2: [f'CharOverride-{x}' for x in [40, 41]]}
    return has_explicit_big or has_class(element, big_by_vol.get(vol, []))

def is_not_big(element):
    return 'smaller-text-in-chapter-title' in element.get('class', [])

def is_hebrew(element):
    return any('hebrew' in class_ for class_ in element.get('class', [])) or element.get('lang') == 'he-IL'
def replace_element_with_styles(element, vol, version_lang):
    if isinstance(element, NavigableString):
        return
    outer = inner = soup.new_tag('p')
    tags = OrderedDict({
        'em': is_italic(element, vol),
        'b': is_bold(element, vol),
        'big': is_big(element, vol),
        'small': is_not_big(element),
        'span': is_grey(element)
    })
    for tag in tags:
        if tags[tag]:
            new = soup.new_tag(tag)
            if tag == 'span':
                new['class'] = 'mediumGrey'
            inner.append(new)
            inner = new
    if version_lang == 'english' and is_hebrew(element):
        new = soup.new_tag('span', dir='rtl')
        inner.append(new)
        inner = new
    for i in range(len(element.contents)):
        inner.append(element.contents[0])
    element.replace_with(*outer.contents)

def get_all_elements_for_note(first_element):
    notes = 1
    elements = [first_element]
    next = first_element.next_sibling
    while get_class(next) and get_class(next)[0] in [MARKERS[x]["class"] for x in MARKERS]:
        elements.append(next)
        next = next.next_sibling
        notes += 1
    current = elements[-1]
    while notes > 0:
        max_elements_for_note = 9 #maybe this is risky, and can take more than one note?
        for _ in range(max_elements_for_note):
            current = current.next_sibling
            if not current or current.name == 'br':
                return
            elements.append(current)
            if '›' in str(current):
                break
        if '›' not in str(current):
            return #something is wrong with data
        notes -= 1
    return elements

def handle_note(elements, vol):
    post_elements = []
    endnotes = []
    testing_string = ''
    state = 'marker'
    markers = []
    notes = []
    for element in elements:
        if isinstance(element, Tag) and element['class']:
            string = element.string
            if 'grey-text' in element['class']:
                get_new_element = lambda x: soup.new_tag('span', **{'class': 'mediumGrey'})
                #sometimes grey. sometimes wrong, but without damage like on space or ‹
            elif 'er' in element['class'] or 'ENR' in element['class']:
                endnotes.append(element)
                continue #end note, should be removed after the note
            elif is_italic(element, vol):
                get_new_element = lambda x: soup.new_tag('em') #italics. the second condtion if for letter with dot that is in italic
            elif any('hebrew' in class_ for class_ in element['class']) or element.get('lang') == 'he-IL':
                get_new_element = lambda x: soup.new_tag('span', dir='rtl')
            elif any('dot' in class_ for class_ in element['class']):
                get_new_element = lambda x: NavigableString(x) #a latin letter with dot
            elif not string.strip() or string.strip() in '‹∞›':
                get_new_element = lambda x: NavigableString(x)
            else:
                get_new_element = lambda x: NavigableString(x)
        else:
            string = element
            if string.strip() == ',':
                post_elements.append(NavigableString(','))
                continue
            get_new_element = lambda x: NavigableString(x)
        testing_string += string

        for substring in re.split('([‹›])', string):
            if not substring:
                continue

            new_element = get_new_element(substring)
            if isinstance(new_element, Tag):
                new_element.string = substring
            if substring == '‹':
                state = 'note <'
            elif substring == '›':
                state = 'unknown'

            elif state == 'marker':
                if re.search('^[r∞]*$', substring):
                    markers += [x.replace('r', '') for x in substring.strip()]
                elif not substring.strip():
                    continue
                elif re.search('[∞]', substring):
                    print(555, substring, elements)
                else:
                    post_elements.append(new_element)
            elif state == 'note <':
                if re.search('^[r∞]$', substring):
                    new_note = soup.new_tag('i', **{'class': 'footnote'})
                    notes.append({substring[0].replace('r', ''): new_note})
                    state = 'note'
                else:
                    print('starting ‹ with another thing', substring)
            elif state == 'note':
                if re.search('^[∞]$', substring): # or substring=='r': #this is noted out for unique case of one r that is the real element
                    print('unexpected characters', substring, elements)
                new_note.append(new_element)
            else:
                post_elements.append(new_element)

    new = []
    for marker in markers:
        sup = soup.new_tag('sup', **{'class': 'footnote-marker'})
        sup.string = replace_marker(marker)
        new.append(sup)
        try:
            note = [n[marker] for n in notes if marker in n][0]
        except:
            print(555, marker, notes, elements)
        else:
            notes.remove({marker: note})
            strip_whitespaces(note, False)
            new.append(note)
    if notes:
        print('too many notes', elements)

    testing_string = testing_string.strip()
    if testing_string[-1] == ',':
        testing_string = testing_string[:-1]
    if len(re.findall('^[∞r]*', testing_string)[0]) != len(re.findall('‹[^›]*›', testing_string)):
        print('problem with notes', testing_string, elements)

    if None in new:
        print(new + post_elements + endnotes, elements)
    return new + post_elements + endnotes

def strip_before(element):
    prev = element.previous_sibling
    if isinstance(prev, NavigableString):
        new = prev.rstrip()
        prev.replace_with(new)
    elif prev.string:
        prev.string = prev.string.rstrip()

def house_keep(string):
    string = string.replace('</em><em>', '')
    string = re.sub('\{([^\}]*)\}', r' (\1) ', string)
    return ' '.join(string.split())

def space_notes(segment):
    reg = '(?:<sup |<i data-commentator).*?</i>'
    start_reg = '[,\.:!;’]'
    parts = re.split(f'({reg}|<br>|<img.*?>)', segment)
    string = ''
    first = True
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.search(reg, part):
            string += part
        elif first:
            string += part
            first = False
        elif part == '<br>':
            string = string.strip() + part
            first = True
        else:
            string += f' {part}'
    string = re.sub(f' ({start_reg})', r'\1', string)
    return string.strip()

def stringify(element):
    p_tag = soup.new_tag('p')
    title_classes = ['chapter-number-title-Hebrew', 'chapter-number-title']
    if any(title in element['class'] for title in title_classes):
        big_tag = soup.new_tag('big')
        for  i in range(len(element.contents)):
            big_tag.append(element.contents[0])
        p_tag.append(big_tag)
    else:
        for i in range(len(element.contents)):
            p_tag.append(element.contents[0])
    strip_whitespaces(p_tag)
    string = str(p_tag)[3:-4]
    string = space_notes(string)
    string = house_keep(string)
    return string

IMAGES = {}
def handle_images(html, volume_num):
    global FIRST_IMAGE_NUM, IMAGES
    for img in html.find_all('img'):
        src = img['src']
        if src not in IMAGES:
            file = src.split('/')[-1]
            path = f'new data/vol {volume_num}/image/{file}'
            if not os.path.exists(path):
                print('missing file', path)
                return
            else:
                shutil.copy2(path, f'new data/images/{FIRST_IMAGE_NUM}.png')
                IMAGES[src] = f'https://textimages.sefaria.org/Tikkunei_Zohar/{FIRST_IMAGE_NUM}.png'
                FIRST_IMAGE_NUM += 1
        if img.parent.name == 'span':
            if len(img.parent.contents) > 1:
                if len(img.parent.contents) > 2 or img.parent.contents[1].string != ' ':
                    print('something in spam with image', img.parent.contents)
            img = img.parent
        new_img = soup.new_tag('img', src=IMAGES[src])
        img.replace_with(new_img)


class HeParagraph:

    def __init__(self, html, volume):
        self.volume = volume
        self.html = html

    def parse_elements(self):
        for element in self.html.find_all(True):
            for e in element.find_all(True):
                if e.name != 'br':
                    print(111, element.contents)
                    break
            if element.name in ['br', 'img']:
                continue
            if element.name == 'span' and element['class'] == ['rh-recto-Hebrew', 'CharOverride-7']:
                element.decompose()
                continue
            replace_element_with_styles(element, self.volume.num, 'hebrew')

    def remove_outer_redundant_tags(self):
        should_be_removed = lambda x: 'span' and len(x.contents)==1 and x.contents[0].name == 'img'
        for element in self.html.find_all(True):
            if should_be_removed(element):
                element_contents = element.contents
                element.replace_with(*element_contents)

    def parse(self):
        self.remove_outer_redundant_tags()
        handle_images(self.html, self.volume.num)
        self.parse_elements()

        self.string = stringify(self.html)


class EnParagraph:

    def __init__(self, html, volume):
        self.html = html
        self.volume = volume
        self.symbol_footnotes = []

    @staticmethod
    def is_note_first(element):
        for marker in MARKERS.values():
            if (isinstance(element, Tag) and element.string and element.has_attr('class') and
                    marker['class'] in element['class'] and re.search(marker['original_regex'], element.string)):
                return True

    def get_symbol_footnotes(self):
        next = self.html.next_sibling
        while next and (isinstance(next, NavigableString) or next.name != 'p'):
            if isinstance(next, Tag):
                fns = next.find_all('p', class_='side-notes')
                for fn in fns:
                    for element in fn.contents:
                        if self.is_note_first(element):
                            note = []
                            self.symbol_footnotes.append(note)
                        note.append(element)
            next = next.next_sibling

    def handle_symbol_footnotes(self):
        footnotes = self.symbol_footnotes[:]
        for i, element in enumerate(self.html.find_all(self.is_note_first)):
            if not element or element.decomposed:
                continue
            involved_elements = get_all_elements_for_note(element)
            if not involved_elements:
                print('problem with identifying elements')
                print(111, self.html)
                print(222, element)
                pass
            else:
                strip_before(involved_elements[0])
                new_elements = handle_note(involved_elements, self.volume.num)
                new_sups = [e for e in new_elements if isinstance(e, Tag) and e.name=='sup']
                new_is = [e for e in new_elements if isinstance(e, Tag) and e.name=='i' and e['class']==['footnote']]
                new_new_is = [] #this is ugly. i had parsed the notes from the p elements, and here i'm changing them to be from the div elements
                for sup, i_tag in zip(new_sups, new_is):
                    try:
                        content = footnotes.pop(0)
                        inline_data_string = ''.join(i_tag.strings)
                        post_data_string = ''.join([x.string.strip() for x in content[1:] if x.string])
                        inline_marker = sup.string
                        post_marker = replace_marker(content[0].string)
                        if inline_marker != post_marker:
                            print(333, inline_marker, post_marker, self.html)
                        # if inline_data_string != post_data_string:
                        #     print(222, inline_data_string, post_data_string, self.html)
                        new_i = soup.new_tag('i', **{'class': 'footnote'})
                        for e in content[1:]:
                            new_i.append(e)
                            replace_element_with_styles(e, self.volume.num, 'english')
                        strip_whitespaces(new_i, False)
                        # if str(i_tag) != str(new_i):
                        #     print(444, i_tag, new_i, self.html)
                        new_new_is.append(new_i)
                    except IndexError:
                        print('not enough notes', self.html, self.symbol_footnotes, new_elements)
                involved_elements[0].replace_with(*new_elements)
                for old, new in zip(new_is, new_new_is):
                    old.replace_with(new)
                for e in involved_elements[1:]:
                    if e not in new_elements:
                        if isinstance(e, Tag):
                            e.decompose()
                        else:
                            e.extract()
        if footnotes:
            print('redundant foonotes', self.html, self.symbol_footnotes)

    def handle_endnotes(self):
        def is_note(element):
            if isinstance(element, Tag):
                classes = element.get('class')
                if classes and any(c in classes for c in ['er', 'ENR']):
                    return True
        for note in self.html.find_all(is_note):
            global ENDNOTE_NUM
            # print(note)
            num = int(note.string)
            if num != ENDNOTE_NUM + 1:
                print(f'footnotes out of order: {num} comes after {ENDNOTE_NUM}')
            ENDNOTE_NUM = num
            new_tag = soup.new_tag('i', **{'data-commentator': COMMENTRATOR, 'data-order': num, 'data-label': num})
            note.replace_with(new_tag)

    def handle_footnotes(self):
        def is_footnote(element):
            return isinstance(element, Tag) and element.get('id') and 'endnote' in element.get('id')
        for a_tag in self.html.find_all('a'):
            note = self.volume.fn['parsed'].pop(a_tag.string)
            a_tag.replace_with(*note)

    def parse_elements(self):
        global TOOL
        #this loop is for checking after all previous methods work
        for element in self.html.find_all(True, recursive=False):
            if  element.name == 'i' and element.get('class') == ['footnote']:
                continue
            for e in element.find_all(True):
                if e.name not in ['em', 'i', 'br', 'sup', 'img']:
                    if e.name == 'span' and (e.get('dir') == 'rtl' or e.get('class') == ['mediumGrey']):
                        continue
                    # print(222, element, e, e.get('class'))
                    # TOOL.add(e.name)

        for element in self.html.find_all(True):
            if element.name in ['br', 'i', 'sup', 'img', 'em', 'big', 'b']: #i and sup for we onsert ours. in the first run we should check it maybe this is #todo for next times
                continue
            elif element.name == 'span':
                class_names = element.get('class', [])
                if 'mediumGrey' in class_names or element.get('dir') == 'rtl':
                    continue
                if class_names == ['rh-verso-ENGLISH', 'CharOverride-7']:
                    element.decompose() #double for the chapter title
                    continue
                if any(fnr in class_names for fnr in ['FNR---verse-English', 'FNR']): #wrap footnote
                    contents = element.contents
                    element.replace_with(*contents)
                    continue
                replace_element_with_styles(element, self.volume.num, 'english')
            else:
                print(f'unidentified element: {element}')

    def parse(self):
        self.get_symbol_footnotes()
        self.handle_symbol_footnotes()
        self.handle_endnotes()
        self.handle_footnotes()
        handle_images(self.html, self.volume.num)
        self.parse_elements()

        self.string = stringify(self.html)

class Volume:

    def __init__(self, en, he, fn, num):
        self.num = num
        self.en = {'html': en, 'p_elements': []}
        self.he = {'html': he, 'p_elements': []}
        self.fn = {'html': fn, 'parsed': {}}
        self.handle_footnotes()

    def handle_footnotes(self):
        for a in self.fn['html'].find_all('a'):
            sup = soup.new_tag('sup', **{'class': 'footnote-marker'})
            i_tag = soup.new_tag('i', **{'class': 'footnote'})
            footnote_marker = None
            for i in range(len(a.contents)):
                child = a.contents[0]
                if isinstance(child, Tag) and 'endnote-' in child.get('id', ''):
                    footnote_marker = str(child.string)
                    child.extract()
                    continue
                replace_element_with_styles(child, self.num, 'english')
                i_tag.append(a.contents[0])
            sup.string = footnote_marker
            strip_whitespaces(i_tag, False)
            if footnote_marker in self.fn['parsed']:
                print(f'double note: {footnote_marker}')
            self.fn['parsed'][footnote_marker] = [sup, i_tag]


    @staticmethod
    def is_chapter(element):
        return 'chapter-number-title' in element['class'][0]

    @staticmethod
    def is_daf(element):
        return element.name == 'div' and element.find_all(True) and 'daf' in element.find_all(True)[0]['class'][0]

    def split_paragraphs(self):
        daf, chapter = None, None
        for text in [self.en, self.he]:
            for child in text['html'].find_all(True, recursive=False):
                if self.is_chapter(child):
                    chapter = child.get_text()
                elif self.is_daf(child):
                    daf = child.get_text()

                if child.name == 'p': #todo - solve the problem of chapter title before daf
                    text['p_elements'].append({'chapter': chapter, 'daf': daf, 'html': child})

    def check_langs_alignment(self):
        # check that the transition of tikkunim and ammudim is identical. in many cases it's not and therefore we should find a way to validate it
        # for he1, he2, en1, en2 in zip(self.he['p_elements'], self.he['p_elements'][1:], self.en['p_elements'], self.en['p_elements'][1:]):
        #     for key in ['chapter', 'daf']:
        #         if (he1[key] == he2[key]) ^ (en1[key] == en2[key]):
        #             print(f'problem with alignment of {key}: {he1[key].strip()} {he2[key].strip()} {en1[key].strip()} {en2[key].strip()}')
        #             print(he2['html'], en2['html'])

        for he, en in zip(self.he['p_elements'], self.en['p_elements']):
            if len(he['html'].find_all('br')) != len(en['html'].find_all('br')):
                print(f'num of breaks is not equal\n{en}\n{he}')

    def parse(self):
        self.split_paragraphs()
        self.check_langs_alignment()

        # this is for manual printing of the chapters and dapim
        # chapters, dapim = [], []
        # for p in self.en['p_elements']:
        #     if p['chapter'] not in chapters: chapters.append(p['chapter'])
        #     if p['daf'] not in dapim: dapim.append(p['daf'])
        # print(1, chapters)
        # print(2, [x.strip() for x in dapim if x])

        for he_p in self.he['p_elements']:
            he_p['obj'] = HeParagraph(he_p['html'], self)
            he_p['obj'].parse()

        for en_p in self.en['p_elements']:
            en_p['obj'] = EnParagraph(en_p['html'], self)
            en_p['obj'].parse()

        if self.fn['parsed']:
            print('unused footnotes:', self.fn['parsed'])

def post(volumes):
    he_text = [[] for _ in range(32)] #TODO this assumes the volume starts with a page starting and that the first page is 16a
    en_text = [[] for _ in range(32)] #TODO this assumes the volume starts with a page starting and that the first page is 16a
    daf = ''
    for volume in volumes:
        for he, en in zip(volume.he['p_elements'], volume.en['p_elements']):
            if he['daf'].strip() != daf: # hebrew data for dapim is better
                he_text.append([])
                en_text.append([])
                daf = he['daf'].strip()
            he_text[-1].append(he['obj'].string)
            en_text[-1].append(en['obj'].string)
    text_dict = {
        'language': 'he',
        'versionTitle': 'Constantinople, 1740',
        'versionSource': 'https://margalya.com/pages/tz',
        'text': he_text
    }
    server = 'http://localhost:8000'
    # server = 'https://new-shmuel.cauldron.sefaria.org'
    post_text(TITLE, text_dict, server=server, index_count='on')
    text_dict['language'] = 'en'
    text_dict['versionTitle'] = 'Tiqqunei ha-Zohar, trans. by David Solomon. Margalya Press; Melbourne, 2024'
    text_dict['text'] = en_text
    post_text(TITLE, text_dict, server=server, index_count='on')


if __name__ == '__main__':
    vol_indexes = {
        2: {'en': 0, 'he': 1, 'fn': 2},
        3: {'en': 1, 'he': 2, 'fn': 0}
    }
    volumes = []
    for vol in range(2, 4):
        print(f'vol. {vol}')
        with open(f'new data/vol {vol}.html') as fp:
            soup = BeautifulSoup(fp, 'html.parser')
        en = soup.body.find_all('div', recursive=False)[vol_indexes[vol]['en']]
        he = soup.body.find_all('div', recursive=False)[vol_indexes[vol]['he']]
        fn = soup.body.find_all('div', recursive=False)[vol_indexes[vol]['fn']]
        volume = Volume(en, he, fn, vol)
        volume.parse()
        volumes.append(volume)

    post(volumes)

    print(TOOL)