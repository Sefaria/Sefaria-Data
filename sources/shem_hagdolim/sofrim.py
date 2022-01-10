import time
import django
django.setup()
import re
import requests
from sources.functions import gematria, getGematria, post_link, post_index, post_text, add_term, add_category
from sefaria.model import *

def eng_letter(letter):
    eng_letters = ['Alef', 'Bet', 'Gimel', 'Dalet', 'He', 'Vav', 'Zayin', 'Chet', 'Tet', 'Yod', 'Kaf', 'Lamed', 'Mem', 'Nun', 'Samekh', 'Ayin', 'Peh', 'Tzadi', 'Kof', 'Resh', 'Shin', 'Tav']
    return eng_letters[sum([int(digit) for digit in str(getGematria(letter) - 1)])]

class Node():

    def __init__(self, name='', hname='', typ='schema', depth=2):
        self.name = name
        self.node = SchemaNode() if typ == 'schema' else JaggedArrayNode()
        if name:
            self.node.add_primary_titles(name, hname)
        else:
            self.node.key = 'default'
            self.node.default = True
        if type != 'schema':
            self.node.addressTypes = ['Seif', 'Section'][-depth:]
            self.node.sectionNames = ['Seif', 'Paragraph'][-depth:]
            self.node.depth = depth
        self.node.validate()


