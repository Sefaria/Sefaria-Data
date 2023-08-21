import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import gematria, encode_hebrew_numeral
from data_utilities.XML_to_JaggedArray import int_to_roman
from sources.functions import post_index, post_link, add_term
from sources.functions import post_text as pto

TAGS = {
    'chelek': '@00',
    'chapter': '@11',
    'seif': '@03'
}

def check_order(num_list, to_print, start=1):
    if num_list != list(range(start, len(num_list)+start)):
        print(to_print)


class OrAriPerek():

    def __init__(self, ari, or_pnimi, chelek, num):
        self.ari = ari
        self.or_pnimi = or_pnimi
        self.chelek = chelek
        self.num = num
        self.links = []

    def check_tags(self):
        base = re.findall('@55([א-ת])', self.ari)
        comm = re.findall('^([א-ת])\)', self.or_pnimi, re.M)
        if base != comm:
            print(f'''no matching between letters in ari and or pnimi in part {self.chelek.num} ch. {self.num}
            base: {base}
            commentary: {comm}''')
        if not 'אבגדהוזחטיכלמנסעפצקרשת'.startswith(''.join(base)):
            print(f'''problem with letter numbers in part {self.chelek.num} ch. {self.num}
            base: {base}
            commentary: {comm}''')

    def check_seifim(self, seifim):
        for i, seif in enumerate(seifim, 1):
            nums = re.findall('^\$\*? ?[א-ת]{1,3}\) ', seif, re.M)
            if len(nums) != 1:
                print(f'{len(nums)} seif tags in part {self.chelek.num} ch. {self.num} seif {i}')
            elif gematria(nums[0]) != i:
                print(f'seif {gematria(nums[0])} instaed of seif {i} in ari perek {self.num}')

    def parse_seif_ari(self, seif):
        letter_reg = '\$ ?[א-ת]{1,3}?\) '
        note_reg = f'^\*(?! ?{letter_reg}).*'
        notes = re.findall(note_reg, seif, re.M)
        if seif.count('*') != len(notes) * 2:
            print(f'problem with *s: {seif}')
        seif = re.sub(note_reg, '', seif, flags=re.M)
        for note in notes:
            note = re.sub('^\* ', '', note)
            seif = re.sub('^(\$)\* |\*', r'\1<sup class="footnote-marker">*</sup><i class="footnote">{}</i>'.format(note), seif, 1, re.M)
            seif = seif.replace(re.escape(note), '')
        seif = seif.split('\n') if self.chelek.num < 5 else [seif.strip()]
        expected_lines = 2 if self.chelek.num < 5 else 1
        if len([l for l in seif if l]) != expected_lines:
            print(f'not {expected_lines} lines as expected:', seif)
        if not re.search(f'^{letter_reg}', re.sub('^\$<sup.*?</i>', '$', seif[expected_lines-1])):
            print('no letter:', re.sub('^\$<sup.*?</i>', '$', seif[expected_lines-1]))
        remove_letter = lambda x: re.sub('^\$(<sup.*?</i>)?[א-ת]{1,3}?\) ', r'\1', x).strip()
        if self.chelek.num < 5:
            return {'title': seif[0].strip(), 'content': remove_letter(seif[1])}
        else:
            return {'title': '', 'content': remove_letter(seif[0])}


    def parse_ari(self):
        if self.chelek.num < 5:
            seifim = self.ari.split(TAGS['seif'])
        else:
            seifim = [f'${seif}' for seif in  re.split('^\$', self.ari, flags=re.M)]
        seifim = [seif for seif in seifim if seif.strip()]
        self.ari = {'title': seifim[0], 'seifim titles': '', 'seifim': []}
        if '@22' in self.ari['title']:
            self.ari['title'], self.ari['seifim titles'] = [x.strip() for x in self.ari['title'].split('@22')]
        seifim = seifim[1:]
        self.check_seifim(seifim)
        i = 1
        for s, seif in enumerate(seifim, 1):
            for letter in re.findall('@55([א-ת])', seif):
                link_label = letter
                if self.chelek.num == 2 and self.num == 1 and letter == 'ר':
                    link_label = 'ר וש'
                seif = re.sub('@55([א-ת]) ?', fr'<i data-commentator="Ohr Penimi" data-label="\1" data-order="{i}"></i>', seif, 1, flags=re.M)
                self.links.append({
                    'refs': [f'Talmud Eser HaSefirot, Section {int_to_roman(self.chelek.num)} {self.num}:{s}',
                             f'Ohr Penimi on Talmud Eser HaSefirot {self.chelek.num}:{self.num}:{i}'],
                    'type': 'commentary',
                    'auto': True,
                    'generated_by': 'TES parser',
                    'inline_reference': {
                        'data-commentator': 'Ohr Penimi',
                        'data-order': i,
                        'data-label': link_label
                    }
                })
                if not (self.chelek.num == 2 and self.num == 1 and letter == 'ר'):
                    i += 1
            self.ari['seifim'].append(self.parse_seif_ari(seif))

    def parse_or(self):
        seifim = re.sub('@33( ?)', r'\1<b>', self.or_pnimi, flags=re.M)
        seifim = re.sub('( ?)@44', r'</b>\1', seifim, flags=re.M)
        seifim = [line.strip() for line in re.split('(^[א-ת]{1,3}\))', seifim, flags=re.M)]
        self.or_pnimi = {'intro': seifim[0]}
        seifim.pop(0)
        self.or_pnimi['seifim'] = []
        for i in range(0, len(seifim), 2):
            if self.chelek.num < 5:
                self.or_pnimi['seifim'].append({'letter': seifim[i], 'content': seifim[i + 1].replace('\n', '<br>')})
            else:
                content = re.split('(?=<br><b>)', seifim[i + 1].replace('\n', '<br>'))
                self.or_pnimi['seifim'].append({'letter': seifim[i], 'content': content})

    def parse(self):
        self.check_tags
        self.parse_ari()
        self.parse_or()
        if self.chelek.num > 4:
            if len(self.ari['seifim']) < len(self.or_pnimi['seifim']):
                print(f"ari has {len(self.ari['seifim'])} seifim, while or pnimi {len(self.or_pnimi['seifim'])}")
            if len(self.ari['seifim']) < gematria(self.or_pnimi['seifim'][-1]['letter']):
                print(f"ari has {len(self.ari['seifim'])} seifim, while last in or pnimi is {self.or_pnimi['seifim'][-1]['letter']}")
            for i in range(len(self.or_pnimi['seifim']) - 1):
                if gematria(self.or_pnimi['seifim'][i]['letter']) >= gematria(self.or_pnimi['seifim'][i+1]['letter']):
                    print(f"seif {self.or_pnimi['seifim'][i+1]['letter']} comes after {self.or_pnimi['seifim'][i]['letter']} in or pnimi")


