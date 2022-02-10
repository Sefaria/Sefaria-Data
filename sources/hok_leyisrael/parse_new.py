import os
import time
import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup, element as Element
import re
from sources.functions import getGematria, post_sheet
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from sefaria.utils.hebrew import strip_cantillation

def del_children(elements):
    new = []
    for element in elements:
        if element.parent not in elements:
            new.append(element)
    return new

def tokenizer(s):
    s = strip_cantillation(s, strip_vowels=True)
    s = re.sub(r'[:,.]', '', s)
    s = re.sub(r'\([^\)]*\)', ' ', s)
    s = re.sub(r'<[^>]*>', ' ', s)
    return s.split()

def unite_refs(refs):
    refs = set(r for ref in refs for r in ref.all_segment_refs())
    new = []
    while refs:
        first = ref = next(iter(refs))
        while ref in refs:
            end = ref
            refs.remove(ref)
            ref = ref.next_segment_ref()
        ref = first.prev_segment_ref()
        while ref in refs:
            first = ref
            refs.remove(first)
            ref = first.prev_segment_ref()
        new.append(Ref(f'{first.normal()}-{end.normal().split()[-1]}'))
    return new


class Section():

    def __init__(self, name, day):
        self.name = name
        self.day = day
        self.segments = []
        self.first = None

    def parse_tanakh(self, elements, is_small=lambda x: x.name == 'small' and x.next_element.name == 'small',
              is_text=lambda x: x.name == 'span' and 'style' in x.attrs and x['style'] in ['font-size:38px;', 'font-size:135%;'],
              is_chapter=lambda x: x.name == 'big' and x.next_element.name == 'b'):

        for element in elements:
            # if self.day.i==4 and self.name=='ketuvim':print(element)
            if self.day.i == 6 and self.name == 'navi' and element.name == 'span' \
                    and 'style' in element.attrs and element['style'] in ['font-size:29px;', 'font-size:109%;']: #Friday haftarah
                self.parse_tanakh(element.children,
                           is_small=lambda x: x.name=='small' and x.next_element.name=='small' and x.next_element.next_element.name=='small',
                           is_text=lambda x: (type(x)==Element.NavigableString and x.strip()) or (x.name=='span' and x['style']=='font-family:Ezra SIL SR;'),
                           is_chapter=lambda x: x.name=='small' and x.next_element.name=='big')

            if is_small(element):
                text = element.text.strip()
                if not text:
                    continue
                if re.search(r'^\([א-פ]{1,2}\)$', text):
                    self.v = getGematria(text)
                    if not self.first:
                        self.first = f'{self.book} {self.c}:{self.v}'
                else:
                    self.segments.append({'ref': None, 'text': text, 'type': 'instructions'})
                    self.append_source({'ref': None, 'text': text, 'type': 'instructions'})
            elif is_chapter(element):
                text = list(element.strings)[0].strip()
                chap_reg = r'^[א-פ]{1,2}' if self.name != 'ketuvim' else r'^[א-ק]{1,3}'
                if re.search(chap_reg, text):
                    self.c = getGematria(text)
                    self.v = 1
                else:
                    print('unidentified big text', element)
            elif is_text(element):
                if not isinstance(element, str):
                    element = element.text
                text = ' '.join(element.split())
                self.segments.append({'ref': f'{self.book} {self.c}:{self.v}', 'text': text, 'type': 'text with ref'})
                self.append_source({'ref': f'{self.book} {self.c}:{self.v}', 'text': text, 'type': 'text with ref'})

        if self.segments:
            self.refs = [Ref(f'{self.first}-{self.c}:{self.v}')]
        self.check()

    def parse_paged(self, elements, rate):

        text = ''
        for e in elements:
            if e.name == 'span' and 'style' in e.attrs and e['style'] in ["font-size:26px;", 'font-size:100%;', 'font-size:99%;']:
                text = e.text
                break
        if not text:
            print('no text day', self.day.i)
        text = re.sub('<[^>]*>', '', text)
        matcher = ParallelMatcher(tokenizer, verbose=False, all_to_all=False, min_words_in_match=8, min_distance_between_matches=0,
                                  only_match_first=True, ngram_size=5, max_words_between=7, both_sides_have_min_words=True)

        next = self.ref.next_section_ref()
        if next:
            if next.next_section_ref():
                ref = f'{self.ref.normal()}-{next.next_section_ref().normal().split()[-1]}'
            else:
                ref = f'{self.ref.normal()}-{next.normal().split()[-1]}'
        else:
            ref = self.ref.normal()

        if re.search("כוּ'|\.", ' '.join(text.split()[:10])):
            text_to_find = re.split("כוּ'|\.", text, 1)[1].strip()
            text_to_find = re.sub('^\.', '', text_to_find).strip()
        else:
            text_to_find = text
        matches = matcher.match([(' '.join(tokenizer(text_to_find)[:15]), 'hok'), ref], return_obj=True)
        matches = [m for m in matches if all(x.ref.normal().split(':')[0] in self.ref.normal() or 'Chadash' in x.ref.normal() or x.mesechta == 'hok' for x in [m.a, m.b])]
        if not matches:
            #print(' '.join(text_to_find.split()[:15]))
            #print('no match for start', self.day.i, text, ref)
            #return
            # ad hoc handling!!!
            if ref == 'Bava Metzia 59a-60a':
                start = 'Bava Metzia 59a:3'
            elif ref == 'Avodah Zarah 2a-3a':
                start = 'Avodah Zarah 2a:2'
            elif ref == 'Shevuot 38b-39b':
                start = 'Shevuot 38b:26'
            else:
                start = Ref(ref).all_segment_refs()[0].context_ref().all_segment_refs()[-1].normal()
        else:
            match = max(matches, key=lambda x: x.score)
            start = match.a.ref if match.a.mesechta != 'hok' else match.b.ref
            start = start.all_segment_refs()[0].normal()

        matches = matcher.match([(' '.join(tokenizer(text_to_find)[-15:]), 'hok'), ref], return_obj=True)
        if not matches:
            # ad hoc!!!
            if ref == 'Zohar 3:271b-3:272b':
                end = '3:274a:2'
            elif ref == 'Berakhot 14a-15a':
                end = '16b:17'
            elif ref == 'Kiddushin 29a-30a':
                end = '30b:14'
            elif ref == 'Bava Metzia 85a-86a':
                end = '85b:3'
            elif ref == 'Bava Kamma 80a-81a':
                end = '83a:8'
            elif ref == 'Avodah Zarah 2a-3a':
                end = '5a:5'
            else:
                print('no match for end', self.day.i, text, ref)
                return
        else:
            match = max(matches, key=lambda x: x.score)
            end = match.a.ref if match.a.mesechta != 'hok' else match.b.ref
            end = end.all_segment_refs()[-1].normal().split()[-1]
        try:
            ref = Ref(f"{start}-{end}")
        except:
            if f"{start}-{end}" == "Zohar Chadash, Midrash HaNe'elam Al Eichah 9-5":
                ref = Ref("Zohar Chadash, Midrash HaNe'elam Al Eichah 9-13")
            else:
                print(f'problem with ref {self.day.i} {start}-{end}')
                return

        # text_len = sum([len(word) for word in tokenizer(text)])
        # ref_len = sum([len(word) for word in tokenizer(ref.text('he').as_string())])
        # if not rate < text_len / ref_len < 1 / rate:
        #     print('strings different', text_len / ref_len, self.day.i, text, ref)

        self.segments.append({'ref': ref, 'text': text, 'type': 'davka text with ref'})
        self.append_source({'ref': ref, 'text': text, 'type': 'davka text with ref'})
        matcher.reset()

    def check(self):
        # matcher = ParallelMatcher(lambda x: re.sub('[^ א-ת]', '', x).split(), verbose=False, all_to_all=False)
        # for segment in self.segments:
        #     if segment['ref']:
        #         matches = matcher.match([segment['ref'], (segment['text'], 1)], return_obj=True)
        #         if not matches:
        #             print('no match', self.day.i, segment)
        refs = [Ref(segment['ref']) for segment in self.segments if segment['ref']]
        all_refs = set(refs)
        if not refs:print('no refs', self.segments)
        if self.segments and all_refs != set([r for ref in self.refs for r in ref.all_segment_refs()]):
            #print(self.day.i, refs, self.refs)
            pass

    def append_source(self, segment):
        if segment['type'] == 'instructions':
            self.day.sources.append({'node': self.day.node,
                                 'outsideBiText': {'he': f"<small>{segment['text']}</small>",
                                                   'en': f"<small>{segment['text']}</small>"}})
            self.day.node += 1
        elif segment['type'] in ['text with ref', 'ref without text']:
            prev = self.day.sources[-1] if self.day.sources else None
            if prev and 'ref' in prev.keys():
                if Ref(segment['ref']).follows(Ref(prev['ref'])):
                    prev['ref'] = Ref(f"{Ref(prev['ref']).all_segment_refs()[0].normal()}-{segment['ref'].split()[-1]}").normal()
                    return
                elif Ref(segment['ref']) == (Ref(prev['ref'])):
                    return
            self.day.sources.append({'node': self.day.node,
                                 'ref': Ref(segment['ref']).normal()})
            self.day.node += 1
        elif segment['type'] == 'davka text with ref':
            self.day.sources.append({'node': self.day.node,
                                 'ref': segment['ref'].normal(),
                                'text': segment['text']})
            self.day.node += 1



