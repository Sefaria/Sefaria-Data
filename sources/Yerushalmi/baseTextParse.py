# encoding=utf-8

import os
import csv
import re
import bs4
from functools import partial
from itertools import zip_longest
from sources.Yerushalmi.sefaria_objects import *
from data_utilities.ParseUtil import ParsedDocument, Description, ParseState

"""
Let's make sure:
1) Mishnayot run in order (no gaps).
2) There are no halachot that do not have a corresponding Mishnah
"""

STATE = ParseState()  # global storage for keeping track of state


class StateMachine:
    def __init__(self, states):
        self._current_state = 0
        self._states = states

    def advance_state(self):
        self._current_state += 1

    def get_state(self, advance=False):
        value = self._current_state % len(self._states)
        if advance:
            self.advance_state()
        return self._states[value]


def runs_in_order(int_array: list):
    int_array = [int(i) for i in int_array]  # typecasting
    for i, value in enumerate(int_array):
        if i == 0:
            if value != 1:
                return False
        else:
            if value - int_array[i - 1] != 1:
                return False
    return True


def get_chapters(book: bs4.Tag) -> list:
    return list(book.find_all('chapter'))


def get_sections(chapter: bs4.Tag) -> list:
    """
    This method must return a list of Tags. These tags will be both Mishnah and Halakha tags.
    We'd like to return a list of Mishnah-Halakha pairs. Occasionally the Halakha tag might be missing. Ultimately, this
    isn't a problem as we need to treat the pair as a single section anyway.
    """
    mishnayot, halakhot = chapter.find_all('mishna'), {h['num']: h for h in chapter.find_all('halacha')}
    m_numbers = [m.get('num', 'None') for m in mishnayot]
    try:
        if not runs_in_order(m_numbers):
            print(f'Mishnayot out of order at chapter {STATE.get_ref("Chapter", one_indexed=True)}', m_numbers)
    except ValueError:
        print(f'Mishnayot non-ints at chapter {STATE.get_ref("Chapter", one_indexed=True)}', m_numbers)

    sections = []
    for mishna in mishnayot:
        num = mishna.get('num', None)
        halakha = halakhot.get(num, None)
        if halakha:
            del halakhot[num]  # ultimately, we want the halakhot dict to be empty at the end of the loop
        else:
            print(f'missing halakha at Chapter {STATE.get_ref("Chapter", True)} mishnah {num}')
        sections.append((mishna, halakha))
    if len(halakhot) > 0:
        print(f'Halakhot that do not correspond to any Mishnah at {STATE.get_ref("Chapter", one_indexed=True)}',
              list(halakhot.keys()))
        # print(halakhot['u1'])
    return sections


def get_sections_ii(chapter: bs4.Tag, tag_factory):
    mishanyot, halakhot = [], []
    contents = chapter.find_all(re.compile(r'mishna|halacha'))

    for content in contents:
        if content.name == 'mishna':
            """
            Some Halakhot are embedded within a Mishnah. Some tractates don't have any halakhot listed. This logic is 
            reliable for extracting Talmud from within a <mishna> tag, but the enumeration of halakhot is not.
            """
            source_paras = content.find_all('source_para')
            if len(source_paras) > 1:
                new_halacha = tag_factory('halacha', derived=len(halakhot)+1, note=f'extracted from mishna {content["num"]}')
                for source in source_paras[1:]:
                    source = source.extract()
                    new_halacha.append(source)
                content.insert_after(new_halacha)
                halakhot.append(new_halacha)

            content['derived'] = len(mishanyot) + 1
            mishanyot.append(content)
        else:
            content['derived'] = len(halakhot) + 1
            halakhot.append(content)

    mishnayot = {m['derived']: m for m in mishanyot}
    halkhot_numbers = {int(h['derived']) for h in halakhot}
    hanging_mishnayot = [m for d, m in mishnayot.items() if int(d) not in halkhot_numbers]
    hanging_mishnayot.sort(key=lambda x: int(x['derived']))
    result = [(mishnayot.get(halacha['derived'], None), halacha) for halacha in halakhot]
    result += [(m, None) for m in hanging_mishnayot]
    return result
    # return [(mishna, halacha) for mishna, halacha in zip_longest(mishanyot, halakhot, fillvalue=None)]


