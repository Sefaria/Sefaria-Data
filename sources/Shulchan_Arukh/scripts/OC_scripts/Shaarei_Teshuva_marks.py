# encoding=utf-8

"""
Problem: Shaarei Teshuva uses the Be'er Hetev marks, but does not use all of them and has some of it's own.
Solution: Create unique marks for the Shaarei Teshuva

Step 1: Identify all locations where Be'er Hetev marks go out of order. Manually check if any of these are unique to
Shaarei Teshuva. If so - change the mark to the new Shaarei Teshuva mark. Keep a record of the locations where these
were added.

Step 2: Compare Be'er Hetev marks to the existing text on Sefaria. Any discrepancy should be checked against Shaarei
Teshuva. As before, any changes should be tracked.

Step 3: Parse Shaarei Teshuva and determine which Be'er Hetev markers need to have a Shaarei Teshuva marker added next
to them. Special care needs to be taken in places where a unique Shaarei Teshuva marker has already been added.
Three lists can be made for each siman:
    1) Available Be'er Hetev marks at which a Shaarei Teshuva mark can be added
    2) Shaarei Teshuva markers that are already there
    3) Shaarei Teshuva comments that need a marker
For each comment that needs a marker, I first check if the marker has already been set. If not, I can then look at the
available locations and set the appropriate marker. If no available locations exist, log the location and handle manually.
Once a location has been used to match, remove from the list of available matches.

Any ambiguity should be logged and handled manually. Ambiguity would be more than one comment in Shaarei Teshuva and
more than one mark. I don't think that can happen. For testing purposes, print locations with double marks in Shaarei
Teshuva to the console so that they can be manually reviewed.

It would be wise to first scan Shaarei Teshuva to make sure the marks follow some semblance of order. They don't, but
strange jumps may indicate a Siman jump that was missed. This would include out-of-order and duplicate comments.

Shaarei Teshuva marked with @62

I'll define a StructuredDocument class, which will have a file broken into it's subsequent chapters with no editing.
This can be used to call up individual chapters. StructuredDocument will have a "get_chapter method", and an
"edit_chapter" method. It will be instantiated with a filepath and a regex. This seems to be a decent class, look to see
if it has potential for re-use.
"""

import re
import codecs
from sefaria.model import *
from fuzzywuzzy import fuzz
from sources.functions import getGematria

class StructuredDocument:
    """
    class for extracting specific parts (i.e. chapters) of a text file. Pieces that exist outside the structure (an intro
    for example) will be included, but they will not be as easily accessible as the chapters.
    """

    def __init__(self, filepath, regex):
        with codecs.open(filepath, 'r', 'utf-8') as infile:
            lines = infile.readlines()

        sections, section_mapping = [], {}
        current_section, section_num, section_index = [], None, 0

        for line in lines:
            match = re.search(regex, line)
            if match:
                if len(current_section) > 0:
                    sections.append(u''.join(current_section))
                    if section_num:
                        section_mapping[section_num] = section_index
                    section_index += 1
                    current_section = []
                section_num = getGematria(match.group(1))

            current_section.append(line)
        else:
            sections.append(u''.join(current_section))
            section_mapping[section_num] = section_index

        self._sections = sections
        self._section_mapping = section_mapping

    def get_section(self, section_number):
        section_index = self._section_mapping[section_number]
        return self._sections[section_index]

    def _set_section(self, section_number, new_section):
        section_index = self._section_mapping[section_number]
        self._sections[section_index] = new_section

    def edit_section(self, section_number, callback, *args, **kwargs):
        old_section = self.get_section(section_number)
        new_section = callback(old_section, *args, **kwargs)
        self._set_section(section_number, new_section)

    def get_whole_text(self):
        return u''.join(self._sections)

    def write_to_file(self, filename):
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.write(self.get_whole_text())

    def get_chapter_values(self):
        return sorted(self._section_mapping.keys())


def collect_matches(chapter_text, mark_type, chapter_value):
    regex = load_regex(chapter_value, mark_type)
    return [m.group(1) for m in re.finditer(regex, chapter_text)]


