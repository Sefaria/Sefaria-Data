# encoding=utf-8

import re
import codecs
import csv
from data_utilities.util import get_cards_from_trello
from data_utilities.util import getGematria
from sources.local_settings import SEFARIA_PROJECT_PATH
from sefaria.utils.talmud import section_to_daf
from fuzzywuzzy import process, fuzz
from sefaria.model import *

with open('../trello_board.json') as board:
    cards = [card.replace(' on', '') for card in get_cards_from_trello('Parse Rambam Talmud style', board)]
"""
To open files:
for card in cards:
    with codecs.open('{}.txt'.format(card), 'r', 'utf-8') as infile:
        <code here>
"""


def check_header(lines):
    """
    Check that each @11 is followed by an @22 on the same or the following line
    :param lines: list of lines in file
    :return: Boolean
    """

    is_good = True
    previous_line = lines[0]
    for index, next_line in enumerate(lines[1:]):

        if re.match(u'@11', previous_line):
            if re.search(u'@22', previous_line):
                pass
            else:
                if re.search(u'@22', next_line):
                    pass
                else:
                    print 'bad line at {}'.format(index+1)
                    is_good = False
        previous_line = next_line
    return is_good


def align_header(filename):
    """
    Place @11 and @22 on the same line to make for easier parsing
    :param filename: name of file
    """

    with codecs.open(filename, 'r', 'utf-8') as infile:
        old_lines = infile.readlines()
    new_lines = []

    previous_line = old_lines[0]
    for index, next_line in enumerate(old_lines[1:]):

        if re.match(u'@11', previous_line):
            if re.search(u'@22', previous_line):
                pass
            else:
                if re.search(u'@22', next_line):
                    previous_line = previous_line.replace(u'\n', u'')
                else:
                    print 'bad line at {}'.format(index+1)
                    raise KeyboardInterrupt

        new_lines.append(previous_line)
        previous_line = next_line
    else:
        new_lines.append(previous_line)
    with codecs.open(filename+'.tmp', 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)


def format_reference(filename):
    """
    Ensure that each reference line contains an actual reference and that it is encapsulated inside parentheses. Calls
    str.rstrip() on each line to remove trailing spaces.
    DANGER: Will overwrite file!!!
    :param filename: path to file
    """

    with codecs.open(filename, 'r', 'utf-8') as infile:
        file_lines = [re.sub(u' +', u' ', line).replace(u' \n', u'\n') for line in infile]

    fixed_lines = []
    for line in file_lines:
        if re.match(u'@11', line):
            has_reference = re.search(u'@22', line)
            assert has_reference is not None

            ref = re.search(u'@22([\u05d0-\u05ea" ]+)$', line)
            if ref is not None:
                line = line.replace(ref.group(1), u'({})'.format(ref.group(1)))
        fixed_lines.append(line)

    with codecs.open(filename+'.tmp', 'w', 'utf-8') as outfile:
        outfile.writelines(fixed_lines)


class RambamReferenceError(Exception):
    pass