def test_sections(chapter: bs4.Tag) -> list:
    sections = chapter.find_all(re.compile(r'mishna|halacha'))
    state = StateMachine(['mishna', 'halacha'])
    for section in sections:
        if state.get_state(advance=True) != section.name:
            print(f'Halakhot do not follow Mishnayot in Chapter {STATE.get_ref("Chapter", True)}')
            break
    return []


def test_halakhot_in_order(chapter: bs4.Tag) -> list:
    sections = chapter.find_all('halacha')
    numbers = [h.get('num', None) for h in sections]
    if any('u' in n for n in numbers):
        print(f'strange unmarked halakhot in Chapter {STATE.get_ref("Chapter", one_indexed=True)}', numbers)
    else:
        try:
            in_order = runs_in_order(numbers)
        except ValueError:
            print(f'Unable to decipher numbers in Chapter {STATE.get_ref("Chapter", one_indexed=True)}', numbers)
            return []

        if not in_order:
            print(f'Halakhot do not run in order in Chapter {STATE.get_ref("Chapter", one_indexed=True)}', numbers)
    return []


def simple_clean(dirty: str) -> str:
    cleaned = re.sub(r'\s+', ' ', dirty)
    return cleaned.rstrip().lstrip()


def get_he_segments(section: tuple) -> list:
    """
    :param section: Mishnah or Halacha Tag
    :return: A list of strings. These strings should be the final products shown on Sefaria
    """
    mishnah, halakah = section
    segments = [simple_clean(s.text) for s in mishnah.find_all('source_para')]
    if halakah:
        segments.extend(simple_clean(s.text) for s in halakah.find_all('source_para'))
    return segments


def get_segments_csv(section: tuple, book_title) -> list:
    mishnah, halakha = section
    segments = []
    chapter, section = STATE.get_ref('Chapter', True), STATE.get_ref('Halakha', True)
    if mishnah:
        segments.append({
            'Address': f'{book_title} {chapter}:{section}:{len(segments)+1}',
            'Text': simple_clean(mishnah.find('source_para').text),
            'Official Num': mishnah.get('num', 'missing'),
            'Derived Num': mishnah.get('derived', ''),
            'Note': mishnah.get('note', ''),
            'Type': 'Mishnah'
        })

    if halakha:
        for i, source in enumerate(halakha.find_all('source_para')):
            segment = {
                'Address': f'{book_title} {chapter}:{section}:{len(segments)+1}',
                'Text': simple_clean(source.text),
             }
            if i == 0:
                segment.update({
                    'Type': 'Halakha',
                    'Note': halakha.get('note', ''),
                    'Derived Num': halakha.get('derived', ''),
                    'Official Num': halakha.get('num', ''),
                })
            segments.append(segment)

    return segments


if __name__ == '__main__':
    input_files = [f for f in os.listdir('GuggenheimerXmls') if f.endswith('xml')]
    filednames = [
        'Address', 'Type', 'Text', 'Official Num', 'Derived Num', 'Note',
    ]

    for input_file in input_files:
        # if 'berakhot' not in input_file and 'sabbat' not in input_file:
        #     continue
        print(input_file)
        with open(os.path.join("GuggenheimerXmls", input_file)) as fp:
            soup = bs4.BeautifulSoup(fp, 'xml')
        books = soup.find_all('book')
        for book in books:
            title = book['id']
            print(title)
            section_getter, segment_getter = \
                partial(get_sections_ii, tag_factory=soup.new_tag), partial(get_segments_csv, book_title=title)
            descriptors = [
                Description('Chapter', get_chapters),
                Description('Halakha', section_getter),
                Description('Segment', segment_getter)
            ]
            document = ParsedDocument("Guggenheimer", "גוגנהיימר", descriptors)
            document.attach_state_tracker(STATE)
            document.parse_document(book)
            with open(f'code_output/csv_reports/{title}.csv', 'w') as fp:
                writer = csv.DictWriter(fp, filednames, restval='')
                writer.writeheader()
                document.filter_ja(lambda x: writer.writerow(x))
    from data_utilities.util import ja_to_xml
    # ja_to_xml(document.get_ja(), ["Chapter", "Halakha", "Segment"], "code_output/parse_test.xml")
