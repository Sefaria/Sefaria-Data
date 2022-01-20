import os
import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup, element as Element
import re
from sources.functions import getGematria

def del_children(elements):
    new = []
    for element in elements:
        if element.parent not in elements:
            new.append(element)
    return new


class Section():

    def __init__(self, name, day):
        self.name = name
        self.day = day
        self.segments = []
        self.first = None

    def parse(self, elements, is_small=lambda x: x.name == 'small' and x.next_element.name == 'small',
              is_text=lambda x: x.name == 'span' and 'style' in x.attrs and x['style'] in ['font-size:38px;', 'font-size:135%;'],
              is_chapter=lambda x: x.name == 'big' and x.next_element.name == 'b'):

        for element in elements:
            # if self.day.i==6 and self.name=='navi':print(element)
            if self.day.i == 6 and self.name == 'navi' and element.name == 'span' \
                    and 'style' in element.attrs and element['style'] in ['font-size:29px;', 'font-size:109%;']: #Friday haftarah
                self.parse(element.children,
                           is_small=lambda x: x.name=='small' and x.next_element.name=='small' and x.next_element.next_element.name=='small',
                           is_text=lambda x: type(x)==Element.NavigableString and x.strip(),
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
            elif is_chapter(element):
                text = list(element.strings)[0].strip()
                if re.search(r'^[א-פ]{1,2}', text):
                    self.c = getGematria(text)
                    self.v = 1
                else:
                    print('unidentified big text', element)
            elif is_text(element):
                if not isinstance(element, str):
                    element = element.text
                text = ' '.join(element.split())
                self.segments.append({'ref': f'{self.book} {self.c}:{self.v}', 'text': text, 'type': 'text with ref'})

        if self.segments:
            self.refs = [Ref(f'{self.first}-{self.c}:{self.v}')]

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
        tora.parse(self.tora)
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
            navi.ref = [Ref(x) for x in ['Hosea 14:2-10', 'Micah 7:18-20', 'Joel 2:11-27']]
            self.navi = navi
            return
        navi.c = getGematria(navi.c)
        navi.parse(self.navi)
        self.navi = navi

    def parse_ketuvim(self):
        pass

    def parse_mishnah(self):
        pass

    def parse_gemara(self):
        pass

    def parse_zohar(self):
        pass

    def parse_halakha(self):
        pass

    def parse_musar(self):
        pass

    def parse_all(self):
        self.parse_tora()
        self.parse_navi()
        self.parse_ketuvim()
        self.parse_mishnah()
        self.parse_gemara()
        self.parse_zohar()
        self.parse_halakha()
        self.parse_musar()


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
            day.parse_all()

if __name__ == '__main__':
    for file in os.listdir('newdata'):
        print(file)
        week = Week(BeautifulSoup(open(f'newdata/{file}', encoding='windows-1255'), 'html.parser'))
        print(week.parasha)
        week.divide_parts()
        week.parse_days()

        # try:
        #     segs = [len(d.navi.segments) for d in week.days[:5]]
        #     if segs[:5] != [6,4,5,6,5]:
        #         print(segs)
        #     segs = [len(d.navi.refs[0].all_segment_refs())  for d in week.days[:5]]
        #     if segs[:5] != [6,4,5,6,5]:
        #         print(segs)
        # except Exception as e:
        #     print(e,'boo')
        #     pass