def load_regex(chapter, mark_type):
    """
    Get the necessary regex for markers
    :param chapter:
    :param string mark_type: 'baer_marks', 'shaarei_marks' or 'shaarei_seifim'
    :return: string
    """
    number_group = u'[\u05d0-\u05ea]{1,2}'

    regs = {
        'baer_marks': u'@66\(({})\)'.format(number_group),
        'shaarei_marks': u'@62\(({})\)'.format(number_group),
    }

    if chapter < 242 or chapter > 416:
        regs['shaarei_seifim'] = u'@22\(({})\)'.format(number_group)
    else:
        regs['shaarei_seifim'] = u'@11\(({})\)'.format(number_group)

    return regs[mark_type]


def find_mark_locations(baer_marks, shaarei_marks, shaarei_seifim, chapter):
    locations = []
    if len(baer_marks) != len(set(baer_marks)) or len(shaarei_seifim) != len(set(shaarei_seifim)):
        print u"Double Marker in Chapter {}".format(chapter)
    for seif in shaarei_seifim:
        if seif in shaarei_marks:
            continue
        elif seif in baer_marks:
            locations.append(seif)
        else:
            print u"Unable to locate position for {} in chapter {}".format(seif, chapter)
    return locations


def add_marks_to_chapter(base_document, shaarei_document, chapter_num):
    """
    Given a chapter I can easily extract regexes with a finditer
    This needs to be called three times - twice on base text to find markers, once on Shaarei Teshuva for seifim

    1) Pick a chapter
    2) Get text for that chapter for both base and commentary
    3) Extract all three match sets
    4) Given match sets, decide where @62 needs to be added -> This can return a regex. Should be an independant function
    5) Edit given chapter

    :param StructuredDocument base_document:
    :param StructuredDocument shaarei_document:
    :param int chapter_num:
    """
    def repl(x):
        return re.sub(u'@66\(([\u05d0-\u05ea]{1,3})\)', u'\g<0> @62(\g<1>)', x.group())

    base_chapter, shaarei_chapter = base_document.get_section(chapter_num), shaarei_document.get_section(chapter_num)

    baer_marks     = collect_matches(base_chapter,    'baer_marks',     chapter_num)
    shaarei_marks  = collect_matches(base_chapter,    'shaarei_marks',  chapter_num)
    shaarei_seifim = collect_matches(shaarei_chapter, 'shaarei_seifim', chapter_num)

    locations = u'@66\(({})\)'.format(
        u'|'.join(find_mark_locations(baer_marks, shaarei_marks, shaarei_seifim, chapter_num)))

    base_document.edit_section(chapter_num, lambda x: re.sub(locations, repl, x))


def replace_em():
    with codecs.open(u'../../txt_files/Orach_Chaim/part_3/שולחן ערוך אורח חיים חלק ג שערי תשובה.txt', 'r', 'utf-8') as infile:
        the_text = infile.read()

    def repl(x):
        fixed = re.sub(ur'[\'"]', u'', x.group(1))
        return u'@00{}'.format(fixed)
    s = re.compile(ur'@00\u05e1\u05d9(?:\'|\u05de\u05df)? ([\u05d0-\u05ea\'\"]{1,5})')
    new_text = re.sub(s, repl, the_text)
    with codecs.open('../../txt_files/Orach_Chaim/part_3/test.txt', 'w', 'utf-8') as outfile:
        outfile.write(new_text)


def print_em():
    with codecs.open(u'../../txt_files/Orach_Chaim/part_3/שולחן ערוך אורח חיים חלק ג שערי תשובה.txt', 'r', 'utf-8') as infile:
        the_text = infile.read()
    matches = re.findall(u'@00[^n]+', the_text.replace(u'\n', u'n'))
    with codecs.open(u'../../txt_files/Orach_Chaim/part_3/stuff.txt', 'w', 'utf-8') as outfile:
        outfile.write(u'\n'.join(matches))

