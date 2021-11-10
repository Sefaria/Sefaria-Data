# encoding=utf-8

import re
import os
import csv
import bs4
import time
import json
import zipfile
from typing import List
from functools import reduce
from itertools import zip_longest
import data_utilities.text_align as align
from data_utilities.sanity_checks import find_out_of_order
import simpleaudio
from sources.functions import post_text, post_index, add_term, add_category
from data_utilities.util import getGematria, traverse_ja, word_index_from_char_index
from sources.Yerushalmi import sefaria_objects
from sefaria.utils.hebrew import strip_nikkud
from sefaria.model.schema import AddressTalmud
from sefaria.datatype.jagged_array import JaggedArray
from concurrent.futures.process import ProcessPoolExecutor
from data_utilities.util import ja_to_xml, traverse_ja
from data_utilities.normalization import TextSanitizer, sanitized_words_to_unsanitized_words
from data_utilities.ParseUtil import *
from data_utilities.dibur_hamatchil_matcher import match_ref, match_text

time_start = time.time()


# file_list = [os.path.join('mechon-mamre', f) for f in os.listdir('./mechon-mamre') if f.endswith('html')]
# for f in file_list:
#     # print(f)
#     with open(f) as fp:
#         soup = bs4.BeautifulSoup(fp, 'html5lib')
#         print(f, soup.h2.text)


"""
For the sake of this script, I'm going to collect all the sanitizers and mapping data into one place. That
will allow me to easily pull out individual pieces of data in a more limited scope. The drawback is this is an
incredibly stateful approach, which I usually abhor. Although ultimately, this object is nearly the final result
of the script. For the sake of this project, I believe this will ultimately help make the final push a little
easier.

 {
  <tractate-title>: [
    {
      guggenheimer: <guggenheimer-segments>,
      mehon-sanitizer: <sanitizer-for-mehon>  # this contains both the word list and original division,
      mapping: the result from create_tractate_mappings,
      halkha-indices: <array>
    }
  ]

}
"""

ASSEMBLER = {}
SANITIZATION_REGEX = r'((?<=\s)\([^()]+\)\s)|[.:]'


"""
In order to put the mehon text together, I need to convert the sanitized index into a non-sanitized index. The method
util.convert_normalized_indices_to_unnormalized_indices will do this for a character index. I need to be able to take
a word index, convert to a character index, get the unsanitzed char index then the unsanitized word index. It might be
more beneficial to not use exact char-to-word indices, but rather to "round down" or rather "backwards" to the nearest
space.

Let's start easy. Take the guggenheimer. Work out which segments are start of a new halakha. Then assemble a JaggedArray
"""


def assemble_guggenheimer_chapter(segments, mappings, halakha_segments, mishnayot_included=True, verbose=False):

    def correct_halakha(halkha_number, segment_number):
        if segment_number == -1:
            return True  # no halakha transition if we couldn't match the segment
        return halakha_segments[halkha_number] <= segment_number < halakha_segments[halkha_number + 1]

    segment_map, clean_divisions = mappings['word_mapping'], mappings['clean']
    assert len(segments) == len(segment_map) == len(clean_divisions)
    current_halakha = 0
    clean = True

    ja, error_list = JaggedArray(), []
    for i, segment in enumerate(segments):
        segment_start, segment_end = segment_map[i]
        first_check = True

        """
        check that:
        1. if advancing, check that ja isn't blank - can do this at the end?
        2. if advancing, check that we have a clean break
        3. always check that start and end are in the same halakha
        """

        while not correct_halakha(current_halakha, segment_start):
            current_halakha += 1
            if first_check:
                first_check = False
                # we expect guggenheimer to end a segment at the exact location where a Vilna halakha ends
                clean_break = clean_divisions[i][0] and clean_divisions[i-1][1]
                if not clean_break:
                    clean = False
                    error_message = f'possible issue with first gemarra segment of halakha {current_halakha} segment number: {i+1}'
                    error_list.append(error_message)
                    if verbose:
                        print(error_message)
        if not correct_halakha(current_halakha, segment_end):
            clean = False

            try:
                segment_number = len(ja.get_element([current_halakha]))
            except IndexError:
                segment_number = 1 if mishnayot_included else 2
            error_message = f'{current_halakha+1}:{segment_number} segment num: {i+1} bridges two halakhot (one indexed)'
            error_list.append(error_message)
            if verbose:
                print(error_message)
                print(segment)
                
        if not mishnayot_included and current_halakha >= len(ja):
            append_in_ja(ja, current_halakha, 'חסרה משנה')  # add a placeholder segment as a placeholder for mishnah
        append_in_ja(ja, current_halakha, segment)

    if not all([len(x) > 0 for x in ja.array()]):
        clean = False
        error_message = 'empty halakhot found'
        error_list.append(error_message)
        if verbose:
            print(error_message)
    return ja.array(), clean, error_list


def assemble_mehon_segments(mehon_chapter, sanitized_chapter, mappings, sanitizer):
    word_indices = mappings['matches']
    unsanitized_word_indices = sanitized_words_to_unsanitized_words(mehon_chapter, sanitized_chapter, sanitizer, word_indices)
    unsanitzed_word_list = mehon_chapter.split()
    segments = []
    for indices in unsanitized_word_indices:
        start, end = indices
        # if start == 0:
        #     debugging_method(mehon_chapter, end)
        if -1 in indices:
            segments.append('')
        else:
            segments.append(' '.join(unsanitzed_word_list[start:end+1]))
    return segments


