import os
import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
from sources.functions import getGematria

def del_children(elements):
    new = []
    for element in elements:
        if element.parent not in elements:
            new.append(element)
    return new


class Section():

    def __init__(self, name):
        self.name = name
        self.segments = []


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
        tora = Section('tora')
        if self.i == 0:
            print(self.week.parasha)
            term = Term().load({'scheme': 'Parasha', 'titles': {'$elemMatch': {'text':  self.week.parasha}}})
            if not term:
                term = Term().load({'scheme': 'Parasha', 'titles': {'$elemMatch': {'text': self.week.parasha.replace('י', '')}}})
            ref = term.ref
            tora.book = Ref(ref).book
            tora.c = Ref(ref).starting_ref().normal().split()[-1].split(':')[0]
        else:
            tora.book = self.get_prev_day().tora.book
            tora.c = self.get_prev_day().tora.c

        for element in del_children(self.tora):
            print(1,element)
            if element.name == 'small' and element.next_element.name == 'small':
                text = element.text.strip()
                if not text:
                    print('no text in', element)
                    continue
                if re.search(r'^\([א-פ]{1,2}\)$', text):
                    tora.v = getGematria(text)
                else:
                    tora.segments.append({'ref': None, 'text': text, 'type': 'instructions'})
            elif element.name == 'big':
                text = element.text.strip()
                if not text:
                    print('no text in', element)
                    continue
                if re.search(r'^[א-פ]{1,2}', text):
                    tora.c = getGematria(text)
                else:
                    print('unidentified big text', element)
            elif element.name == 'span' and 'style' in element.attrs and element['style'] == 'font-size: 150%':
                text = ' '.join(element.text.split())
                tora.segments.append({'ref': f'{tora.book} {tora.c}:{tora.v}', 'text': text, 'type': 'text with ref'})


        self.tora = tora

    def parse_navi(self):
        pass

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

        def handle_day(start, day):
            current = day.tora
            href = lambda x: x.name == 'a' and 'href' in x.attrs
            for element in start.next_elements:
                if href(element):
                    if 'name' in element.attrs and re.search('יום|ליל', element['href']) \
                            and re.search('יום|ליל', element['name']):
                        return element
                    if re.search('נביאים|הפטרת', element['href']):
                        current = day.navi
                    if re.search('כתובים', element['href']):
                        current = day.ketuvim
                    if re.search('משנה', element['href']):
                        current = day.mishnah
                    if re.search('גמרא', element['href']):
                        current = day.talmud
                    if re.search('זוהר', element['href']):
                        current = day.zohar
                    if re.search('הלכה', element['href']):
                        current = day.halakha
                    if re.search('מוסר', element['href']):
                        current = day.musar
                current.append(element)

        start = self.soup.find(attrs={'href': re.compile('יום|ליל'), 'name': re.compile('יום|ליל')})
        day = 0
        while start:
            start = handle_day(start, self.days[day])
            if not self.days[day].navi and day != 5:
                print(day, 'no navi')
            day += 1

    def parse_days(self):
        for day in self.days:
            day.parse_all()

if __name__ == '__main__':
    for file in os.listdir('data')[1:2]:
        print(file)
        week = Week(BeautifulSoup(open(f'data/{file}', encoding='windows-1255'), 'html.parser'))
        week.divide_parts()
        week.parse_days()
        segs = [len(d.tora.segments) for d in week.days]
        if segs[:6] != [7,5,6,7,6,27]:
            print(segs)