class AriOrChelek():

    def __init__(self, ari, or_pnimi, num):
        self.ari = ari
        self.or_pnimi = or_pnimi
        self.num = num
        self.links = []
        self.text_names = ['ari', 'or_pnimi']

    def handle_chelek_str(self, text_name):
        text = getattr(self, text_name)
        chelek_lines = re.findall(f'{TAGS["chelek"]}.*', text)
        if len(chelek_lines):
            print(f"there are {len(chelek_lines)} in chelek {self.num} of {text_name}")
        text = re.sub(f'{TAGS["chelek"]}.*\n?', '', text)
        setattr(self, text_name, text)

    def split_chapters(self, text_name):
        text = getattr(self, text_name)
        if text_name == 'ari':
            if self.num < 5:
                chapter_nums = re.findall(f'^{TAGS["chapter"]}פרק ([א-י]\'?(?:"[א-ט])?)$', text, re.M)
                if len(chapter_nums) != text.count(TAGS["chapter"]):
                    print(f'perek tags with weird continuation in chelek {self.num} of {text_name}')
                check_order([gematria(chap) for chap in chapter_nums],
                            f'problem with order of chapters {[gematria(chap) for chap in chapter_nums]} in chelek {self.num} of {text_name}')
                text = [x.strip() for x in re.split(f'^{TAGS["chapter"]}פרק [א-י]\'?(?:"[א-ט])?$', text, flags=re.M)]
            else:
                if not text.startswith('@01'):
                    print('problem with beginning of ari')
                text = text.split('\n', 1)
        else:
            temp = re.findall('^א\)(?:[\s\S](?!^א\)))*', text, flags=re.M)
            if self.num == 15:
                temp = [text.split('\n', 1)[1]]
            text = [''] if self.num != 1 else [re.split('^א\)', text, flags=re.M)[0]]
            while temp:
                text.append(temp.pop(0))
                while len(re.findall('^[א-ת]{1,3}\)', text[-1], flags=re.M)) < len(re.findall('@55[א-ת]', self.ari['chapters'][len(text)-2])):
                    try:
                        text[-1] += f'\n{temp.pop(0)}'
                    except IndexError:
                        print('missing letter(s) on ohr pnimi')
                        break
        setattr(self, text_name, {'title': text[0],'chapters': text[1:]})

    def parse(self):
        for text_name in self.text_names:
            self.handle_chelek_str(text_name)
            self.split_chapters(text_name)
        if len(self.ari['chapters']) != len(self.or_pnimi['chapters']):
            print(f"ari has {len(self.ari['chapters'])} chaptes while or pnimi {len(self.or_pnimi['chapters'])} in chelek {self.num}")
        for i, (ari, or_pnimi) in enumerate(zip(self.ari['chapters'], self.or_pnimi['chapters'])):
            perek = OrAriPerek(ari, or_pnimi, self, i+1)
            perek.parse()
            self.ari['chapters'][i], self.or_pnimi['chapters'][i] = perek.ari, perek.or_pnimi
            self.links += perek.links