def assemble_mehon_chapter(mehon_segments, guggenheimer_ja, mishnayot):
    ja = JaggedArray()
    reversed_mishnayot = mishnayot[::-1]
    prev_halakha = -1
    # for mehon_segment, gugg_segment in zip(mehon_segments, traverse_ja(guggenheimer_ja)):
    gug_iter = traverse_ja(guggenheimer_ja)
    for mehon_segment in mehon_segments:
        gugg_segment = next(gug_iter)
        current_halakha = gugg_segment['indices'][0]
        if current_halakha != prev_halakha:  # new halakha
            try:
                mishna = reversed_mishnayot.pop()
            except IndexError:
                mishna = 'חסרה משנה'
            prev_halakha = current_halakha
            # append_in_ja(ja, current_halakha, mishna)
            try:
                h = ja.get_element([current_halakha])
                h.insert(0, mishna)
            except IndexError:
                ja.set_element([current_halakha, 0], mishna)
            gugg_segment = next(gug_iter)
            current_halakha = gugg_segment['indices'][0]
        append_in_ja(ja, current_halakha, mehon_segment)

    return ja.array()


class DividedSegments:

    def __init__(self, division_length, segment_offset=0, word_offset=0):
        self._division_length = division_length
        self.segment_offset = segment_offset
        self._original_segments = []
        self._divided_segments = []
        self._division_indices = []
        self._word_list = []
        self.word_offset = word_offset

    def set_segments(self, segments):
        self._original_segments = segments
        division = self.divide_segments(segments, self._division_length, self.segment_offset)
        self._division_indices = division['indices']
        self._divided_segments = division['segments']

    def get_segments(self):
        return tuple(self._divided_segments)

    def set_words(self, words):
        self._word_list = words

    def get_words(self):
        return tuple(self._word_list)

    def get_original_segments(self):
        return tuple(self._original_segments)

    def get_division_indices(self):
        return tuple(self._division_indices)

    segments = property(get_segments, set_segments)
    words = property(get_words, set_words)

    def realign_mapping(self, map_indices: list, drop_ooo=False) -> dict:
        """

        :param map_indices: mapping indices. key 'matches' from `match_text
        :param drop_ooo: drop Out Of Order indices. If this is true, we will regard indices that are out of order as
        a miss. For example
        (0, 4), (10, 14), (5, 9)  -> (0, 4), (-1, -1), (5, 9)
        :return:
        """
        new_mapping = {'matches': [], 'match_text': []}
        if drop_ooo:
            out_of_order = set(out_of_order_segments(map_indices))
        else:
            out_of_order = set()

        for segment_number, (segment, division_indices) in enumerate(
                zip(self._original_segments, self._division_indices)):
            segment_start, segment_end = division_indices

            if segment_start in out_of_order:
                first_word = -1
            else:
                first_word = map_indices[segment_start][0]

            if (segment_end - 1) in out_of_order:
                last_word = -1
            else:
                last_word = map_indices[segment_end - 1][1]

            # first_word, last_word = map_indices[segment_start][0], map_indices[segment_end - 1][1]

            if last_word <= first_word:  # end must be larger than beginning, otherwise set this to a miss
                last_word = -1

            if first_word == -1:
                if segment_number == 0:
                    first_word = 0
                else:
                    last_match = new_mapping['matches'][-1][1]
                    first_word = last_match + 1 if last_match > 0 else first_word

            if last_word == -1:
                if segment_number == len(self._division_indices) - 1:
                    last_word = len(self._word_list) - 1
                else:
                    next_segment = map_indices[segment_end]
                    next_match = map_indices[segment_end][0]

                    # we don't want to fill in missing information if there is bad data in the next segment
                    if segment_end not in out_of_order and -1 not in next_segment and next_match-1 > first_word:
                        last_word = next_match -1
                    # last_word = next_match - 1 if -1 not in next_segment or segment_end in out_of_order else last_word

            if -1 in (first_word, last_word):
                aligned_text = ''
            else:
                aligned_text = ' '.join(self._word_list[first_word: last_word + 1])

            new_mapping['match_text'].append((segment, aligned_text))
            new_mapping['matches'].append((first_word, last_word))

        # sanity check. The error correction code can make mistakes in rare cases
        out_of_order = out_of_order_segments(new_mapping['matches'])
        for index in out_of_order:
            if new_mapping['matches'][index][0] > -1:
                new_mapping['matches'][index] = (-1, new_mapping['matches'][index][1])
                new_mapping['match_text'][index] = (new_mapping['match_text'][index][0], '')

        return new_mapping

    def repair_mapping(self, map_indices: list) -> dict:
        pass

    @staticmethod
    def divide_segments(segments, division_length, starting_segment_index=0):
        divided_segments, segment_indices = [], []
        current_index = starting_segment_index
        for segment in segments:
            segment_start = current_index
            segment_words = segment.split()
            divider = 0
            while divider < len(segment_words):
                divided_segments.append(' '.join(segment_words[divider:divider + division_length]))
                divider += division_length
                current_index += 1
            segment_indices.append((segment_start, current_index))
        return {'segments': divided_segments, 'indices': segment_indices}


def get_mehon_halakhot(mehon_chapter):
    """
    obtain the indices at which halakhot start in a list of mehon segments
    :return:
    """
    result = [0]
    for halakha in mehon_chapter:
        result.append(result[-1] + len(halakha))
    return result


def word_mapping_to_segments(word_mapping: List[tuple], sanitizer: TextSanitizer) -> dict:
    """
    match_text returns word mappings. This method will convert a mapping list into a segment map.

    Returns a dict with keys: { mapping, clean }.
    clean maps to an array of boolean pairs. If a value is True, that means that the mapping index is exactly at the
    segment boundary.
    :param word_mapping:
    :param sanitizer:
    :return:
    """
    def get_segment(word_index):
        if word_index < 0:
            return -1
        else:
            return sanitizer.check_sanitized_index(word_index)

    result = {
        'word_mapping': [],
        'clean': [],
    }
    segment_start_indices = sanitizer.get_sanitized_word_indices()
    for pair in word_mapping:
        start, end = pair
        start_segment, end_segment = get_segment(start), get_segment(end)
        result['word_mapping'].append((start_segment, end_segment))

        if start == -1:
            start_clean = False
        else:
            start_clean = start == segment_start_indices[start_segment]

        # working out if the end is clean has more edge cases to handle
        if end == -1:
            end_clean = False
        elif end_segment < len(segment_start_indices) - 1:
            # the end is clean if the next segment begins on the next word
            end_clean = end + 1 == segment_start_indices[end_segment+1]
        else:
            # if this is the last segment, we need to know how many words are in the section
            end_clean = end == len(sanitizer.get_sanitized_word_list()) - 1
        result['clean'].append((start_clean, end_clean))
    return result