class Day():

    def __init__(self, i, week):
        self.i = i
        self.week = week
        self.tora = []
        self.navi = []
        self.ketuvim = []
        self.mishnah = []
        self.talmud = []
        self.zohar = []
        self.halakha = []
        self.musar = []
        self.node = 1
        self.sources = []
        self.sheet = {'status': "public",
                      'sources': self.sources,
                      'owner': 1,
                      'sheetLanguage': 'hebrew',
                      'displayedCollection': 'חק-לישראל',
                      'group': 'חק לישראל',
                      'collections': [{'name': 'חק לישראל', 'slug': 'חק-לישראל'}],
                      'options': {
                          'collaboration': "none",
                          'divineNames': "noSub",
                          'assignable': 0,
                          'bsd': 0,
                          'boxed': 0,
                          'numbered': 0,
                          'highlightMode': 0,
                          'langLayout': "heRight",
                          'layout': "sideBySide",
                          'language': "bilingual"
                      }}

    def get_prev_day(self):
        if self.i == 0:
            return
        return self.week.days[self.i-1]

    def parse_tora(self):
        tora = Section('tora', self)
        if self.i == 0:
            term = Term().load({'scheme': 'Parasha', 'titles': {'$elemMatch': {'text': self.week.parasha}}})
            if not term:
                term = Term().load(
                    {'scheme': 'Parasha', 'titles': {'$elemMatch': {'text': self.week.parasha.replace('י', '')}}})
            ref = term.ref
            tora.all_parasha_ref = ref
            tora.book = Ref(ref).book
            tora.c = Ref(ref).starting_ref().normal().split()[-1].split(':')[0]
        else: #elif self.i < 6:
            tora.book = self.get_prev_day().tora.book
            tora.c = self.get_prev_day().tora.c
        # else:
        #     tora.ref = Ref(self.week.days[0].tora.all_parasha_ref)
        #     tora.segments.append({'ref': tora.ref.normal(), 'text': tora.ref.text('he').text, 'type': 'text with ref'})
        #     self.tora = tora
        #     return
        tora.parse_tanakh(self.tora)
        self.tora = tora

    def parse_navi(self):
        if not self.navi:
            return
        navi = Section('navi', self)
        reg = 'הפטרת (?:[^-]*)- (.*(?![^ ]*$)) (.*)' if self.i == 6 else '^נביאים - ([^-]*)- פרק (.*)'
        br = False
        for element in self.navi:
            if isinstance(element, str):
                continue
            for string in element.stripped_strings:
                if re.search(reg, string):
                    title = string
                    br = True
                    break
            if br:
                break
        navi.book, navi.c = re.findall(reg, title)[0]
        try:
            navi.book = Ref(navi.book.strip()).normal()
        except: #haftarat vayelech
            for x in ['Hosea 14:2-10', 'Micah 7:18-20', 'Joel 2:11-27']:
                self.sources.append({'node': self.node,
                                         'ref': x})
                self.node += 1
            return
        navi.c = getGematria(navi.c)
        navi.parse_tanakh(self.navi)
        self.navi = navi

    def parse_ketuvim(self):
        if not self.ketuvim:
            return
        ketuvim = Section('ketuvim', self)
        reg = '^כתובים - ([^-]*)- פרק (.*)'
        for element in self.ketuvim:
            if isinstance(element, str):
                continue
            for string in element.stripped_strings:
                if re.search(reg, string):
                    ketuvim.book, ketuvim.c = re.findall(reg, string)[0]
                    break
        ketuvim.book = Ref(ketuvim.book.strip()).normal()
        ketuvim.c = getGematria(ketuvim.c)
        ketuvim.parse_tanakh(self.ketuvim)
        self.ketuvim = ketuvim

    def parse_mishnah(self):
        if not self.mishnah:
            return
        mishnah = Section('mishnah', self)
        ref =re.sub('[^Bא-ת]', '', str(self.mishnah[0])).replace('B', ' ').replace('מסכת ', '')
        mishnah.append_source({'type': 'ref without text', 'ref': Ref(ref).normal()})
        self.mishnah = mishnah

    def parse_gemara(self):
        if not self.talmud:
            return
        talmud = Section('talmud', self)
        ref = re.sub('[^\'Bא-ת]', '', str(self.talmud[0])).replace('B', ' ').replace('גמרא ', '').replace("''", '"').replace('ט"ל', 'לט')
        ref = re.sub('^מציעא', 'בבא מציעא', ref)
        talmud.ref = Ref(ref)
        talmud.parse_paged(self.talmud, 0.5)
        self.talmud = talmud

    def parse_zohar(self):
        if not self.zohar:
            return
        zohar = Section('zohar', self)
        ref = str(self.zohar[0]).replace('אחריBדף', 'אחריBמותBדף')
        if 'זוהרBחדש' in ref:
            zohar.ref = Ref("Zohar Chadash, Midrash HaNe'elam Al Eichah")
        else:
            parasha, page = re.sub('[^\'Bא-ת]', '', ref).replace('B', ' ').split(' דף ')
            parasha = Ref(parasha.replace('זוהר', 'זהר, פרשת').replace(' לך', ' לך לך').replace('פרשת הקדמה', 'הקדמת ספר הזוהר').replace('בהעלתך', 'בהעלותך').
                          replace('תשא', 'כי תשא').replace('אמר', 'אמור').replace('בחקתי', 'בחוקותי').replace('בחקותי', 'בחוקותי').replace('פרשת המן', 'המן').
                          replace('פרשת ההאדראזוטאקדישא', 'האדרא זוטא קדישא'))
            part = parasha.normal().split()[-1].split(':')[0]
            part = chr(1487+int(part))
            page = Ref(f'זהר, {part} {page}')
            if not set(parasha.all_segment_refs()) & set(page.all_segment_refs()):
                print('problem with ref', self.i, parasha, page)
            zohar.ref = page
        zohar.parse_paged(self.zohar, 0.7)
        self.zohar = zohar

    def parse_halakha(self):
        if not self.halakha:
            return
        text = ''
        for element in self.halakha:
            if element.name == 'span' and 'style' in element.attrs and element['style'] in ["font-size:26px;", "font-size:98%;"]:
                text = element.text
                break
        if not text:
            print(self.i, 'not finding halakha')
        ref, text = text.split('\n')
        ref = ref.replace("''", '"')
        ref = re.sub('הרמ\'|הר"[מם]?|ה?רמב"ם', 'משנה תורה,', ref)
        ref = re.sub("משנה תורה, [הח]'", 'משנה תורה, הלכות', ref)
        ref = ref.replace('ק"ש', 'קריאת שמע').replace('תפלה', 'תפילה').replace('פרק', '').replace('ש"ע', '').replace('י"ד', 'יו"ד').\
            replace('א"ח', 'או"ח').replace('ההלכות', 'הלכות').replace('ח"מ', 'חו"מ').replace('הלכות שבע', 'הלכות שבת').replace('פי"', 'י"')\
            .replace('יסוד', 'יסודי').replace('הלכות ע"ז', 'הלכות עבודה זרה וחוקות הגויים').replace('ת"ת', 'תלמוד תורה').replace('פכ"', 'כ"').\
            replace('יסודיי', 'יסודי')
        ref = ref.replace("מסי'", "סי'").replace('ואילך', '') #reducing likutim the first siman
        try:
            if not Ref(ref).text('he').text:
                ref = ref.split()
                ref = ' '.join(ref[:-1]) + f'-{ref[-1]}'
                if 'משנה תורה' in ref:
                    ref = ref.replace('פ"', '')
                if not Ref(ref).text('he').text:
                    print(ref, 'no text')
        except:
            ref = ref.replace('ומסימן כ"ד', '')
            Ref(ref)
        matcher = ParallelMatcher(tokenizer, verbose=False, all_to_all=False, min_words_in_match=5, min_distance_between_matches=0,
                                  only_match_first=True, ngram_size=5, max_words_between=7, both_sides_have_min_words=True)
        matches = matcher.match([(text, 'hok'), ref], return_obj=True)
        matches = [m for m in matches if m.score > -0.4]
        refs = [m.a.ref for m in matches] + [m.b.ref for m in matches]
        refs = [r for r in refs if r.normal() != 'Berakhot 58a']
        refs = unite_refs(refs)
        print(self.i)
        if len(refs) != 1:
            # for m in matches:
            #     print(m.a.ref, m.b.ref, m.score)
            print(refs, ref, text)
            with open('log.txt', 'a', encoding='utf-8') as fp:
                fp.write(f'{refs}\n{ref}\n{text}\n')
        time.sleep(5)
        matcher.reset()

        # self.day.sources.append({'node': self.day.node,
        #                          'ref': refs[0].normal(),
        #                         'text': ' '.join(text.split())})
        # self.day.node += 1

    def parse_musar(self):
        pass

    def parse_all(self):
        # self.parse_tora()
        # self.parse_navi()
        # self.parse_ketuvim()
        # self.parse_mishnah()
        # self.parse_gemara()
        # self.parse_zohar()
        self.parse_halakha()
        self.parse_musar()

    def make_sheet(self):
        days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שישי']
        days = ['יום ' + d for d in days]
        days[5] = days[5].replace('יום', 'ליל')
        self.sheet['title'] = f'חק לישראל - {self.week.parasha} {days[self.i]}'
        for source in self.sources:
            if 'ref' in source.keys() and 'text' not in source.keys():
                source['text'] = {'he': ''.join([f"<div>{r.text('he').text}</div>" for r in Ref(source['ref']).all_segment_refs()]),
                                  'en': ''.join([f"<div>{r.text('en').text}</div>" for r in Ref(source['ref']).all_segment_refs()])}
                source['heRef'] = Ref(source['ref']).he_normal()
            elif 'ref' in source.keys() and 'text' in source.keys():
                if Ref(source['ref']).text('en').text:
                    source['text'] = {'he': source['text'],
                                      'en': ''.join([f"<div>{r.text('en').text}</div>" for r in Ref(source['ref']).all_segment_refs()])}
                else:
                    source['text'] = {'he': source['text']}
                    source['text']['en'] = source['text']['he']

                source['heRef'] = Ref(source['ref']).he_normal()



