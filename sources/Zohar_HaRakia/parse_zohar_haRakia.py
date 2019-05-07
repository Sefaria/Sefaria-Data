# encoding=utf-8
from __future__ import unicode_literals, print_function

import re
import codecs
from data_utilities.util import getGematria


def find_line_with_pattern(pattern, lines):
    for line_index, line in enumerate(lines):
        if re.search(pattern, line):
            return line_index
    else:
        return -1


class Azharot(object):
    """
    tags: @00 - start of negative commandments
          @22 - new line
          @44 / @55 - commandment counter
          Ignore the rest

    Split into positive and negative commandments.
    We can use a ParsedDocument for the initial parse. That might not be necessary, as a depth 1 text is easy to iterate
    as is.
    So just iterate and add things as strings to a single list.
    We'll have two methods - one for formatting, another for identifying the commandment numbers. Each method will
    operate on our initial parse.
    """

    def __init__(self):
        self.positive_data, self.negative_data = self._load_data()
        
        self.positive_segments = self._make_initial_parse('positive')
        self.negative_segments = self._make_initial_parse('negative')

    @staticmethod
    def _load_data():
        with codecs.open('Azharot.txt', 'r', 'utf-8') as fp:
            doc_lines = fp.readlines()

        negative_start = find_line_with_pattern(u'^@00', doc_lines)
        return doc_lines[:negative_start], doc_lines[negative_start:]

    def _make_initial_parse(self, commandment_type):
        def prepare_segment(string_list):
            new_segment = ''.join(string_list)
            new_segment = re.sub('^@22([\u05d0-\u05ea]{1,3})\)', '', new_segment)
            new_segment = ' '.join(new_segment.split())
            return new_segment

        if commandment_type == 'positive':
            raw_data = self.positive_data
        elif commandment_type == 'negative':
            raw_data = self.negative_data
        else:
            raise ValueError("commandment_type must be 'positive' or 'negative'")

        current_segment, parsed_data = [], []
        for row in raw_data:
            new_segment_match = re.match('^@22([\u05d0-\u05ea]{1,3})\)', row)

            if new_segment_match:
                if getGematria(new_segment_match.group(1)) - 1 != len(parsed_data):
                    print("Length mismatch found at {} for {} commandments".format(new_segment_match.group(1),
                                                                                   commandment_type))
                if current_segment:
                    parsed_data.append(prepare_segment(current_segment))
                    current_segment = []
        else:
            parsed_data.append(prepare_segment(current_segment))

        return parsed_data


