import re
import os
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import gematria
from sources.functions import post_link, post_text, add_term, post_index, add_category
import copy


class Masechet:

    def __init__(self, lines, masechet):
        self.lines = lines
        self.masechet = Ref(masechet).normal()
        self.is_talmud = Ref(masechet).is_bavli()
        self.text = []

        self.curr_loc = 0 if self.is_talmud else [0, 0]
        self.is_amud_aleph = None
        self.curr_line = ''

    def handle_loc(self):
        if self.is_talmud:
            daf_reg = 'ק?[א-ק][א-ט]?'
            daf_s = 'דף'
            daf = re.findall(f'^% *(?:{daf_s} )?({daf_reg}) *$|^%% ({daf_reg})', self.curr_line)
            amud = re.findall('^%%%? ?(?:ע[״"])?([אב]) *$', self.curr_line)
            if amud:
                if amud[0] == 'ב':
                    if self.is_amud_aleph:
                        self.curr_loc += 1
                        self.is_amud_aleph = False
                    else:
                        print(f'amud b when it is already b. current page is {self.curr_loc}')
                else:
                    if self.is_amud_aleph == 'a':
                        print(f'amud a when it is already a. current page is {self.curr_loc}')
                    self.is_amud_aleph = 'a'
            elif daf:
                daf = [x for x in daf[0] if x][0]
                page = gematria(daf) * 2 - 1
                if page <= self.curr_loc:
                    print(f'page is going from {self.curr_loc} to {page}', self.curr_line)
                self.curr_loc = page
                self.is_amud_aleph = 'daf'
            else:
                print(f'cant understand {self.curr_line}')
            if len(self.text) < self.curr_loc:
                self.text += [[] for _ in range(self.curr_loc - len(self.text))]
        else:
            perek = re.findall(r'\bפ([ט-ל]?[״"][א-ל])', self.curr_line)
            mishna = re.findall(r'\bמ([ט-ל]?[״"][א-ל])', self.curr_line)
            if perek:
                self.curr_loc[0] = gematria(perek[0])
                if len(self.text) < self.curr_loc[0]:
                    self.text += [[] for _ in range(self.curr_loc[0] - len(self.text))]
            if mishna:
                self.curr_loc[1] = gematria(mishna[0])
                if len(self.text[self.curr_loc[0]-1]) < self.curr_loc[1]:
                    self.text[self.curr_loc[0]-1] += [[] for _ in range(self.curr_loc[1] - len(self.text[self.curr_loc[0]-1]))]
            elif not perek:
                print('no lcation', self.curr_line)

    def parse_line(self):
        line = self.curr_line
        line = re.sub('־( ?נ"ב)', r'.\1', line)
        line = re.sub('־|;|\?', '', line)
        line = re.sub(' (\.|:)', r'\1', line)
        if line.count('*') == 1:
            if line.startswith('*'):
                line = line.replace('*', '')
            else:
                line = '*' + line
        if line.count('*') > 3:
            line = line.replace('*', '$', 2)
            line = line.replace('*', '')
            line = line.replace('$', '*')
        line = re.sub('\*(.*)\*', r'<b>\1</b>', line)
        line = line.replace('*', '')
        if self.is_talmud:
            self.text[self.curr_loc - 1].append(line)
        else:
            self.text[self.curr_loc[0] - 1][self.curr_loc[1] - 1].append(line)

    def rebreak_lines(self, text=None):
        if text==None:
            text = self.text
        for i in range(len(text)):
            try:
                element = text[i]
            except IndexError:
                break
            if isinstance(element, list):
                self.rebreak_lines(text=text[i])
            else:
                if element.endswith('.'):
                    text[i] = text[i][:-1] + ':'
                elif element.endswith('כצ"ל'):
                    text[i] = text[i] + ':'
                elif not element.endswith(':') and i != len(text)-1:
                    text[i] = text[i] + ' ' + text[i+1]
                    text.pop(i+1)
        return text

    def parse(self):
        for line in self.lines[1:]:
            line = ' '.join(line.split())
            self.curr_line = line
            if not line:
                continue
            if line.startswith('%'):
                self.handle_loc()
            else:
                self.parse_line()
        self.rebreak_lines(self.text)


    def post(self, first):
        server = 'http://localhost:9000'
        # server = 'https://new-shmuel.cauldron.sefaria.org'
        collective = "Haggahot Ya'avetz"
        he_coll = 'הגהות מהריעב״ץ'
        title = f'{collective} on {self.masechet}'
        he_title = f'{he_coll} על {Ref(self.masechet).he_normal()}'
        seder = Ref(self.masechet).index.categories[-1]
        if self.is_talmud:
            cats_path = ['Talmud', 'Bavli', 'Acharonim on Talmud', collective]
        else:
            cats_path = ['Mishnah', 'Acharonim on Mishnah', collective]
        if first:
            add_term(collective, he_coll, server=server)
            add_category(collective, cats_path, server=server)
        cats_path.append(seder)
        add_category(seder, cats_path, server=server)
        schema = JaggedArrayNode()
        schema.add_primary_titles(title, he_title)
        if self.is_talmud:
            schema.depth = 2
            schema.addressTypes = ['Talmud', 'Integer']
            schema.sectionNames = ['Daf', 'Comment']
        else:
            schema.depth = 3
            schema.addressTypes = ['Perek', 'Mishnah', 'Integer']
            schema.sectionNames = ['Chapter', 'Mishnah', 'Comment']
        index_dict = {
            'title': title,
            'categories': cats_path,
            'schema': schema.serialize(),
            'dependence': 'Commentary',
            'base_text_titles': [self.masechet],
            'collective_title': collective
        }
        post_index(index_dict, server=server)
        text_dict = {
            'title': title,
            'versionTitle': 'Vilna Edition',
            'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH001300957/NLI',
            'text': self.text,
            'language': 'he'
        }
        post_text(title, text_dict, server=server)


for i, file in enumerate(os.listdir('data')):
    print(f'***', file)
    with open(f'data/{file}') as fp:
        text = fp.read()
    text = re.sub(': *\*', ':\n*', text)
    text = re.split('^%.*(?:רא["י״׳]ש|רמב"ם|פסקי|המשניות)', text, flags=re.M)[0].split('\n')
    masechet = Masechet(text, file)
    masechet.parse()
    masechet.post(i==0)
