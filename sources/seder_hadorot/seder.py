import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import *
import re
from sources.functions import post_text, post_index, getGematria, post_link
from sefaria.system.exceptions import DuplicateRecordError

def getYear(year_str):
    if type(year_str) == int:
        return year_str
    parts = year_str.split()
    year = getGematria(parts[-1])
    if len(parts) == 2:
        elef = 1 if parts[0] == 'אלף' else getGematria(parts[0]) - 1
        year += 1000 * elef
    return year

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
            self.node.addressTypes = ['Integer', 'Integer'][-depth:]
            self.node.sectionNames = ['Integer', 'Integer'][-depth:]
            self.node.depth = depth
        self.node.validate()

class DicNoode():

    def __init__(self, first, last, hwm, name=''):
        self.name = name
        self.node = DictionaryNode({'lexiconName': 'Seder HaDorot'})
        self.node.firstWord = first
        self.node.lastWord = last
        self.node.headwordMap = hwm
        if name:
            pass
        else:
            self.node.key = 'default'
            self.node.default = True
        self.node.validate()

class Parser():

    def __init__(self):
        seder = 'Seder HaDorot'
        self.alts = []
        self.index = Node(seder, 'סדר הדורות')
        self.intro = Node('Introduction', 'הקדמה', typ='ja', depth=1)
        self.almanac = Node('Almanac', 'סדר ימות עולם')
        #default = DicNoode('1', '6000', [['האלף הראשון', f'{seder}, Almanach 1-1000'], ['האלף השני', f'{seder}, Almanach 1001-2000'], ['האלף השלישי', f'{seder}, Almanach 2001-3000'], ['האלף הרביעי', f'{seder}, Almanach 3001-4000'], ['האלף החמישי', f'{seder}, Almanach 4001-5000'], ['האלף השישי', f'{seder}, Almanach 5001-6000']])
        default = Node(typ='ja')
        index = Node('Index', 'מפתח', typ='ja')
        self.almanac.node.append(default.node)
        self.almanac.node.append(index.node)
        self.almanac.node.validate()
        self.tanaim = Node('Tanaim and Amoraim', 'סדר תנאים ואמוראים', typ='ja')
        self.books = Node('Authors and Compositions', 'סדר מחברים וספרים', typ='ja')
        self.hagahot = Node('Haggahot', 'הגהות', typ='ja')
        for node in [self.intro, self.almanac, self.tanaim, self.books, self.hagahot]:
            self.index.node.append(node.node)
        self.texts = {}
        self.links = []
        self.topic_links = []
        self.names = {}
        with open('seder.txt', encoding='utf-8') as fp:
            self.data = fp.read()
        self.eng_letters = ['Alef', 'Bet', 'Gimel', 'Dalet', 'He', 'Vav', 'Zayin', 'Chet', 'Tet', 'Yod', 'Kaf', 'Lamed',
                            'Mem', 'Nun', 'Samekh', 'Ayin', 'Peh', 'Tzadi', 'Kof', 'Resh', 'Shin', 'Tav']

    def altnode(self, name, hname, wholeref, include=True):
        node = ArrayMapNode()
        node.depth = 0
        node.wholeRef = f'{self.index.name}, {wholeref}'
        if include:
            node.includeSections = True
        node.add_title(name, 'en', True)
        node.add_title(hname, 'he', True)
        return node

    def find_year_in_text(self, text, term=''):
        one = "[א-ת]\'"
        two90 = '[י-צ]"[א-ט]|ט"ו|ט"ז'
        two300 = '[ק-ש]"[א-צ]'
        two400 = 'ת"[א-ת]'
        two = f'{two90}|{two300}|{two400}'
        three = '[ק-ש]{}|ת{}'.format(f'(?:{two90})', f'(?:{two})')
        four = f'ת(?:{three})'
        five = f'ת{four}'
        gim_patterm = f'{five}|{four}|{three}|{two}|{one}'
        years = re.findall(f'(?:[ב-ה]"א|אלף) (?:{gim_patterm})', text)
        if years:
            more = re.findall(f' {gim_patterm}(?: |$)', text.split(years[-1])[-1])
        else:
            more = re.findall(f' {gim_patterm}(?: |$)', text)
        for year in more:
            year = getYear(year)
            if years:
                year += getYear(years[-1]) // 1000 * 1000
            try:
                year_text = ' '.join(self.texts[self.almanac.name][year-1])
            except IndexError:
                continue
            year_text = re.sub('<.*?>', '', year_text)
            if term in year_text:
                years.append(year)
        return years

    def link_topic(self, name, ref):
        topic_set = TopicSet({"titles.text": name})
        if topic_set.count() == 1:
            slug = topic_set.array()[0].slug
            self.topic_links.append(RefTopicLink({'toTopic': slug,
            'ref': ref,
            'linkType': "about",
            'dataSource': "sefaria"}))
        elif topic_set.count() > 1:
            #print('more than one topic for', name)
            pass

    def housekeep(self, data):
        if data == []:
            return []
        if type(data[0]) == str:
            data = [re.sub('[^ \na-zא-ת.,:"\'\/<>\)\(\]\[\-⬤\}\{]', '', line) for line in data]
            data = [re.sub(' *\{([^\}]*)\}', r'<sup>*</sup><i class="footnote">\1</i>', line) for line in data]
            return [' '.join(line.split()) for line in data]
        return [self.housekeep(e) for e in data]

    def parse_lines(self, data, intro=False):
        data = data.replace('@44@33', '@33@44').replace('@11@55', '@55@11')
        data = re.sub('@([^ \)]*\)) *\n', r'\1 ', data)
        data = [' '.join(line.split()) for line in data.split('\n') if line]
        data = [l for l in data if l]
        for l, line in enumerate(data):
            if not intro:
                if line.count('@44') != line.count('@55'):
                    print(f'unbalanced 44s and 55s in line {l}, starts with {line[:150]}')
                line = line.replace('@44', '<small>').replace('@55', '</small>')
            if line.count('@11') != line.count('@33'):
                print(f'unbalanced 11s and 33s in line {l}, starts with {line[:150]}')
            line = re.sub('@66|@11', '<b>', re.sub('@77|@33', '</b>', line))
            line = re.sub('#(.)', r'<b>\1</b>', line)
            line = line.replace('%', '⬤')
            #TODO handle {}
            data[l] = line
        return data

    def parse_intro(self):
        data = self.data.split('@00הקדמת הגאון המחבר ז"ל')[1].split('@00סדר ימות עולם')[0]
        self.texts[self.intro.name] = self.parse_lines(data, True)
        self.alts.append(self.altnode('Introduction', 'הקדמה', f'Introduction 1-{len(self.texts[self.intro.name])}', False))

    def parse_almanac(self):
        data = self.data.split('@00סדר ימות עולם')[1].split('@00מפתח לסדר הדורות חלק ראשון')[0]
        data = re.sub('@00אלף.*\n', '', data)
        data = re.sub('(@00.*\n)(@22.*\n)', r'\2\1', data)
        secs = re.findall('@22([^\n]*)([\s\S]*?)(?=@22|$)', data)
        years = [getYear(e[0]) for e in secs]
        for x, y in zip(years, years[1:]):
            if x >= y:
                print(x, y)
        data = [e[1] for e in secs]
        new = [[] for _ in range(5500)]
        alt_starts, alt_ends = [], []
        for sec, year in zip(data, years):
            year_pars = self.parse_lines(sec)
            for p, par in enumerate(year_pars):
                if '@00' in par:
                    year_pars[p] = f'<b>{par.replace("@00", "")}</b>'
                    alt_starts.append(f'{year}:{p + 1}')
                    alt_ends.append(f'{year if p!=0 else year-1}:{p if p!=0 else len(new[year-2]) if len(new[year-2]) != 0 else 1}')
            new[year-1] = year_pars
        self.texts[self.almanac.name] = new

        #alts
        self.alts.append(self.altnode('Almanac', 'סדר ימות עולם', 'Almanac 1-5600'))
        ordinals = [('First', 'ראשון'), ('Second', 'שני'), ('Third', 'שלישי'), ('Fourth', 'רביעי'), ('Fifth', 'חמישי'), ('Sixth', 'שישי')]
        alt_ends = alt_ends[1:] + ['4727:1']
        etitles = ['First Generation of Tannaim', 'Second Generation of Tannaim', 'Third Generation of Tannaim', 'First Generation of Amoraim', 'Second Generation of Amoraim', 'Third Generation of Amoraim', 'Fourth Generation of Amoraim', 'Fifth Generation of Amoraim', 'Sixth Generation of Amoraim', 'Seventh Generation of Amoraim', 'Chronology of Savoraim', 'The Geonic Chronology of Sherira Gaon']
        htitles = ['דור ראשון של תנאים', 'דור שני של תנאים', 'דור שלישי של תנאים', 'דור ראשון של אמוראים', 'דור שני של אמוראים', 'דור שלישי של אמוראים', 'דור רביעי של אמוראים', 'דור חמישי של אמוראים', 'דור שישי של אמוראים', 'דור שביעי של אמוראים', 'סדר רבנן סבוראי', 'סדר הגאונים לרב שרירא גאון']
        for i in range(6):
            start = i * 1000 + 1 if i != 4 else 4740
            end = (i + 1) * 1000 if i != 3 else 3829
            node = self.altnode(f'{ordinals[i][0]} Thousand', f'האלף ה{ordinals[i][1]}', f'{self.almanac.name} {start}-{end}')
            self.alts[1].append(node)
            if i == 3:
                for _ in range(12):
                    self.alts[1].append(self.altnode(etitles.pop(0), htitles.pop(0), f'{self.almanac.name} {alt_starts.pop(0)}-{alt_ends.pop(0)}'))

    def parse_index(self):
        data = self.data.split('@00מפתח לסדר הדורות חלק ראשון')[1].split('@00סדר תנאים ואמוראים ')[0]
        new = re.sub('@00.*', '', data)
        self.texts[f'{self.almanac.name}, Index'] = [[p] for p in self.parse_lines(new)]
        alt = self.altnode('Index', 'מפתח', f'{self.almanac.name}, Index 1-{len(self.texts[f"{self.almanac.name}, Index"])}', False)
        data = re.findall('@00(.*)\n([\s\S]*?)(?=@00|$)', data)
        letters = [d[0] for d in data]
        data = [d[1] for d in data]
        start = 2
        sec = 2
        for i, (letter, chunk) in enumerate(zip(letters, data)):
            lines = [l.strip() for l in chunk.split('\n') if l.strip()]
            end = start + len(lines) - 1
            letter_alt = self.altnode(self.eng_letters[i], letter.replace("'", ''), f'{self.almanac.name}, Index {start}-{end}', False)
            for l, line in enumerate(lines):
                name = re.findall('@11(.*)@33', line)[0].strip()
                for year in self.find_year_in_text(line, name):
                    self.names[name] = f'{self.index.name}, {self.almanac.name}, Index, {sec+l}:1'
                    self.link_topic(name, self.names[name])
                    self.links.append({'refs': [self.names[name],
                                                f'{self.index.name}, {self.almanac.name}, {(getYear(year))}'],
                                       'type': 'Quotation',
                                       'generated_by': 'seder hadorot parser'})
                letter_alt.append(self.altnode(str(l+1), name, f'{self.almanac.name}, Index {start+l}', False))
            start = end + 1
            alt.append(letter_alt)
            sec += len(lines)
        self.alts[1].append(alt)

    def parse_tanaim_amoraim(self):
        data = self.data.split('@00סדר תנאים ואמוראים')[1].split('@00סדר מחברים וסדר ספרים ')[0]
        new = re.sub('@00.*', '', data)
        self.texts[f'{self.tanaim.name}'] = []
        for tana in re.findall('(@11[\s\S]*?)(?=@11|$)', new):
            self.texts[f'{self.tanaim.name}'].append(self.parse_lines(tana))
        self.alts.append( self.altnode(self.tanaim.name, 'סדר תנאים ואמוראים', f'{self.tanaim.name} 1-{len(self.texts[f"{self.tanaim.name}"])}', False))
        data = re.findall('@00(.*)\n([\s\S]*?)(?=@00|$)', data)
        letters = [d[0] for d in data]
        data = [d[1] for d in data]
        start = 1
        for i, (letter, chunk) in enumerate(zip(letters, data)):
            entries = re.findall('(@11[\s\S]*?)(?=@11|$)', chunk)
            end = start + len(entries) - 1
            letter_alt = self.altnode(self.eng_letters[i], letter.replace("'", '')[:5], f'{self.tanaim.name} {start}-{end}', False)
            for l, entry in enumerate(entries):
                name = re.findall('@11\*?(.*)@33', entry)[0]
                name = re.sub('[^א-ת "\']', '', name).strip()
                letter_alt.append(self.altnode(str(l+1), name, f'{self.tanaim.name} {start+l}', False))
                self.link_topic(name, f'{self.index.name}, {self.tanaim.name} {start+l}:1')
                if name in self.names:
                    self.links.append({'refs': [f'{self.names[name]}', f'{self.index.name}, {self.tanaim.name} {start+l}:1'],
                                       'type': 'Reference',
                                       'generated_by': 'seder hadorot parser'})
            start = end + 1
            self.alts[2].append(letter_alt)

    def parse_books(self):
        data = self.data.split('@00סדר מחברים וסדר ספרים')[1].split('@00הגהות ותקונים בש"ס, בשמות החכמים, מסודרים ע"פ שמותיהם, בסדר א"ב. ')[0]
        new = re.sub('@00(.*)', r'<b>\1</b>', data)
        new = re.sub('@22.*', '', new)
        self.texts[self.books.name] = [[l] for l in self.parse_lines(new)]
        self.alts.append(self.altnode(self.books.name, 'סדר מחברים וספרים', f'{self.books.name} 1-3714'))
        authors, essays = re.findall('@00(.*\n[\s\S]*?)(?=@00|$)', data)
        start = 3
        for data, ename, hname in ((authors, 'Authors', 'סדר מחברים'), (essays, 'Compositions', 'סדר ספרים')):
            start += 1
            alt = self.altnode(ename, hname, f'{self.books.name}, {ename} {start}-{start-1+len(data)}', False)
            data = re.findall('@22(.*)\n([\s\S]*?)(?=@22|$)', data)
            letters = [d[0] for d in data]
            data = [d[1] for d in data]
            for i, (letter, chunk) in enumerate(zip(letters, data)):
                entries = re.findall('(@11[\s\S]*?)(?=@11|$)', chunk)
                end = start + len(entries) - 1
                if 'אות' not in letter:
                    letter = f'אות {letter}'
                letter_alt = self.altnode(self.eng_letters[i], letter.replace("'", '')[:5], f'{self.books.name} {start}-{end}', False)
                for l, entry in enumerate(entries):
                    name = re.findall('@11\*?(.*)@33', entry)[0]
                    name = re.sub('[^א-ת "\']', '', name).strip()
                    letter_alt.append(self.altnode(str(l + 1), name, f'{self.books.name} {start + l}', False))
                alt.append(letter_alt)
                start = end + 1
            self.alts[-1].append(alt)

    def parse_hagahot(self):
        data = self.data.split('@00הגהות ותקונים בש"ס, בשמות החכמים, מסודרים ע"פ שמותיהם, בסדר א"ב. ')[1]
        new = re.sub('(?:@00|@22).*', '', data)
        self.texts[self.hagahot.name] = [[l] for l in self.parse_lines(new)]
        self.alts.append(self.altnode(self.books.name, 'הגהות', f'{self.books.name} 1-102'))
        part1, part2 = data.split('@00עוד הגהות בש"ס \n')
        part1 = re.findall('@22(.*)\n([\s\S]*?)(?=@22|$)', part1)
        letters = [d[0] for d in part1]
        part1 = [d[1] for d in part1]
        start = 2
        for letter, chunk in zip(letters, part1):
            entries = re.findall('(@11[\s\S]*?)(?=@11|$)', chunk)
            end = start + len(entries) - 1
            if 'אות' not in letter:
                letter = f'אות {letter}'
            i = getGematria(letter) - 407
            i = sum([int(digit) for digit in str(i - 1)])
            try:
                letter_alt = self.altnode(self.eng_letters[i], letter.replace("'", '')[:5], f'{self.hagahot.name} {start}-{end}', False)
            except IndexError:
                letter_alt = self.altnode('More Hagahot', 'עוד הגהות', f'{self.hagahot.name} {start}-{end}', False)
            self.alts[-1].append(letter_alt)
            start = end + 1
        alt = self.altnode('More Hagahot', 'עוד הגהות', f'{self.hagahot.name} {start}-{end}', False)
        part2 = re.findall('@22(.*)\n([\s\S]*?)(?=@22|$)', part2)
        mass = [d[0] for d in part2]
        part2 = [d[1] for d in part2]
        for mas, chunk in zip(mass, part2):
            mas = mas.strip()
            end = start + len(chunk.split('\n')) - 1
            alt.append(self.altnode(library.get_index(mas).title, mas, f'{self.hagahot.name} {start}-{end}', False))
            start = end + 1
        self.alts[-1].append(alt)

    def parse_all(self):
        self.parse_intro()
        self.parse_almanac()
        self.parse_index()
        self.parse_tanaim_amoraim()
        self.parse_books()
        self.parse_hagahot()

    def post(self):
        '''l = Lexicon()
        l.name = l.index_title = 'Seder HaDorot'
        l.version_lang = l.to_language = 'he'
        l.language = 'heb'
        l.text_categories = []
        try:
            l.save()
        except DuplicateRecordError:
            pass'''

        server = 'http://localhost:9000'
        #server = 'https://jtlinks.cauldron.sefaria.org'
        self.index.node.validate()
        index_dict = {
            "title": self.index.name,
            "categories": ['Reference'],
            "schema": self.index.node.serialize(),
            'default_struct': "Topic",
            "alt_structs": {'Topic': {'nodes': [n.serialize() for n in self.alts]}}}
        post_index(index_dict, server=server)
        for name, text in self.texts.items():
            text = self.housekeep(text)
            version = {'text': text,
                       'versionTitle': 'Seder HaDorot',
                       'versionSource': '',
                       'language': 'he'}
            post_text(f'{self.index.name}, {name}', version, index_count='on', server=server)
        post_link(self.links, server=server, VERBOSE=False)
        for tl in self.topic_links:
            try:
                tl.save()
            except DuplicateRecordError:
                pass
        print(len(self.topic_links))

if __name__ == '__main__':
    p = Parser()
    p.parse_all()
    p.post()
