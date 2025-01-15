import os
import re
import csv
from collections import Counter
from lxml import etree
import django
django.setup()
from report import parse_file

TAGS = set()
COUNTER = Counter()

def has_only_text(element):
    return element.text is not None and len(element) == 0

class Entry:

    tags_order = ['head-word', 'pos', 'notes', 'binyan', 'senses']

    def __init__(self, xml):
        self.xml = xml
        self.id = self.xml.get('id')
        self.problems = []
        self._validate_no_text_in_root()
        self._handle_headword()
        #TODO check order of tags

        # for child in self.xml.findall('.//pos'):
        #     real_poses = ['שם מקום', 'נ׳', 'מה״ש', 'שם איש', 'ז׳', 'פ״י', 'נ״ר', 'נ', 'זו״נ', 'מה״ק', 'מה״ח',
        #                   'ז׳ שם איש', 'שה״מ', 'תה״פ׳', 'ז׳ שם מקום', 'פ״ע', 'ת׳', 'שס איש', 'ז״ר', 'מה״י', 'ת׳ ותה״פ',
        #                   'כנ׳', 'פ׳י', 'תה״פ', 'פעו״י', 'מה״ג', 'מה״ג ומה״י', 'פיו״ע', 'מה״ג ומה״ח', ]
        #     fix_yud = ['ני', 'תי', 'זי', ]
        #     add_space = ['ת׳נ׳', 'מה״גז״ר', 'ז׳נ׳', ]
        #     other = ['פעז״י', 'ז״', 'ג׳', 'פע״וי', 'פ״ו', 'נ״', ]
        #     text = child.text
        #     if not text:
        #         continue
        #     text = re.sub('[–·\n;,\.]', '', text).strip()
        #     global TAGS
        #     if text not in real_poses + fix_yud + add_space + other:
        #         print(etree.tostring(xml, pretty_print=True, encoding='utf-8').decode())
        #         TAGS.add(text)
        # for child in self.xml.findall('.//binyan-name'):
        #     binyanim = ['נפ׳', 'אפ׳', 'פיעל', 'פעל', 'התפ׳', 'הפ׳', 'אתפ׳', 'נתפ׳', 'פַעל', 'הופ׳']
        #     global TAGS
        #     text = child.text
        #     if not text:
        #         continue
        #     text = text.strip().replace(',', '')
        #     text = re.sub(',·–>', '', text)
        #     if text not in binyanim:
        #         print(etree.tostring(xml, pretty_print=True, encoding='utf-8').decode())
        # for child in self.xml.findall('.//notes'):
        #     parent = child.getparent()
            # if parent.tag != 'sense':
            #     pos = parent.find('pos')
            #     if parent.tag == 'entry' and pos is not None and ('שם איש' in pos.text or 'שם מקום' in pos.text):
            #         continue
            #     print(1, etree.tostring(xml, pretty_print=True, encoding='utf-8').decode())
        # for child in self.xml.findall('.//number'):
        #     text = re.sub('[ –·]', '', child.text)
        #     if not re.search(r'^\d\)$', text):
        #         print(1, etree.tostring(child, pretty_print=True, encoding='utf-8').decode())
        binyans = [c for c in self.xml if c.tag == 'binyan']
        for binyan in binyans:
            if binyan[0].tag == 'binyan-name':
                self.problems.append('binyan-name without binyam-form before. May be should be sub entry of the previos')
                print(0)
            else:
                print(1)

        for prev, child in zip(self.xml, self.xml[1:]):
            if prev.tag == 'senses' and child.tag == 'binyan':
                self.problems.append('binyan after senses. Maybe should b a new entry')
        for child in self.xml.findall('.//bold'):
            if 'xref' in {c.tag for c in child} and child.text and child.text.strip():
                self.problems.append(f'Strings in bold. Maybe should be a new entry: {child.text.strip()}')
            if child.text and child.text.strip() not in ['', '–', '—', '|']:
                self.problems.append(f'Strings in bold. Maybe should be a new entry: {child.text.strip()}')
            global TAGS
            # TAGS.add(parent.tag)
            TAGS |= {c.tag for c in child}

    def _validate_no_text_in_root(self):
        direct_text = []
        if self.xml.text and self.xml.text.strip():
            direct_text.append(self.xml.text.strip())
        for child in self.xml:
            if child.tail and child.tail.strip():
                direct_text.append(child.tail.strip())
        if direct_text:
            print(f"strings in entry's root: {direct_text}")

    def _handle_headword(self):
        hws = self.xml.findall('head-word')
        if len(hws) < 1:
            print(f'entry id {self.id} has {len(hws)} headwords')
            return
        hw = hws[0]
        if not has_only_text(hw):
            print('head-word tag has more than text')
        self.hw = hw.text.strip()

path = 'data'
report = []
for file in sorted(os.listdir(path), key=lambda x: int(re.findall('^\d+', x)[0])):
    # if file != '02-Beth.xml': continue
    print(file)
    root = parse_file(file)
    entries = root.findall('.//entry')
    for entry in entries:

        tags = [child.tag for child in entry.iterchildren()]
        # if 'notes' in tags:
        #     print(etree.tostring(entry, pretty_print=True, encoding='utf-8').decode())
        d = {'binyan': 1, 'senses': 2}
        tags = [t for t in tags if t in d]
        # if tags and tags[0] == 'binyan':
        # tags = [d[t] for t in tags if t in d]
        # if not all(x<y for x,y in zip(tags, tags[1:])) or ('binyan' in tags and 'senses' not in tags):
        #     print(etree.tostring(entry, pretty_print=True, encoding='utf-8').decode())

        entry = Entry(entry)

        report.append({'problems': '\n'.join(entry.problems), 'xml': etree.tostring(entry.xml, pretty_print=True, encoding='utf-8').decode()})
print(TAGS)
for x in COUNTER:
    if COUNTER[x] > 1:
        print(x)

with open('report for krupnik entries.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['problems', 'xml'])
    w.writeheader()
    for row in report:
        w.writerow(row)