def create_map_repair(mapping: list, comment_segments: list, base_text_words: list, output_file=None):
    """
    :param mapping: match indices. (the value for "matches" returned from match_text)
    :param comment_segments: list of comments fed to match_text
    :param base_text_words: list of words that represent the base text fed to match_text
    :param output_file:
    :return:
    """
    mapping_gaps = get_mapping_gaps(mapping, len(base_text_words))
    if len(mapping_gaps) == 0:
        return None, None
    segment_edits, html_rows = [], []
    for gap in mapping_gaps:
        gap_start, gap_end = gap['segments']
        segments = comment_segments[gap_start: gap_end+1]
        for seg_num, seg in enumerate(segments, gap_start):
            segment_edits.append({
                'index': seg_num,
                'gap_start': gap['words'][0],
                'gap_end': gap['words'][1] - 1,  # actual index of the final word, to be consistent with match_text
                'content': seg,
                'match_words': ''
            })
            if seg_num == gap_start:
                words = ' '.join(base_text_words[gap['words'][0]:gap['words'][1]])
                html_rows.append(
                    f'<tr><td>{seg_num}</td><td>{seg}</td><td rowspan="{len(segments)}">{words}</td></tr>'
                )
            else:
                html_rows.append(
                    f'<tr><td>{seg_num}</td><td>{seg}</td></tr>'
                )
    if output_file:
        assert output_file.endswith('.csv')
        with open(output_file, 'w') as fp:
            fieldnames = ['index', 'gap_start', 'gap_end', 'content', 'match_words']
            writer = csv.DictWriter(fp, fieldnames)
            writer.writeheader()
            writer.writerows(segment_edits)
    return segment_edits, html_rows


def create_css():
    return '''
          th, td {
            padding: 8px;
            border: 1px solid #ddd
          }
          td {
            direction: rtl;
            text-align: right;
          }
          tr:nth-child(odd) {
            background-color: #f2f2f2;
          }
          tr.bridging, tr.unmatched, tr.exception, tr.nonconsecutive {
            background-color: #ff0000;
          }
          tr:hover {
            background-color: #ccffff;
          }
          td:nth-child(1) {
            direction: ltr;
            text-align: left;
          }
          tr.error {
            background-color: #ff4242;
          }
          tr.error:hover {
            background-color: #fa7a7a
          }
        '''


def create_helper_html(html_rows, output_file):
    table_rows = '\n'.join(html_rows)
    output = f'''
    <!DOCTYPE html>
      <html><meta charset="utf-8">
        <head>
          <style type="text/css">{create_css()}</style>
        </head>
        <body>
          <table>
            <tr><th>Segment Number</th><th>Comment Segment</th><th>Base Text Words (Unmatched)</th></tr>
            {table_rows}
          </table>
        </body>
      </html>  
    '''
    with open(output_file, 'w') as fp:
        fp.write(output)


# def prepare_texts_for_mapping(tractate: sefaria_objects.Index, talmud_only):
#     gug_tractate_chapters = grab_guggenheim_chapters(tractate.title, talmud_only)
#     he_title = re.sub(r'^תלמוד ירושלמי ', '', tractate.get_title('he'))
#     mehon = get_segments_from_raw(f'mechon-mamre/{he_title}.html')
#     mehon_ja = create_chap_ja(mehon, talmud_only)
#     mehon_chaps = three_to1ja(mehon_ja)
#     mehon_text, gug_text = [], []
#     for chap_num in range(len(mehon_chaps)):
#         mehon_text = ' '.join(mehon_chaps[chap_num])
#         mehon_text = re.sub(r'[.:]', '', mehon_text)
#         mehon_text = re.sub(r'(?<=\s)\([^()]+\)\s', '', mehon_text).split()
#         gug_text = [m.replace('־', ' ') for m in gug_tractate_chapters[chap_num]]
#         gug_text = [strip_nikkud(m) for m in gug_text]
#         gug_text = [re.sub(r'[.:]', '', m) for m in gug_text]
#     return gug_text, mehon_text


def out_of_order_segments(mapping):
    """
    We can define two types of "out of order" segments:
    Fully out of order, e.g [1, 5], [10, 14], [6, 9]
    Partially out of order, e.g [1, 5], [4, 9], [10, 14]
    In the scope of this mdoule, we enforce that for every mapping segment n, n[0] < n[1] which makes the following
    impossible: [1, 5], [6, 3], [10, 14]
    :param mapping:
    :return:
    """
    # partially out of order
    out_of_order = set()
    for i, _ in enumerate(mapping[1:], 1):
        current, previous = mapping[i], mapping[i-1]
        if current[0] <= previous[1]:
            out_of_order.add(i)

    # fully out of order
    temp_mapping = [j[0] if i not in out_of_order else 9999 for i, j in enumerate(mapping) ]
    for i in find_out_of_order(temp_mapping):
        out_of_order.add(i)

    return sorted(list(out_of_order))


def mark_out_of_order_as_miss(mapping_dict):
    mapping = mapping_dict['matches']
    indices = out_of_order_segments(mapping)
    for item in indices:
        mapping[item] = (-1, -1)