class Parser():

    def __init__(self):
        self.main = Node('Shem HaGedolim, Maarekhet Sefarim', 'שם הגדולים, מערכת ספרים')
        self.menachem = Node('Hagahot Menachem Tzion', 'הגהות מנחם ציון')
        self.sheerit = Node('Hagahot Sheerit Tzion', 'הגהות שארית ציון', 'ja')
        self.pletat = Node('Kuntres Peleitat Sefarim', 'קונטרס פליטת ספרים')
        node = Node('Introduction', 'הקדמה', 'ja', 1)
        self.pletat.node.append(node.node)
        self.texts = {}
        self.notes = {}
        self.intro = False
        self.links = []
        self.notes_sheerit = {}

    def check_and_add_to_texts(self, key):
        try:
            return self.texts[key]
        except KeyError:
            self.texts[key] = []
        return self.texts[key]

    def parse_page(self, letter, title):
        self.notes_menachem = {}
        with open(f'{letter}.html', encoding='utf-8') as fp:
            page = fp.read()
        page = page.replace('\n', ' ')
        secs = re.findall('<h2>.*?(?=<h2>)', page)
        secs.sort(key=lambda x: 1 if 'id="שארית_ציון"' in x else -1 if 'id="הערות_חיד&quot;א"' in x else 0)
        for sec in secs:
            if re.search('id="ה(?:גה|ער)ות_וו?יקיעור(?:ך|כים)"|תפריט ניווט', sec):
                continue
            if re.search(f'id="{title}\'?"', sec): #also seder tanaim veamoraim
                if letter == 'סתנוא':
                    current = f'{self.main.name}, {self.c_title}, Seder Tanaim VeAmoraim'
                else:
                    self.c_title, self.ch_title = f'Letter {eng_letter(letter)}', f'מערכת {letter}'
                    if 'id="קונטרס_אחרון"' in page:
                        node = Node(self.c_title, self.ch_title)
                        ja = Node(typ='ja')
                        node.node.append(ja.node)
                        ja = Node('Kuntres Acharon', 'קונטרס אחרון', 'ja')
                        node.node.append(ja.node)
                        if letter == 'ס':
                            ja = Node('Seder Tanaim VeAmoraim', 'סדר תנאים ואמוראים', 'ja')
                            node.node.append(ja.node)
                    else:
                        node = Node(self.c_title, self.ch_title, 'ja')
                    self.main.node.append(node.node)
                    current = f'{self.main.name}, {self.c_title}'
            elif 'id="קונטרס_אחרון"' in sec:
                current = f'{self.main.name}, {self.c_title}, Kuntres Acharon'
            elif 'id="הג&quot;ה_מנחם_ציון"' in sec:
                if letter == 'ס':
                    node = Node(self.c_title, self.ch_title)
                    ja = Node(typ='ja')
                    node.node.append(ja.node)
                    ja = Node('Likutei Menachem on Seder Tanaim VeAmoraim', 'לקוטי מנחם על סדר תנאים ואמוראים', 'ja')
                    node.node.append(ja.node)
                else:
                    node = Node(self.c_title, self.ch_title, 'ja')
                self.menachem.node.append(node.node)
                current = f'{self.menachem.name}, {self.c_title}'
            elif 'id="שארית_ציון"' in sec:
                current = self.sheerit.name
            elif 'id="פליטת_ספרים' in sec:
                node = Node(self.c_title, self.ch_title, 'ja')
                self.pletat.node.append(node.node)
                current = f'{self.pletat.name}, {self.c_title}'
            elif 'id="הערות_חיד&quot;א"' in sec:
                current = 'notes'
            elif 'id="לקוטי_מנחם">' in sec:
                current = f'{self.menachem.name}, {self.c_title}, Likutei Menachem on Seder Tanaim VeAmoraim'
            else:
                print(title, sec[:200])
            data = self.check_and_add_to_texts(current) if current != 'notes' else self.notes
            data_len = len(data)
            if data_len == 0 and type(data) == list:
                data.append([])

            #check numbering and append arrays
            for tag, line in re.findall('<(p|d[dt]|li)>(.*?)</(?:p|d[dt]|li)>', sec):
                old_num = len(data)
                temp = re.sub('<.*?>', '', line).strip()
                num_re = re.search('^(?:הערה )?(\(?)(?:ש\'צ )?(?:קו?"א )?([^ ]*?)([\)\*])', temp) if tag != 'li' else None
                num = num_re.group(2) if num_re else None
                if not num and not data_len:
                    if re.search("מתוך: +שם הגדולים", temp):
                        continue
                    if 'id="פליטת_ספרים' in sec:
                        self.intro = True
                        self.check_and_add_to_texts(f'{self.pletat.name}, Introduction')
                elif num and data != self.notes:
                    num = getGematria(num)
                    if num - 1 != old_num and num != old_num:
                        print(f'sequence problem {num} comes after {old_num}', line)
                    for _ in range(num-old_num):
                        data.append([])

                #parse line
                if num_re:
                    line = line.replace(num_re.group(0), f'{num_re.group(1)}{num_re.group(2)}{num_re.group(3)}', 1)
                for sup in re.findall('<sup.*?</sup>', line):
                    if re.findall('id="fn_\([^\) _]*\)', sup): #menachem zion
                        label = re.findall('id="fn_\(([^\) _]*)\)', sup)[0]
                        while label in self.notes_menachem:
                            label += '*'
                        order = getGematria(label)
                        if data != self.notes:
                            ref = f'{current} {len(data)}:{len  (data[-1])+1}'
                        else:
                            ref = 'Shem HaGedolim, Maarekhet Sefarim, Letter Samekh, Seder Tanaim VeAmoraim.46.1'
                        self.notes_menachem[label] = {'order': order, 'ref': ref}
                        line = line.replace(sup, f'<i data-commentator="{self.menachem.name}" data-label="{label}" data-order="{order}"></i>', 1)
                    elif re.findall('id="fn_\(ש&#39;צ_[^\) _]*\)', sup): #sheerit zion
                        label = re.findall('id="fn_\(ש&#39;צ_([^\) _]*)\)', sup)[0]
                        while label in self.notes_sheerit:
                            label += '*'
                        order = getGematria(label)
                        ref = f'{current} {len(data)}:{len(data[-1])+1}'
                        self.notes_sheerit[label] = {'order': order, 'ref': ref}
                        line = line.replace(sup, f'<i data-commentator="{self.sheerit.name}" data-label="{label}" data-order="{order}"></i>', 1)
                    elif re.findall('id="fn_[^\) _]*\*_', sup): #chida on stva
                        label = re.findall('id="fn_([^\) _]*)\*_', sup)[0].replace('*', '')
                        line = line.replace(sup, f'<sup>{label}</sup><i class="footnote">{self.notes[label]}</i>')
                    elif 'id="cite_ref-' in sup:
                        line = line.replace(sup, '')
                    else:
                        print('unrecognized ref', sup)

                if '<cite id' in line:
                    if re.findall('<cite id="fn_\([^\) _]*\)', line):
                        label = re.findall('<cite id="fn_\(([^\) _]*)\)', line)[0]
                        if label not in self.notes_menachem:
                            print(f'menachem note {label} not in the main')
                        elif len(data) != self.notes_menachem[label]['order']:
                                print(f'menachem note in location {len(data)} has order {self.notes_menachem[label]["order"]}')
                        else:
                            self.links.append({'refs': [self.notes_menachem[label]['ref'], f'{current} {len(data)}:{len(data[-1])+1}'],
                                               'inline_reference': {'data-commentator': self.menachem.name, 'data-order': self.notes_menachem[label]['order'], 'data-label': label},
                                               'type': 'commentary',
                                              'generated_by': 'shem hagedolim project'})
                            self.notes_menachem.pop(label)
                    elif re.findall('<cite id="fn_\(ש&#39;צ_[^\) _]*\)', line):
                        label = re.findall('<cite id="fn_\(ש&#39;צ_([^\) _]*)\)', line)[0]
                        if label not in self.notes_sheerit:
                            print(f'shherit note {label} not in the main')
                        elif len(data) != self.notes_sheerit[label]['order']:
                            print(f'shherit note in location {len(data)} has order {self.notes_sheerit[label]["order"]}')
                        else:
                            self.links.append({'refs': [self.notes_sheerit[label]['ref'],
                                                        f'{current} {len(data)}:{len(data[-1]) + 1}'],
                                               'inline_reference': {'data-commentator': self.sheerit.name,
                                                                    'data-order': self.notes_sheerit[label]['order'],
                                                                    'data-label': label},
                                               'type': 'commentary',
                                               'generated_by': 'shem hagedolim project'})
                            self.notes_sheerit.pop(label)
                    elif re.findall('<cite id="fn_[^\) _]*\*"', line):
                        label = re.findall('<cite id="fn_([^\) _]*)\*"', line)[0]
                        line = re.sub('<cite id="fn.*?</a>:', '' ,line)
                    else:
                        print('unrecognized note', line)

                line = re.sub('<span class="TooltipSpan"><small>&#160;.*?</small></span>', '', line)
                line = line.replace('<br />', '<br>')
                line = re.sub('</a>:|(?!</?b>|</?small>|<i data|</i>|</?sup>|<i class|<br>)<[^>]*?>', '', line)
                line = re.sub('<small></small>|</small><small>|<b></b>|</b><b>', '', line)
                line = line.replace('&#160;', ' ')
                line = ' '.join(line.split())
                if 'd' in tag and not line.startswith('<small>'):
                    line = f'<small>{line}'
                if 'd' in tag and not line.endswith('</small>'):
                    line += '</small>'
                line = re.sub(' (<i data.*?</i>(?: |$))', r'\1', line)

                if self.intro:
                    self.check_and_add_to_texts(f'{self.pletat.name}, Introduction').append(line)
                    self.intro = False
                elif data == self.notes:
                    self.notes[label] = line
                else:
                    data[-1].append(line)

        if self.notes_menachem:
            print('refernces to menachem w/o notes:', [self.notes_menachem.keys()])

    def post(self, just_links=False):
        server = 'http://localhost:9000'
        server = 'https://shem.cauldron.sefaria.org'
        if not just_links:
            shem = 'Shem HaGedolim'
            cats = ["Reference", shem]
            add_term(shem, 'שם הגדולים', server=server)
            add_category(shem, cats, server=server)
            for index in [self.main, self.menachem, self.pletat, self.sheerit   ]:
                index.node.validate()
                index_dict = {
                    "title": index.name,
                    "categories": cats,
                    "schema": index.node.serialize()}
                if index != self.main:
                    index_dict['base_text_titles'] = [self.main.name]
                    index_dict['dependence'] = 'Commentary'
                if index == self.sheerit:
                    index_dict['base_text_titles'].append(self.pletat.name)
                post_index(index_dict, server=server)
            for name, text in self.texts.items():
                if name == 'Shem HaGedolim, Maarekhet Sefarim, Letter Samekh, Seder Tanaim VeAmoraim':
                    text[0][0] = '<b>תנאים</b><br>' + text[0][0]
                    text[26][0] = '<b>אמוראים</b><br>' + text[26][0]
                version = {'text': text,
                    'versionTitle': 'Podgorze, 1905 (Wikisource edition)',
                    'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH000411346/NLI',
                    'language': 'he'}
                post_text(name, version, index_count='on', server=server)
        if self.notes_sheerit:
            print('refernces to shherit w/o notes:', [self.notes_sheerit.keys()])
        while 'error' in post_link(self.links, server=server, VERBOSE=False):
            time.sleep(360)

def save(req):
    if req.status_code != 200:
        print('problem with request', letter)
        return
    with open(f'{letter}.html', 'wb') as fp:
        fp.write(req.content)

if __name__ == '__main__':
    sg = Parser()
    for letter in gematria.keys():
        print(letter)
        #req = requests.request('get', f'https://he.wikisource.org/wiki/שם_הגדולים_(קרענגיל)/חלק_ב/{letter}')
        #save(req)
        sg.parse_page(letter, f'מערכת_{letter}')
        if letter == 'ס':
            print('סדר תנאים ואמוראים')
            #req = requests.request('get', f'https://he.wikisource.org/wiki/שם_הגדולים_(קרענגיל)/חלק_ב/סדר_תנאים')
            #save(req)
            #continue
            sg.parse_page('סתנוא', 'סדר_תנאים_ואמוראים')
    sg.post()