source_filename = {
    'volI': u'../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א.txt',
    'volII': u'../../txt_files/Orach_Chaim/part_2/שולחן ערוך אורח חיים חלק ב מחבר.txt',
    'volIII': u'../../txt_files/Orach_Chaim/part_3/מחבר שולחן ערוך אורח חיים חלק ג.txt',
    'shaarei_I': u'../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א שערי תשובה.txt',
    'shaarei_II': u'../../txt_files/Orach_Chaim/part_2/שולחן ערוך אורח חיים חלק ב שערי תשובה.txt',
    'shaarei_III': u'../../txt_files/Orach_Chaim/part_3/שולחן ערוך אורח חיים חלק ג שערי תשובה.txt',
    'testI': u'../../txt_files/Orach_Chaim/part_1/test.txt',
    'testII': u'../../txt_files/Orach_Chaim/part_2/test.txt',
    'testIII': u'../../txt_files/Orach_Chaim/part_3/test.txt',
}
base_doc = StructuredDocument(source_filename['volI'], u'@22([\u05d0-\u05ea]{1,4})')
shaarei_doc = StructuredDocument(source_filename['shaarei_I'], u'@00([\u05d0-\u05ea]{1,4})')
available_chapters = shaarei_doc.get_chapter_values()


for c in available_chapters:
    add_marks_to_chapter(base_doc, shaarei_doc, c)

with codecs.open(source_filename['volI'], 'w', 'utf-8') as outfile:
    outfile.write(base_doc.get_whole_text())



"""
Siman 267 has two א seifim and is a good test case.

Since we are generating marks in Shulchan Arukh from the commentary, we have no ability to cross reference across
both data sources. There do seem to be several OCR errors in the seif marks inside Sha'arei Teshuva that we have
no good way of picking up.

One potential solution be to compare the first word after the mark to the first word of the Seif (a fuzzy match
would be best). This might be a bit naive though.


The following will need to be a part of the regex to grab a word:
([^ ]*( [^\u05d0-\u05ea])?)*
This allows jumping over any added markers that might be in front of the first word.

find_mark_locations() will give the values that will get an @62 mark added. For each location, I simply 
check the next word.

@66\(<location>)\)([^ ]*( [^\u05d0-\u05ea])?)* (?P<dh>[\u05d0-\u05ea]+)

In Sha'arei Teshuva, for the first pass, I'll just search for a series of Hebrew characters preceded and followed
by non Hebrew characters. If that turns up too much garbage, I'll refine.
"""

def compare_dh(base_document, shaarei_document, chapter_num):

    base_chapter, shaarei_chapter = base_document.get_section(chapter_num), shaarei_document.get_section(chapter_num)

    baer_marks = collect_matches(base_chapter, 'baer_marks', chapter_num)
    shaarei_marks = collect_matches(base_chapter, 'shaarei_marks', chapter_num)
    shaarei_seifim = collect_matches(shaarei_chapter, 'shaarei_seifim', chapter_num)

    locations = find_mark_locations(baer_marks, shaarei_marks, shaarei_seifim, chapter_num)
    requires_examination = []

    for i in locations:
        shaarei_dh, base_dh = None, None
        base_match = re.search(u'@66\({}\)([^ ]*( [^\u05d0-\u05ea])?)* (?P<dh>[\u05d0-\u05ea]+)'.format(i), base_chapter)
        if not base_match:
            print "No dh for {} found in chapter {}".format(i, chapter_num)
            requires_examination.append((chapter_num, i))
        else:
            base_dh = base_match.group('dh')

        shaarei_match = re.search(u'@22\({}\)[^\u05d0-\u05ea]*(?P<dh>[\u05d0-\u05ea]+)'.format(i), shaarei_chapter)
        if not shaarei_match:
            print "No dh for {} found in chapter {} of Shaa'rei Teshuva".format(i, chapter_num)
            requires_examination.append((chapter_num, i))
        else:
            shaarei_dh = shaarei_match.group('dh')

        if base_dh is not None and shaarei_dh is not None:
            ratio = fuzz.ratio(base_dh, shaarei_dh)
            if ratio < 80.0:
                requires_examination.append((chapter_num, i))
                print u'Chapter {} seif {}'.format(chapter_num, i)
                print u'Base: {}'.format(base_dh)
                print u'Shaarei: {}'.format(shaarei_dh)
                print u'Score : {}\n'.format(ratio)
    return requires_examination