class RambamReference:

    def __init__(self):

        self.reference = None
        self.daf = None
        self.ammud = None
        self._daf_is_sham = False
        self._explicit_ammud = False
        self._he_daf = None
        self._he_ammud = None
        self._previous_daf = None
        self._previous_ammud = None

    def _parse_he_reference(self):
        ref_list = self.reference.split(u' ')
        ammud_pattern = re.compile(u'\u05e2"(\u05d0|\u05d1)')
        data_dict = {
            'daf': None,
            'ammud': None
        }

        # case 1: reference splits into 3
        if len(ref_list) == 3:
            if ref_list[0] != u'דף' or ammud_pattern.search(ref_list[2]) is None:
                print self.reference
                raise RambamReferenceError('Does not match header or ammud patterns')

            self._explicit_ammud = True
            data_dict['ammud'] = ref_list[2]
            data_dict['daf'] = ref_list[1]

        # case 2: reference splits into 2
        elif len(ref_list) == 2:
            # no explicit ammud
            if ref_list[0] == u'דף' and ammud_pattern.search(ref_list[1]) is None:
                self._explicit_ammud = False
                data_dict['daf'] = ref_list[1]

            # no header
            elif ref_list[0] != u'דף' and ammud_pattern.search(ref_list[1]) is not None:
                self._explicit_ammud = True
                data_dict['daf'] = ref_list[0]
                data_dict['ammud'] = ref_list[1]

            else:
                print self.reference
                raise RambamReferenceError("Unrecognized pattern for length 2 reference")

        # case 3: reference has only one word
        elif len(ref_list) == 1:
            if ammud_pattern.search(ref_list[0]):
                # only the ammud was found, treat daf as sham
                self._explicit_ammud = True
                data_dict['ammud'] = ref_list[0]
                data_dict['daf'] = u'שם'
            else:
                data_dict['daf'] = ref_list[0]
                self._explicit_ammud = False

        else:
            print self.reference
            raise RambamReferenceError("Reference must consist of 1-3 words")

        if data_dict['daf'] == u'שם':
            self._daf_is_sham = True
        else:
            self._he_daf = data_dict['daf']
        if self._explicit_ammud:
            self._he_ammud = data_dict['ammud']

    def _construct_reference(self):

        if self._daf_is_sham:
            if self._previous_daf is None:
                print self.reference
                raise RambamReferenceError("Non explicit reference with no previous entry provided")
            self.daf = self._previous_daf
        else:
            self.daf = getGematria(self._he_daf)

        if self._explicit_ammud:
            if self._he_ammud == u'ע"ב':
                self.ammud = 'b'
            elif self._he_ammud == u'ע"א':
                self.ammud = 'a'
            else:
                print self.reference
                raise RambamReferenceError("Invalid entry for ammud")
        else:
            if self._daf_is_sham:
                self.ammud = self._previous_ammud
            else:
                self.ammud = 'a'  # sets the default to 'a'

    def update(self, reference):
        self._previous_ammud = self.ammud
        self._previous_daf = self.daf
        self.reference = re.sub(u"'", u"", reference)
        self.daf = None
        self.ammud = None
        self._daf_is_sham = False
        self._explicit_ammud = False
        self._he_daf = None
        self._he_ammud = None
        self._parse_he_reference()
        self._construct_reference()

    def normal(self, tractate=None):
        if self.reference is None:
            raise RambamReferenceError("No reference set")
        simple = str(self.daf) + self.ammud
        if tractate is None:
            return simple
        else:
            return '{} {}'.format(tractate, simple)

    def ref(self, tractate):
        return Ref(self.normal(tractate=tractate))


def add_english_ref(tractate, safe_mode=False):
    if safe_mode:
        tmp = '.tmp'
    else:
        tmp = ''
    with codecs.open('Rambam Mishnah {}.txt'.format(tractate), 'r', 'utf-8') as infile:
        lines = infile.readlines()

    new_lines = []
    reference = RambamReference()
    for line in lines:
        he_ref = re.search(u'@22\((.*)\)', line)
        if he_ref is not None:
            reference.update(he_ref.group(1))
            new_line = line.replace(he_ref.group(), u'{} @23({})'.format(he_ref.group(), reference.normal(tractate)))
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    with codecs.open('Rambam Mishnah {}.txt{}'.format(tractate, tmp), 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)


def construct_mishnah_map():
    mishnah_map = {}

    with open('{}/data/Mishnah Map.csv'.format(SEFARIA_PROJECT_PATH)) as infile:
        rows = csv.DictReader(infile)
        for row in rows:
            row['Book'] = row['Book'].replace('_', ' ')
            mishnah = 'Mishnah {} {}:{}-{}'.format(
                row['Book'], row['Mishnah Chapter'], row['Start Mishnah'], row['End Mishnah'])
            if row['Book'] not in mishnah_map.keys():
                mishnah_map[row['Book']] = {}
            if row['Start Daf'] not in mishnah_map[row['Book']].keys():
                mishnah_map[row['Book']][row['Start Daf']] = []
            mishnah_map[row['Book']][row['Start Daf']].extend(Ref(mishnah).range_list())
    return mishnah_map


def find_best_match(quote, ref_list, error_tolerance=70):
    """
    given a quote and a list of refs, find the ref that best matches the quote
    :param quote: quote from talmud/mishnah that needs to be resolved
    :param ref_list: list refs that are all possible contenders for the source of quote
    :param error_tolerance: If the best score is lower than this value, method will return None
    :return: The ref which best matches quote
    """

    def split_by_length(input_string, length):
        words = input_string.split()
        return [u' '.join(words[i:i+length]) for i in range(len(words)-(length-1))]

    assert isinstance(ref_list, list)
    for ref in ref_list:
        assert isinstance(ref, Ref)
        assert ref.is_segment_level()

    if len(ref_list) == 1:
        return ref_list[0]
    else:
        ref_texts = [ref.text('he', u'Mishnah, ed. Romm, Vilna 1913').text for ref in ref_list]
        scores = [process.extractOne(quote, split_by_length(ref_text, len(quote.split())), scorer=fuzz.UWRatio)
                  for ref_text in ref_texts]
        results = sorted(zip(ref_list, scores), key=lambda x: -x[1][1])

        if results[0][1][1] > error_tolerance:
            return results[0][0]
        else:
            return None