def create_tractate_mappings(tractate: sefaria_objects.Index, talmud_only=True):
    print(tractate.title)
    tractate_assembler = []
    output_dir = f'code_output/mapping_files/{tractate.title.replace(" ", "_")}'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    gug_tractate_chapters = grab_guggenheim_chapters(tractate.title, talmud_only)
    gug_mishnayot_chapters = three_to1ja(grab_guggenheim_chapters(tractate.title, mishna_only=True))
    he_title = re.sub(r'^תלמוד ירושלמי ', '', tractate.get_title('he'))
    mehon = get_segments_from_raw(f'mechon-mamre/{he_title}.html')
    mehon_ja = create_chap_ja(mehon, lambda x: 'גמרא' in x['meta'])
    mishnayot_ja = create_chap_ja(mehon, lambda x: 'משנה' in x['meta'])
    for i, mishna_chapter in enumerate(mishnayot_ja):
        for j, halakha in enumerate(mishna_chapter):
            if len(halakha) > 1:
                mishnayot_ja[i][j] = [' '.join(halakha)]
    mehon_chaps, mishnayot_chaps = three_to1ja(mehon_ja), three_to1ja(mishnayot_ja)
    errors = [0] * len(mehon_chaps)
    for chap_num in range(len(mehon_chaps)):
        # halakha_indices = [0] + [len(c) for c in mehon_ja[chap_num]]
        halakha_indices = get_mehon_halakhot(mehon_ja[chap_num])
        mapping_file = os.path.join(output_dir, f'chapter_{chap_num + 1}_mapping.json')
        raw_mapping_file = mapping_file.replace('chapter', 'raw_chapter')
        # if os.path.exists(mapping_file):
        #     continue
        print(tractate.title, chap_num + 1)
        sanitizer = TextSanitizer(mehon_chaps[chap_num], r'\s+')
        sanitizer.set_sanitizer(lambda x: re.sub(SANITIZATION_REGEX, '', x))
        sanitizer.sanitize()
        # mehon_text_original = ' '.join(mehon_chaps[chap_num])
        # mehon_text_1 = re.sub(r'[.:]', '', mehon_text_original)
        # mehon_text_1 = re.sub(r'(?<=\s)\([^()]+\)\s', '', mehon_text_1)

        # mehon_text_2 = re.sub(r'((?<=\s)\([^()]+\)\s)|[.:]', '', mehon_text_original)
        # print('both versions equivalent?', mehon_text_1.split() == sanitizer.get_sanitized_word_list())
        mehon_text = sanitizer.get_sanitized_word_list()

        """
        I need to be able to say Halakha x is equivalent to words[x:y]. Even better, I just need to say "this group of
        words belong in segment x".
        """

        gug_text = [m.replace('־', ' ') for m in gug_tractate_chapters[chap_num]]
        gug_text = [strip_nikkud(m) for m in gug_text]
        gug_text = [re.sub(r'[.:]', '', m) for m in gug_text]
        divide = DividedSegments(15)
        divide.segments = gug_text
        if os.path.exists(raw_mapping_file):
            with open(raw_mapping_file) as fp:
                mapping = json.load(fp)
        else:
            mapping = match_text(mehon_text, divide.segments, place_all=True, strict_boundaries='text',
                                 place_consecutively=True, daf_skips=3, rashi_skips=3, overall=4)
            mapping['matches'] = [tuple(int(j) for j in i) for i in mapping['matches']]

        # we want to place the data necessary to bring back the original segments into the file
        mapping['realignment'] = divide.get_division_indices()
        with open(raw_mapping_file, 'w') as fp:
            json.dump(mapping, fp)

        fixed_mapping = divide.realign_mapping(mapping['matches'], True)
        fixed_mapping['matches'] = [tuple(int(j) for j in i) for i in fixed_mapping['matches']]
        fixed_mapping.update(word_mapping_to_segments(fixed_mapping['matches'], sanitizer))

        tractate_assembler.append({
            'guggenheimer': gug_tractate_chapters[chap_num],
            'mehon-sanitizer': sanitizer,
            'mapping': fixed_mapping,
            'halakha-indices': halakha_indices,
            'mehon-mishnayot': mishnayot_chaps[chap_num],
            'gugg-mishnayot': gug_mishnayot_chapters[chap_num],
        })

        with open(mapping_file, 'w') as fp:
            json.dump(fixed_mapping, fp)
        out_of_order = out_of_order_segments(fixed_mapping['matches'])
        chapter_edits, html_rows = create_map_repair(
            fixed_mapping['matches'], gug_text, mehon_text,
            os.path.join(output_dir, f'chapter_{chap_num + 1}_repair.csv')
        )
        if chapter_edits:
            errors[chap_num] += len(chapter_edits)
        bad_segments = out_of_order + [c['index'] for c in chapter_edits] if chapter_edits else out_of_order
        if None not in (chapter_edits, html_rows):
            print(f'making repair file for {tractate.title} {chap_num+1}')
            create_helper_html(html_rows, os.path.join(output_dir, f'chapter_{chap_num + 1}_repair.html'))
        review_document = create_review_document(mapping_file, gug_text, mehon_text, bad_segments)
        with open(os.path.join(output_dir, f'{tractate.title}_{chap_num+1}_review.html'), 'w') as fp:
            fp.write(review_document)

        errors[chap_num] += len(out_of_order)
    ASSEMBLER[tractate.title] = tractate_assembler
    return errors