class HistaklutChelek():

    def __init__(self, histaklut, num):
        self.content = histaklut
        self.num = num
        self.letter_reg ='^[א-ת]{1,3}\) '

    def check_seifim(self):
        seifim_nums = [gematria(s) for s in re.findall(self.letter_reg, self.content, flags=re.M)]
        check_order(seifim_nums, f'problem with order of seifim {seifim_nums} in chelek {self.num} of histaklut')
        self.letter_num = len(seifim_nums)

    def parse_seif(self, seif):
        if self.num > 4:
            return {'title': '', 'content': seif.strip().split('\n')}
        seif = [line for line in seif.split('\n', 1)]
        if not len(re.findall(f'^{self.letter_reg}', seif[-1], re.M)):
            print(f"seif in histaklut with {len(re.findall(f'^{self.letter_reg}', seif[-1], re.M))} letters: {seif[-1]}")
        return {'title': seif[0].strip(), 'content': re.sub(self.letter_reg, '', seif[1].strip()).split('\n')}

    def parse_chapter(self, chapter):
        if self.num < 5:
            seifim = re.split('((?:@03.*)?\n^[א-ת]{1,3}\) )', chapter, flags=re.M)
            if len(seifim)//2 == len(seifim)/2:
                print('8888?!')
            seifim = [seifim[0]] + [seifim[2*i+1] + seifim[2*i+2] for i in range(len(seifim)//2)]
            seifim = [s.replace('@03', '') for s in seifim]
        else:
            seifim = re.split(self.letter_reg, chapter, flags=re.M)
        chapter = {'intro': seifim[0].replace('$הסתכלות פנימית', '').strip(), 'seifim': []}
        seifim.pop(0)
        for seif in seifim:
            if seif:
                chapter['seifim'].append(self.parse_seif(seif))
        return chapter

    def parse(self):
        self.check_seifim()
        if self.num < 6:
            chapters = re.split(f'^{TAGS["chapter"]}.*', self.content, flags=re.M)
            chapters = [c.strip() for c in chapters]
        else:
            chapters = [''] + self.content.split('@75\n')
        self.content = {'intro': chapters[0].split('\n')[1:]}
        chapters = chapters[1:]
        self.content['chapters'] = [self.parse_chapter(c) for c in chapters]
        if self.letter_num != sum([len(c['seifim']) for c in self.content['chapters']]):
            print(555, f"{sum([len(c['seifim']) for c in self.content['chapters']])} seifim but {self.letter_num} nums")


class ShutChelek():

    def __init__(self, shut, num):
        self.content = shut
        self.num = num
        self.letter_reg ='^[א-ר]{1,3}\) '

    def split_shut(self):
        parts = [x.strip() for x in re.split('^\$', self.content, flags=re.M)]
        if len(parts) != 5:
            print(f'the number of shut parts in chelek {self.num} is not 4 but {len(parts)-1}')
        if parts[0]:
            print(f'there is something before first part of shut in chelek {self.num}')
        questions = [p.split('\n', 1)[1] for p in parts if re.search('^לוח ה?ש', p)]
        answers = [p.split('\n', 1)[1] for p in parts if re.search('^לוח ה?ת', p)]
        self.content = {
            'questions': {
                'words': questions[0],
                'issues': questions[1]
            },
            'answers': {
                'words': re.sub('^(@33.*?@44) *\n([א-ת]{1,3}\))', r'\2 \1', answers[0], flags=re.M),
                'issues': answers[1]
            }
        }
        if self.num == 6:
            self.content['questions']['siba'], self.content['answers']['siba'] = questions[2], answers[2]

    def check_letters(self):
        get_letters = lambda x: re.findall(self.letter_reg, x, re.M)
        get_nums = lambda x: [gematria(a) for a in get_letters(x)]
        keys = ['words', 'issues']
        if self.num == 6:
            keys.append('siba')
        for key in keys:
            if get_nums(self.content['questions'][key]) != get_nums(self.content['answers'][key]):
                print(f'different number of {key} questions and answers in chelek {self.num}')
                for i, (a, b) in enumerate(zip(get_nums(self.content['questions'][key]), get_nums(self.content['answers'][key]))):
                    if a != b:
                        print(i, a, b)
            letters = get_letters(self.content['questions']['words']) + get_letters(self.content['questions']['issues'])
            check_order([gematria(l) for l in letters if 'ק' not in l],
                        f'Problem with order of letters {[l for l in letters if "ק" not in l]} in chelek {self.num} of shut')
            letters = [re.sub('[ק\)]', '', l).strip() for l in letters if 'ק' in l]
            if not 'אבגדהוזחטיכלמנסעפצ'.startswith(''.join([re.sub('ק|\)', '', l).strip() for l in letters if 'ק' in l])):
                check_order([gematria(l) for l in letters], f'problem with order of letters {letters} in chelek {self.num} of shut', 0)

    def simple_parse(self, text, check_newlines):
        seifim = [seif.strip() for seif in re.split(self.letter_reg, text, flags=re.M)]
        if seifim[0]:
            print(f'something before letters in shut in chelek {self.num}: {seifim[0]}')
        seifim.pop(0)
        if check_newlines:
            bad_seifim = [seif for seif in seifim if '\n' in seifim]
            if bad_seifim:
                print(f'seif with newline in shut in part {self.num}: {bad_seifim}')
        return seifim

    def get_ref(self, text):
        text = text.split('ד"ה')[0]
        if any(word in text for word in ['או"פ', 'אור פנימי']):
            book = 'Ohr Penimi'
            text = re.sub('או"פ|אור פנימי', '', text)
        elif any(word in text for word in  ['הסת"פ']):
            book = 'Histaklut Penimit'
            text = re.sub('הסת"פ', '', text)
        else:
            book = 'Talmud Eser HaSefirot'
            print(f'make sure this ref is to ari: {text}')
        text = re.sub('חלק|פרק|אות', '', text)
        print(text.split())

    def get_refs(self, text):
        #in many cases there is nore than one ref. this make the situation muce more complicated b/c we have to take some of the ref from the first one
        pass

    def parse_words_answers(self):
        seifim = self.content['answers']['words']
        for i, seif in enumerate(seifim):
            parts = re.search('^@33([^:@]+)?:?@44 ?(?:\(([^\)]+)\):)?:?[ \n]?(.+)?$', seif, flags=re.M)
            if not parts:
                print(f'word answer in chelek {self.num} has a probelm with structure: {seif}')
            elif not parts.group(1):
                print(f'word answer in chelek {self.num} has no word: {seif}')
            elif not parts.group(3):
                print(f'word answer in chelek {self.num} has no answer: {seif}')
            else:
                seifim[i] = {
                    'word': parts.group(1),
                    'source': parts.group(2),
                    'answer': parts.group(3),
                }
                seifim[i] = {k: v.strip() if v else None for k, v in seifim[i].items()}
                seifim[i]['ref'] = self.get_refs(seifim[i]['source']) if seifim[i]['source'] else None

    def make_issues_sources_refs(self):
        seifim = self.content['answers']['issues']
        for i, seif in enumerate(seifim):
            ref = re.findall('\(([^\)]*)\)\.?$', seifim[i])
            seifim[i] = {
                'answer': seifim[i],
                'ref': self.get_refs(ref[0]) if ref else None
            }

    def parse(self):
        self.split_shut()
        self.check_letters()
        for qa in ['questions', 'answers']:
            keys = ['words', 'issues']
            if self.num == 6:
                keys.append('siba')
            for wi in keys:
                self.content[qa][wi] = self.simple_parse(self.content[qa][wi], (qa!='answers' or wi!='words'))
        self.parse_words_answers()
        self.make_issues_sources_refs()


class Chelek():

    def __init__(self, ari, or_pnimi, histaklut, shut, num):
        self.ari = ari
        self.or_pnimi = or_pnimi
        self.histaklut = histaklut
        self.shut = shut
        self.num = num
        self.links = []
        self.text_names = ['ari', 'or_pnimi', 'histaklut', 'shut']

    def parse_ari_or(self):
        arior = AriOrChelek(self.ari, self.or_pnimi, self.num)
        arior.parse()
        self.ari, self.or_pnimi = arior.ari, arior.or_pnimi
        self.links += arior.links

    def parse(self):
        self.parse_ari_or()
        histaklut = HistaklutChelek(self.histaklut, self.num)
        histaklut.parse()
        self.histaklut = histaklut.content
        shut = ShutChelek(self.shut, self.num)
        shut.parse()
        self.shut = shut.content


class Parser():

    def __init__(self, ari, or_pnimi, histaklut, shut):
        self.ari = ari
        self.or_pnimi = or_pnimi
        self.histaklut = histaklut
        self.shut = shut
        self.links = []
        self.text_names = ['ari', 'or_pnimi', 'histaklut', 'shut']

    def primary_handle(self, text_name):
        text = getattr(self, text_name)
        text = text.replace('\t', ' ')
        text = re.sub(' +', ' ', text)
        text = re.sub('^ | $', '', text, flags=re.M)
        text = re.sub(' *\n\$(\*)?[א-ת]{1,3}/ב\) *', r'<br><br>\1', text, flags=re.M)
        setattr(self, text_name, text)

    def split_parts(self, text_name):
        text = getattr(self, text_name)
        text = re.split('@00 ?חלק .*\n', text)[1:]
        setattr(self, text_name, text)

    def parse(self):
        for text_name in self.text_names:
            self.primary_handle(text_name)
            self.split_parts(text_name)
        if len({len(getattr(self, text_name)) for text_name in self.text_names}) != 1:
            print('different number of parts: ', '. '.join([f'{text_name} has {len(getattr(self, text_name))} parts' for text_name in self.text_names]))
        for i, _ in enumerate(self.ari):
            print(f'chelek {i+1}')
            chelek = Chelek(self.ari[i], self.or_pnimi[i], self.histaklut[i], self.shut[i], i+1)
            chelek.parse()
            self.ari[i], self.or_pnimi[i], self.histaklut[i], self.shut[i] = chelek.ari, chelek.or_pnimi, chelek.histaklut, chelek.shut
            self.links += chelek.links


def post(parser):
    name = 'Talmud Eser HaSefirot'
    hname = 'תלמוד עשר הספירות'
    main = SchemaNode()
    main.add_primary_titles(name, hname)
    ohr_base = 'Ohr Penimi'
    ohr_base_heb = 'אור פנימי'
    ohr_name = f'{ohr_base} on {name}'
    ohr = SchemaNode()
    ohr.add_primary_titles(ohr_name, f'{ohr_base_heb} על {hname}')
    main_text = {}
    ohr_text = {'d': []}

    #intros
    intro = JaggedArrayNode()
    intro.add_primary_titles('Introduction', 'הקדמה')
    intro.depth = 2
    intro.addressTypes = ['Integer', 'Integer']
    intro.sectionNames = ['Seif', 'Paragraph']
    main.append(intro)
    main_text['Introduction'] = ['א']
    intro.depth = 1
    intro.addressTypes = ['Integer']
    intro.sectionNames = ['Paragraph']
    ohr.append(intro)
    ohr_text['Introduction'] = [parser.or_pnimi[0]['title'].replace('$אור פנימי\n', '')]

    #or pnimi node
    ohr_def = JaggedArrayNode()
    ohr_def.default = True
    ohr_def.key = 'default'
    ohr_def.depth = 3
    ohr_def.addressTypes = ['Integer', 'Integer', 'Integer']
    ohr_def.sectionNames = ['Section', 'Chapter', 'Seif']
    ohr.append(ohr_def)
    ohr.validate()

    for i in range(16):
        he_title = parser.ari[i]['title']
        he_title = re.split(',? כולל', he_title)[0].replace('@01', '')
        chelek_title = f'Section {int_to_roman(i+1)}'
        chelek = SchemaNode()
        main.append(chelek)
        chelek.add_primary_titles(chelek_title, f'חלק {encode_hebrew_numeral(i+1)}: {he_title}')

        #ari node
        ari = JaggedArrayNode()
        ari.default = True
        ari.key = 'default'
        if i < 4:
            ari.depth = 2
            ari.addressTypes = ['Integer', 'Integer']
            ari.sectionNames = ['Chapter', 'Seif']
        else:
            ari.depth = 1
            ari.addressTypes = ['Integer']
            ari.sectionNames = ['Chapter']
        chelek.append(ari)

        #ari text
        if i < 4:
            main_text[chelek_title] = []
            for chapter in parser.ari[i]['chapters']:
                ctitle =  chapter['title'] if chapter['title'] != '$' else ''
                st = chapter['seifim titles']
                seifim = []
                for seif in chapter['seifim']:
                    seif_text = f'<small>{seif["title"].strip()}</small><br>' if seif["title"].strip() else ''
                    seif_text += seif['content']
                    seifim.append(seif_text)
                if ctitle:
                    if i == 2:
                        seifim[0] = f"<b><big>{ctitle}</big></b><br><small>{st}</small><br><br>{seifim[0]}"
                    else:
                        seifim[0] = f"<b><big>{ctitle}</big></b><br><br>{seifim[0]}"
                main_text[chelek_title].append(seifim)
        else:
            main_text[chelek_title] = [seif['content'] for seif in parser.ari[i]['chapters'][0]['seifim']]

        #or pnimi
        if i < 4:
            or_chelek = [[seif['content'] for seif in chapter['seifim']] for chapter in parser.or_pnimi[i]['chapters']]
        else:
            or_chelek = []
            for seif in parser.or_pnimi[i]['chapters'][0]['seifim']:
                or_chelek += [[] for _ in range(gematria(seif['letter']) - len(or_chelek))]
                or_chelek[-1] = seif['content']
        ohr_text['d'].append(or_chelek)

        #histaklut
        def parse_chapter(chapter):
            def parse_seif(seif):
                title = f'<small>{seif["title"]}</small><br>' if seif["title"] else ''
                return f'{title}{"<br>".join(seif["content"])}'
            text = [parse_seif(seif) for seif in chapter['seifim']]
            if chapter['intro']:
                text[0] = f"{chapter['intro']}<br><br>{text[0]}"
            return text
        his = JaggedArrayNode()
        his.add_primary_titles('Histaklut Penimit', 'הסתכלות פנימית')
        if parser.histaklut[i]['chapters'] and parser.histaklut[i]['chapters'][0]['seifim']:
            if i < 7:
                his.depth = 2
                his.addressTypes = ['Integer', 'Integer']
                his.sectionNames = ['Chapter', 'Paragraph']
                if i == 3:
                    intro = f"{parser.histaklut[i]['intro'][0]}<br><br>" + '<br>'.join(parser.histaklut[i]['intro'][1:]).replace('א) ', '')
                elif parser.histaklut[i]['intro']:
                    intro = '<br>'.join(parser.histaklut[i]['intro']) + '<br><br><b>פרק א</b><br>'
                else:
                    intro = ''
                his_text = [parse_chapter(chap) for chap in parser.histaklut[i]['chapters']]
                if i == 3:
                    his_text[0][0] = '<b>פרק א</b><br>' + his_text[0][0]
                    his_text[0] = [intro] + his_text[0]
                else:
                    his_text[0][0] = intro + his_text[0][0]
            else:
                his.depth = 1
                his.addressTypes = ['Integer']
                his.sectionNames = ['Paragraph']
                his_text = parse_chapter(parser.histaklut[i]['chapters'][0])
            chelek.append(his)
            main_text[f'{chelek_title}, Histaklut Penimit'] = his_text
            if i in [0, 1, 3]:
                his.index_offsets_by_depth = {2: [sum([len(his_text[c]) for c in range(x)]) for x in range(len(his_text))]}

        #shut
        keys = [('Terminology', 'פירוש המלות', 'words'), ('Topics', 'עניינים', 'issues')]
        if i == 5:
            keys.append(("Cause and Effect", 'סדר סיבה ומסובב', 'siba'))
        def add_link(text, qora, title, i):
            if type(text) == str and text.startswith('הערה'):
                return text
            address = f'{name}, {chelek_title}, {title} {i+1}'
            if qora != 'Answers':
                adding = lambda x: f'<small>(<a data-ref="{address}" href="/{address.replace(" ", "_")}">לשאלה</a>)</small> {x}'
            else:
                adding = lambda x: f'{x} <small>(<a data-ref="{address}" href="/{address.replace(" ", "_")}">לתשובה</a>)</small>'
            if type(text) == str:
                return adding(text)
            else:
                text[-1] = adding(text[-1])
                return text
        length = 0
        for key in keys:
            q_title = f'List of Questions on {key[0]}'
            a_title = f'List of Answers on {key[0]}'
            questions = JaggedArrayNode()
            questions.add_primary_titles(q_title, f'לוח השאלות ל{key[1]}')
            questions.depth = 1
            questions.sectionNames = ['Paragraph']
            questions.addressTypes = ['Integer']
            if length:
                questions.index_offsets_by_depth = {1: length}
            chelek.append(questions)
            main_text[f'{chelek_title}, {q_title}'] = \
                [f'{add_link(x, "Answers", a_title, ind+length)}' for ind, x in enumerate(parser.shut[i]['questions'][key[2]])]
            length += len(parser.shut[i]['answers'][key[2]])
        length = 0
        for key in keys:
            q_title = f'List of Questions on {key[0]}'
            a_title = f'List of Answers on {key[0]}'
            answers = JaggedArrayNode()
            answers.add_primary_titles(a_title, f'לוח התשובות ל{key[1]}')
            answers.depth = 2
            answers.sectionNames = ['Siman', 'Paragraph']
            answers.addressTypes = ['Integer', 'Integer']
            if length:
                answers.index_offsets_by_depth = {1: length}
            chelek.append(answers)
            if key[0] == 'Terminology':
                source = lambda x: f' ({x["source"]})' if x["source"] else ''
                parse_answer = lambda x: [f"<b>{x['word']}</b>{source(x)}<br>{x['answer']}"]
            elif key[0] == 'Topics':
                parse_answer = lambda x: x['answer'].split('\n')
            else:
                parse_answer = lambda x: x.split('\n')
            main_text[f'{chelek_title}, {a_title}'] = \
                    [add_link(parse_answer(x), 'Questions', q_title, ind+length) for ind, x in enumerate(parser.shut[i]['answers'][key[2]])]
            length += len(parser.shut[i]['answers'][key[2]])

    #post
    def clean_text(text):
        if isinstance(text, list):
            for i in range(len(text)):
                text[i] = clean_text(text[i])
        elif isinstance(text, dict):
            for key in text:
                text[key] = clean_text(text[key])
        else:
            text = re.sub('&03(.*?)<br>', r'<br><small>\1</small><br>', text)
            if text.count('@33') != text.count('@44'):
                print('problem with bold tags', text)
            else:
                text = re.sub('@33( ?)', r'\1<b>', text)
                text = re.sub('( ?)@44', r'</b> ', text)
            text = re.sub('@\d\d|\$|&', '', text)
            text = re.sub(' ([:\.,])', r'\1', text)
        return text
    def post_text(address, text_dict, server):
        text_dict['text'] = clean_text(text_dict['text'])
        pto(address, text_dict, server=server)
    server = 'http://localhost:9000'
    server = 'https://new-shmuel.cauldron.sefaria.org'
    cats = ['Kabbalah', 'Baal HaSulam']
    index_dict = {
        'title': name,
        'categories': cats,
        'schema': main.serialize(),
    }
    post_index(index_dict, server=server)
    add_term(ohr_base, ohr_base_heb, server=server)
    index_dict = {
        'title': ohr_name,
        'categories': cats,
        'schema': ohr.serialize(),
        'dependence': 'Commentary',
        'base_text_titles': [name],
        'collective_title': ohr_base
    }
    post_index(index_dict, server=server)
    text_dict = {
        'title': name,
        'versionTitle': '?',
        'versionSource': '?',
        'language': 'he'
    }
    for t in main_text:
        text_dict['text'] = main_text[t]
        post_text(f'{name}, {t}', text_dict, server=server)
    text_dict['name'] = ohr_name
    text_dict['text'] = ohr_text['Introduction']
    post_text(f'{ohr_name}, Introduction', text_dict, server=server)
    text_dict['text'] = ohr_text['d']
    post_text(ohr_name, text_dict, server=server)

    #links
    for ref in Ref(ohr_name).all_segment_refs():
        if ref.sections[0] < 5:
            continue
        tref = ref.normal()
        bref = f'{name}, Section {int_to_roman(ref.sections[0])} {ref.sections[1]}'
        parser.links.append({
            'refs': [bref, tref],
            'type': 'commentary',
            'auto': True,
            'generated_by': 'TES parser',
        })
    post_link(parser.links, server=server, skip_lang_check=False, VERBOSE=False)


def parse_all():
    parser_args = {}
    titles = {
        'Talmud Eser HaSefirot': 'תלמוד עשר הספירות',
        'Ohr Penimi': 'אור פנימי',
        'Histaklut Penimit': 'הסתכלות פנימית',
        'Questions & Answers': 'שאלות ותשובות'
    }
    attr_names = {
        'Talmud Eser HaSefirot': 'ari',
        'Ohr Penimi': 'or_pnimi',
        'Histaklut Penimit': 'histaklut',
        'Questions & Answers': 'shut'
    }
    with open(f'data/תלמוד עשר הספירות.txt') as fp:
        parser_args['ari'] = fp.read()
    with open(f'data/השאר.txt') as fp:
        data = fp.read()
    part_reg = '@00[^\n]*'
    parser_args['or_pnimi'] = '\n'.join(re.findall(f'{part_reg}|\$אור[^\$]*', data, flags=re.M))
    parser_args['histaklut'] = '\n'.join(re.findall(f'{part_reg}|\$הסתכלות[^\$]*', data, flags=re.M)) + '\n'
    parser_args['shut'] = '\n'.join(re.findall(f'{part_reg}|\$לוח(?:[\s\S](?!@00))*', data, flags=re.M))
    parser = Parser(**parser_args)
    parser.parse()
    post(parser)

if __name__ == '__main__':
    parse_all()


'''
ari
    chelek
        title
        chapter
            title
            seif
                title
                content
or pnimi
    chelek
        title ?? seems redundant
        chapter
            intro (optinal)
            seif
                segment
            
histaklut
    chelek
        intro
            segment
        chapter
            intro (optional)
            seif - numbering goes across chapters for all the chelek
                title
                content
                    segment
    
shut
    questions
        words
            letter
        issues
            letter - the numbering continues from words
    answers
        words
            letter
                word
                source
                answer
                (ref)
        issues
            letter - the numbering continues from words (answer and then source in parens, usually, not in the format of words answers)
                (answer,
                ref)
        
'''