class Week():

    def __init__(self, soup):
        self.soup = soup
        self.parasha = ' '.join(soup.find(text=re.compile('^פרשת')).split())
        self.days = [Day(i, self) for i in range(7)]

    def divide_parts(self):

        day_regex = '(?:יום|ליל)B'

        def handle_day(start, day):
            current = day.tora
            aname = lambda x: x.name == 'a' and 'name' in x.attrs
            for element in start.next_siblings:
                if aname(element):
                    #print(element)
                    if re.search(day_regex, element['name']):
                        return element
                    if re.search('(?:נביאים|הפטרת)B', element['name']):
                        current = day.navi
                    if re.search('כתוביםB', element['name']):
                        current = day.ketuvim
                    if re.search('משנהB', element['name']):
                        current = day.mishnah
                    if re.search('גמראB', element['name']):
                        current = day.talmud
                    if re.search('זוהרB', element['name']):
                        current = day.zohar
                    if re.search('הלכהB', element['name']):
                        current = day.halakha
                    if element['name'] == 'מוסר':
                        current = day.musar
                current.append(element)

        start = self.soup.find(attrs={'name': re.compile(day_regex)})
        day = 0
        while start:
            start = handle_day(start, self.days[day])
            if not self.days[day].navi and day != 5:
                if day == 6:
                    self.days[6].navi = self.days[5].navi
                    self.days[5].navi = []
            if not self.days[day].navi and day != 5:
                print(day, 'no navi')
            if not self.days[day].ketuvim and day < 5:
                print(day, 'no ketuvim')
            if not self.days[day].mishnah and day != 5:
                print(day, 'no mishnah')
            if not self.days[day].talmud and day != 5:
                print(day, 'no talmud')
            if not self.days[day].zohar and day != 5:
                print(day, 'no zohar')
            if not self.days[day].halakha and day != 5:
                print(day, 'no halakha')
            if not self.days[day].musar and day != 5:
                print(day, 'no musar')
            day += 1
        if day != 7:
            print(f'just {day} days')

    def parse_days(self):
        for day in self.days:
            with open('log.txt', 'a', encoding='utf-8') as fp:
                fp.writelines([f'{day.i}\n'])
            day.parse_all()

if __name__ == '__main__':
    server = 'http://localhost:9000'
    with open('log.txt', 'w', encoding='utf-8') as fp:
        fp.write('')
    for file in os.listdir('newdata'):
        print(file)
        with open(f'newdata/{file}', encoding='windows-1255') as fp:
            week = Week(BeautifulSoup(fp, 'html.parser'))
        print(week.parasha)
        with open('log.txt', 'a', encoding='utf-8') as fp:
            fp.write(f'{week.parasha}\n')
        week.divide_parts()
        week.parse_days()
        for day in week.days:
            day.make_sheet()
            #print(post_sheet(day.sheet, server=server)['id'])

        # try:
        #     segs = [len(d.ketuvim.segments) for d in week.days[:5]]
        #     if segs[:5] != [6,4,5,6,5]:
        #         print(segs)
        #     segs = [len(d.ketuvim.refs[0].all_segment_refs())  for d in week.days[:5]]
        #     if segs[:5] != [6,4,5,6,5]:
        #         print(segs)
        # except Exception as e:
        #     print(e,'boo')
        #     pass