def zip_review_documents():

    review_files = []
    for directory in os.listdir('code_output/mapping_files'):
        full_directory = os.path.join('code_output/mapping_files', directory)
        review_files.extend([os.path.join(full_directory, f) for f in os.listdir(full_directory)
                             if f.endswith('review.html')])

    with zipfile.ZipFile('code_output/map_review.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in review_files:
            zf.write(f, arcname=re.sub('/?code_output/mapping_files/?', '', f))


def divide_segments_from_failed_match(mapping, comment_segments, base_words, division_length):
    mapping_gaps = get_mapping_gaps(mapping, len(base_words))

    divisions = []
    for gap in mapping_gaps:
        division = DividedSegments(division_length, gap['segments'][0], gap['words'][0])
        division.words = base_words[gap['words'][0]:gap['words'][1]]
        division.segments = comment_segments[gap['segments'][0]:gap['segments'][1]]
        divisions.append(division)

    return divisions


def make_noise():
    wav_obj = simpleaudio.WaveObject.from_wave_file('WW_Fanfare_SmallItem.wav')
    play = wav_obj.play()
    play.wait_done()


def append_in_ja(ja: JaggedArray, index: int, content):
    try:
        ja.get_element([index]).append(content)
    except IndexError:
        ja.set_element([index], [content], pad=list())


def get_segments_from_raw(filename) -> list:
    with open(filename) as fp:
        soup = bs4.BeautifulSoup(fp, 'html5lib')
        anchor_element = soup.h2
        tags = [t for t in anchor_element.next_siblings if t.name == 'p']
        results = []
        t: bs4.Tag
        for i, t in enumerate(tags):
            bold = t.b.extract()
            if t.br:
                t.br.decompose()
            # if not bold.string or not t.string:
            #     print(str(t))
            # print(i, end=', ')
            results.append({'meta': bold.string, 'content': re.sub(r'<[^<>]+>', '', str(t))})
        return results


def get_daf_from_segment(segment):
    meta = segment['meta']
    reg = re.compile(r'\u05d3\u05e3 (?P<daf>[\u05d0-\u05ea]{1,3})\s*,\s*(?P<amud>[\u05d0\u05d1])')
    match = reg.search(meta)
    if not match:
        return
    return f'{getGematria(match.group("daf"))}{"a" if match.group("amud") == "א" else "b"}'


def get_address_from_segment(segment):
    meta = segment['meta']
    reg = re.compile(
        r'\u05e4\u05e8\u05e7\s*(?P<chp>[\u05d0-\u05ea]{1,3})\s*\u05d4\u05dc\u05db\u05d4\s*(?:\([\u05d0-\u05ea]\)\s*)?(?P<hal>[\u05d0-\u05ea]{1,3})'
    )
    match = reg.search(meta)
    if not match:
        return
    return [getGematria(match.group('chp')) - 1, getGematria(match.group('hal')) - 1]


def create_daf_ja(segment_list):
    ja, address = JaggedArray(), AddressTalmud(1)
    for segment in segment_list:
        index = address.toIndex('en', get_daf_from_segment(segment))
        try:
            ja.get_element([index]).append(segment['content'])
        except IndexError:
            ja.set_element([index], [segment['content']], pad=list())
    return ja.array()


def create_chap_ja(segment_list, filter_method=lambda x: True):
    filtered_segment_list = filter(filter_method, segment_list)
    # if talmud_only:
    #     segment_list = [s for s in segment_list if 'גמרא' in s['meta']]
    ja = JaggedArray()
    for segment in filtered_segment_list:
        content = clean_mehon_string(segment['content'])
        address = get_address_from_segment(segment)
        try:
            ja.get_element(address).append(content)
        except IndexError:
            ja.set_element(address, [content], pad=list())
    return ja.array()


def clean_mehon_string(segment: str):
    segment = segment.replace('\xa0', ' ')
    segment = ' '.join(segment.split())
    segment = re.sub(r'&[lg]t;', '', segment)
    return segment


def three_to1ja(ja):
    result = [JaggedArray(r).flatten_to_array() for r in ja]
    return result


def build_basic_mapping(tractate_name, chapter_ja, daf_ja, new_title=None):
    if not new_title:
        new_title = tractate_name

    def get_chap_address(chap_indices):
        return f'{new_title} {":".join(str(c + 1) for c in chap_indices[:2])}'

    chap_list, daf_list = [f['indices'] for f in traverse_ja(chapter_ja)], [f['indices'] for f in traverse_ja(daf_ja)]
    assert len(chap_list) == len(daf_list)
    address_class = AddressTalmud(1)
    result = {}
    last_daf = current_daf = '1a'
    start = end = tuple(chap_list[0][:2])
    for chap_segment, daf_segment in zip(chap_list, daf_list):
        current_daf = address_class.toStr('en', daf_segment[0] + 1)
        if current_daf != last_daf:
            daf_address = f'{tractate_name} {last_daf}'
            result[daf_address] = (get_chap_address(start), get_chap_address(end))
            start, last_daf = chap_segment, current_daf
        end = chap_segment
    daf_address = f'{tractate_name} {current_daf}'
    result[daf_address] = (get_chap_address(start), get_chap_address(end))

    return result


def align_chapters(commentary_segments, test_words):
    return match_text(commentary_segments, test_words)


def grab_guggenheim_chapters(tractate, talmud_only=False, mishna_only=False):
    with open('guggenheimer_titles.json') as fp:
        title_mapping = json.load(fp)
    if 'Jerusalem Talmud' not in tractate:
        tractate = f'Jerusalem Talmud {tractate}'
    guggenheimer_tractate = title_mapping[tractate]

    with open(f'code_output/csv_reports/{guggenheimer_tractate}.csv') as fp:
        if talmud_only:
            rows = [r for r in csv.DictReader(fp) if r['Type'] != 'Mishnah']
        elif mishna_only:
            rows = [r for r in csv.DictReader(fp) if r['Type'] == 'Mishnah']
        else:
            rows = list(csv.DictReader(fp))
    rows.sort(key=lambda x: [int(i) for i in re.search('(\d+:?)+$', x['Address']).group().split(':')])

    chapters = JaggedArray()
    for row in rows:
        chap_num = int(re.search(r'(\d+):', row['Address']).group(1)) - 1
        append_in_ja(chapters, chap_num, row['Text'])
    return chapters.array()


def get_mapping_gaps(mapping, num_words):
    def matched_segment(seg_indices):
        return -1 not in seg_indices
        # if -1 in seg_indices:
        #     assert all(j == -1 for j in seg_indices)
        #     return False
        # return True

    gaps = []
    start_segment, start_word = None, None
    gap_open = False
    for i, segment in enumerate(mapping):
        if gap_open:
            if matched_segment(segment):  # this means the gap has closed
                assert start_segment is not None and start_word is not None
                gap_open = False
                gaps.append({
                    'segments': (start_segment, i),
                    'words': (start_word, segment[0])
                })
                start_segment, start_word = None, None
            elif segment[1] > 0:
                assert start_segment is not None and start_word is not None
                gap_open = False
                gaps.append({
                    'segments': (start_segment, i),
                    'words': (start_word, segment[1])
                })
                start_segment, start_word = None, None
        else:
            if not matched_segment(segment):  # we need to open a new gap
                assert start_segment is None and start_word is None
                start_segment = i
                if segment[0] == -1:
                    start_word = mapping[i - 1][-1] + 1 if i > 0 else 0
                else:
                    start_word = segment[0]
                gap_open = True
    if gap_open:
        gaps.append({
            'segments': (start_segment, len(mapping)),
            'words': (start_word, num_words)
        })
    return gaps


def create_review_document(mapping_file, comment_segments, base_text_word_list, error_list) -> str:
    """
    For each segment, place words from mapping next to segment. In case of a gap, leave empty (we have map-repair for
    that).
    """
    def default(lst, indx, default_value=''):
        try:
            return lst[indx]
        except IndexError:
            return default_value

    with open(mapping_file) as fp:
        mapping = json.load(fp)['matches']

    if len(mapping) != len(comment_segments):
        print(f'segments don\'t match mapping length in {mapping_file}')

    table_rows = []
    error_set = set(error_list)
    for map_index, pair in enumerate(mapping):
        start_word, end_word = pair
        end_word += 1
        base_words = '' if -1 in pair else ' '.join(base_text_word_list[start_word:end_word])
        comment_segment = default(comment_segments, map_index)
        if map_index in error_set:
            table_rows.append(f'<tr class="error"><td>{map_index+1}</td><td>{comment_segment}</td><td>{base_words}</td></tr>')
        else:
            table_rows.append(
                f'<tr><td>{map_index+1}</td><td>{comment_segment}</td><td>{base_words}</td></tr>'
            )
    table_rows = '\n'.join(table_rows)
    return f'''
    <!DOCTYPE html>
    <html><meta charset="utf-8">
      <head>
        <style type="text/css">{create_css()}</style>
      </head>
      <body>
        <table>
          <colgroup>
            <col style="width: 5%;">
            <col style="width: 45%;">
            <col style="width: 45%;">
          </colgroup>
          <tr><th>Segment Number</th><th>Guggeenheimer</th><th>Mehon Mamre</th></tr>
          {table_rows}
        </table>
      </body>
    </html>
    '''


def output_method(trac):
    return create_tractate_mappings(trac)


def align_mishnayot(guggenheimer, mehon):
    cb = align.CompareBreaks([' '.join(guggenheimer)], mehon, markers=['φ', 'ψ'])
    with_markers = cb.insert_break_marks()[0]
    return [r for r in re.split(r'ψ\d+ψ', with_markers) if r]


def debugging_method(input_string, start_character, end_character):
    """
    use word indexes and words. print out word and characters from previous match.end() to next match.end()
    :return:
    """
    from itertools import zip_longest
    from data_utilities.util import get_word_indices
    input_string = input_string[start_character:end_character]
    indices = get_word_indices(input_string, r'\s+|$')
    words = input_string.split()
    prev_space = 0
    for i, (space_index, word) in enumerate(zip_longest(indices, words, fillvalue='exhausted')):
        try:
            chars = input_string[prev_space:space_index]
        except TypeError:
            chars = 'exhausted'
        print(i, chars, word, sep='\n', end='\n\n')
        prev_space = space_index


def get_moc_index(tractate):
    jnode = JaggedArrayNode()
    # en_title = f'JTmock {tractate}'
    # he_title = 'ירושלמי דמע ' + library.get_index(tractate).get_title('he').replace('תלמוד ירושלמי', 'ירושלמי דמע')
    en_title = tractate.replace("Jerusalem Talmud", "JTmock")
    he_title = library.get_index(tractate).get_title('he').replace('תלמוד ירושלמי', 'ירושלמי דמע')
    jnode.add_primary_titles(en_title, he_title)
    jnode.add_structure(['Chapter', 'Halakhah', 'Segment'], ['Integer', 'Halakhah', 'Integer'])
    jnode.validate()
    return {
        'title': en_title,
        'categories': ['Talmud', 'Yerushalmi', 'Mock Yerushalmi'],
        'schema': jnode.serialize()
    }


def get_moc_version(version_title, ja):
    return {
        'text': ja,
        'language': 'he',
        'versionTitle': version_title,
        'versionSource': 'foo',
    }



if __name__ == '__main__':
    # root = './code_output/mapping_files'
    # folders = os.listdir(root)
    # for folder in folders:
    #     title = re.match(r'^Jerusalem_Talmud_(.*)$', folder)
    #     if not title:
    #         print(f'{folder} did not match regex')
    #         continue
    #     title = title.group(1)
    #     full_path = os.path.join(root, folder)
    #     file_reg = re.compile(r'^chapter_(\d{1,2})_mapping\.json')
    #     files = [f for f in os.listdir(full_path) if file_reg.match(f)]
    #     files.sort(key=lambda x: int(file_reg.search(x).group(1)))
    #     for chapter_num, mapping_file in enumerate(files, 1):
    #         output_file = f'{title}_{chapter_num}_review.html'
    # zip_review_documents()
    # import sys
    # sys.exit(0)
    stuff = sefaria_objects.library.get_indexes_in_category('Yerushalmi', full_records=True).array()
    stuff = [s for s in stuff if 'JTmock' not in s.title]
    stuff.sort(key=lambda x: x.order)
    # stuff = [s for s in stuff if s.title == "Jerusalem Talmud Eruvin"]
    error_dict = {}
    # foo = [s.title == 'Jerusalem Talmud Avodah Zarah' for s in stuff].index(True)
    # create_tractate_mappings(stuff[foo], True)
    # make_noise()
    for thing in stuff:
        error_dict[thing.title] = create_tractate_mappings(thing)
        # break
    error_dict['total'] = sum(sum(c) for c in error_dict.values())
    with open('code_output/errors.json', 'w') as fp:
        json.dump(error_dict, fp)
    # with ProcessPoolExecutor(max_workers=9) as executor:
    #     executor.map(output_method, stuff)
    # slack_url = os.environ['SLACK_URL']
    # import requests
    # requests.post(slack_url, json={'text': 'Script Complete'})
    # make_noise()
    zip_review_documents()
    # berakhot = ASSEMBLER['Jerusalem Talmud Shabbat']
    error_report, mishnayot_report = [], []
    mishnayot_dict = {}
    for key, value in ASSEMBLER.items():
        mishnayot_dict[key] = [{
            'mehon-mishnayot': c['mehon-mishnayot'],
            'gugg-mishnayot':  c['gugg-mishnayot'],
        } for c in value]
    with open('./code_output/mishnayot.json', 'w') as fp:
        json.dump(mishnayot_dict, fp)
    for title, tractate in ASSEMBLER.items():
        text_ja = []
        for chap_num, chapter in enumerate(tractate, 1):
            print(title, chap_num)
            chap_ja, clean_chap, error_list = assemble_guggenheimer_chapter(
                chapter['guggenheimer'], chapter['mapping'], chapter['halakha-indices'], False, True
            )
            # if number of halakhot (length of the chapter) matches the number of mishnayot
            # place a mishna at the beginning of each halakha
            if len(chapter['gugg-mishnayot']) == len(chap_ja):
                mishnayot_report.append({
                    'Tractate': title,
                    'Chapter': chap_num,
                    'Method': 'Simple'
                })
                mishnayot = chapter['gugg-mishnayot']
            else:
                mishnayot_report.append({
                    'Tractate': title,
                    'Chapter': chap_num,
                    'Method': 'Algorithmic'
                })
                mishnayot = align_mishnayot(chapter['gugg-mishnayot'], chapter['mehon-mishnayot'])

            for i, mishna in enumerate(mishnayot):
                try:
                    chap_ja[i][0] = mishna
                except IndexError:
                    try:
                        chap_ja[i].append(mishna)
                        error_list.append('Missing Halakha')
                    except IndexError:
                        error_list.append('Missing Chapter')
                        chap_ja.append([mishna])

            text_ja.append(chap_ja)
            error_report.extend([{
                'Tractate': title,
                'Chapter': chap_num,
                "Error Message": e
            } for e in error_list])
        mehon_ja = []
        for chap_num, chapter in enumerate(tractate):
            print(chap_num+1)
            segment_sanitizer = chapter['mehon-sanitizer']
            full_chapter = ' '.join(segment_sanitizer.get_original_segments())

            segment_list = assemble_mehon_segments(full_chapter,
                                                   ' '.join(segment_sanitizer.get_sanitized_segments()),
                                                   chapter['mapping'],
                                                   lambda x: [(m, '') for m in re.finditer(SANITIZATION_REGEX, x)])

            mehon_ja.append(assemble_mehon_chapter(segment_list, text_ja[chap_num], chapter['mehon-mishnayot']))
        with open('code_output/mishnayot_report.csv', 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=['Tractate', 'Chapter', 'Method'])
            writer.writeheader()
            writer.writerows(mishnayot_report)
        # print(*list(berakhot[0].keys()), sep='\n')
        # ja_to_xml(berakhot_ja, ['Chapter', 'Halakha', 'Segment'], 'code_output/berakhot_gugg_test.xml')
        # ja_to_xml(mehon_berakhot, ['Chapter', 'Halakha', 'Segment'], 'code_output/berakhot_mehon_test.xml')
        server = 'http://localhost:8000'
        # server = 'https://jtmock.cauldron.sefaria.org'
        # add_term('Mock Yerushalmi', 'ירושלמי דמ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ע', server=server)
        # add_category('Mock Yerushalmi', ['Talmud', 'Yerushalmi', 'Mock Yerushalmi'], server=server)
        # ind = get_moc_index(title)
        # post_index(ind, server)
        # post_text(ind['title'], get_moc_version('Guggenheimer', text_ja), server=server)
        # post_text(ind['title'], get_moc_version('Mehon-Mamre', mehon_ja), server=server, index_count="on")
    with open("./code_output/general_report.csv", "w") as fp:
        writer = csv.DictWriter(fp, fieldnames=["Tractate", "Chapter", "Error Message"])
        writer.writeheader()
        writer.writerows(error_report)
    import sys
    sys.exit(0)

    for item_num, thing in enumerate(stuff, 1):
        print(f'{item_num}/{len(stuff)}')
        create_tractate_mappings(thing, True)
        break
    import sys


    sys.exit(0)
    stuff = get_segments_from_raw('mechon-mamre/שקלים.html')
    for thing in stuff:
        if not get_address_from_segment(thing):
            print(thing)
        # print(get_address_from_segment(thing))
    # print(len(stuff))

    # chaps, dafs = create_chap_ja(stuff), create_daf_ja(stuff)
    # mapping = build_basic_mapping('Jerusalem Talmud Shekalim', chaps, dafs, 'Yerushalmi Shekalim NEW')
    # chap_list, daf_list = [f['indices'] for f in traverse_ja(chaps)], [f['indices'] for f in traverse_ja(dafs)]
    # for key in mapping.keys():
    #     first, end = mapping[key]
    #     mapping[key] = Ref(first).to(Ref(end)).normal()
    # a = AddressTalmud(1)

    # print(len(chap_list), len(daf_list))
    # print(*((c, d, a.toStr('en', d[0]+1)) for c, d in zip(chap_list, daf_list)), sep='\n')
    # print(*mapping.items(), sep='\n')
    # import json
    # with open('shekalim_mapping.json', 'w') as fp:
    #     json.dump(mapping, fp)
    # ja_to_xml(r, ['chapter', 'halacha', 'segment'], 'test.xml')
    # with open('mechon-mamre/ברכות.html') as fp:
    #     soup = bs4.BeautifulSoup(fp, 'html5lib')

    # gug_chaps, mehon_ja = grab_guggenheim_chapters('Shekalim'), create_chap_ja(stuff)
    # mehon_chaps = three_to1ja(mehon_ja)
    # mehon_text = ' '.join(mehon_chaps[0])
    # mehon_text = re.sub(r'[.:]', '', mehon_text)
    # mehon_text = re.sub(r'(?<=\s)\([^()]+\)\s', '', mehon_text).split()
    # gug_text = [m.replace('־', ' ') for m in gug_chaps[0]]
    # gug_text = [strip_nikkud(m) for m in gug_text]
    # gug_text = [re.sub(r'[.:]', '', m) for m in gug_text]
    # print(*mehon_chaps[0], sep='\n\n')
    # print(gug_chaps[0][0])
    # print(mehon_chaps[0][0])
    # print(len(gug_chaps), len(mehon_chaps))
    # for chap_num in range(len(mehon_chaps)):
    #     start = time.time()
    #     mehon_text = ' '.join(mehon_chaps[chap_num])
    #     mehon_text = re.sub(r'[.:]', '', mehon_text)
    #     mehon_text = re.sub(r'(?<=\s)\([^()]+\)\s', '', mehon_text).split()
    #     gug_text = [m.replace('־', ' ') for m in gug_chaps[chap_num]]
    #     gug_text = [strip_nikkud(m) for m in gug_text]
    #     gug_text = [re.sub(r'[.:]', '', m) for m in gug_text]
    #     divide = DividedSegments(15)
    #     divide.segments = gug_text
    #     foo = match_text(mehon_text, divide.segments, place_all=True, strict_boundaries='text', place_consecutively=True, daf_skips=3, rashi_skips=3, overall=4)
    #     not_matched = sum(-1 in m for m in foo['matches'])
    #     total = len(foo['matches'])
    #     matched = total - not_matched
    #     end = time.time()
    #     print(f'chapter {chap_num+1} matched {matched}/{total} ({not_matched} unmatched segments)')
    #     print(f'chapter {chap_num+1} required {end-start} seconds to align\n\n\n')
    #     for match, pair in zip(foo['matches'], foo['match_text']):
    #         print(match, *pair, sep='\n|\n', end='\n\n\n')
    #     break
    # initialization = align.initialize_indices(mehon_text, gug_text)
    # best_indices, score = align.find_best_indices(mehon_text, gug_text, indices=initialization, verbose=True, num_iterations=100000)
    # print(type(best_indices))
    # aligned_mehon = []
    # for beginning, ending in zip([0]+best_indices[:-1], best_indices[1:] + [len(best_indices)]):
    #     aligned_mehon.append(' '.join(mehon_text[beginning:ending]))
    # print(len(gug_text), len(aligned_mehon), len(best_indices))
    # for g, m in zip_longest(gug_text, aligned_mehon, fillvalue='???'):
    #     print(g, '\n|\n', m, end='\n\n\n')
    # print(*gug_text, sep='\n\n')
    # # print(*gug_text, sep='\n|\n')
    foo = match_text(mehon_text, gug_text, place_all=True, strict_boundaries='text', place_consecutively=True,
                     daf_skips=3, rashi_skips=3, overall=2)
    print(*foo['matches'], sep='\n')
    edits, h_rows = create_map_repair(foo['matches'], gug_text, mehon_text, 'code_output/repair.csv')
    create_helper_html(h_rows, 'code_output/repair.html')
    # for match, pair in zip(foo['matches'], foo['match_text']):
    #     print(match, *pair, sep='\n|\n', end='\n\n\n')
    #
    # print('\n\n\ntrying new algorithm\n\n\n')
    # retry_with_divisions = divide_segments_from_failed_match(foo['matches'], gug_text, mehon_text, 20)
    # for rt in retry_with_divisions:
    #     print('new stuff')
    #     new_foo = match_text(rt.words, rt.segments, place_all=True, strict_boundaries='text', place_consecutively=True, daf_skips=3, rashi_skips=3, overall=2)
    #     for match, pair in zip(new_foo['matches'], new_foo['match_text']):
    #         print(match, *pair, sep='\n|\n', end='\n\n\n')
    #
    # not_matched = sum(-1 in m for m in foo['matches'])
    # total = len(foo['matches'])
    # matched = total - not_matched
    # print(f'matched {matched}/{total} ({not_matched} unmatched segments)')
    # gaps = get_mapping_gaps(foo['matches'], len(mehon_text))
    # for gap in gaps:
    #     s, e = gap['words']
    #     m_words = mehon_text[s:e]
    #     s, e = gap['segments']
    #     g_segs = gug_text[s:e]
    #     initialization = align.initialize_indices(m_words, g_segs)
    #     best_indices, score = align.find_best_indices(m_words, g_segs, indices=initialization, verbose=True)
    #     aligned_mehon = []
    #     for beginning, ending in zip([0]+best_indices[:-1], best_indices[1:] + [len(best_indices)]):
    #         aligned_mehon.append(' '.join(m_words[beginning:ending]))
    #     for g, m in zip_longest(g_segs, aligned_mehon, fillvalue='???'):
    #         print(g, '\n|\n', m, end='\n\n\n')
    # print(gaps)
    # print(*foo['match_text'], sep='\n')
    # print(clean_mehon_string(stuff[0]['content']), stuff[0]['meta'], sep='\n')
    # foo = u' '.join([str(a) for a in range(45)])
    # foo = [foo, foo, foo]
    # print(*foo, sep='\n')
    # bar = DividedSegments.divide_segments(foo, 10)
    # print(*bar['indices'])
    # print(*bar['segments'], sep='\n')
    # for i in bar['indices']:
    #     s, e = i
    #     stuff = bar['segments'][s:e]
    #     foo = []
    #     for t in stuff:
    #         foo.extend(t)
    #     print(' '.join(foo))
    # time_end = time.time()
    # elapsed = int(time_end - time_start)
    # print(f'script completed in {elapsed} seconds')
    # if elapsed > 10:
    #     make_noise()
    make_noise()
