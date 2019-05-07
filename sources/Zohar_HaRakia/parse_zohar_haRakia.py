# encoding=utf-8
from __future__ import unicode_literals, print_function

import re
import codecs
from collections import OrderedDict
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
        return doc_lines[:negative_start], doc_lines[negative_start+1:]

    def _make_initial_parse(self, commandment_type):
        def prepare_segment(string_list):
            new_segment = ' '.join(string_list)
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
        report_errors = True
        for row in raw_data:
            new_segment_match = re.match('^@22([\u05d0-\u05ea]{1,3})\)', row)

            if new_segment_match:

                if current_segment:
                    parsed_data.append(prepare_segment(current_segment))
                    current_segment = []

                if getGematria(new_segment_match.group(1)) - 1 != len(parsed_data):
                    if report_errors:
                        print("Length mismatch found at {} for {} commandments".format(new_segment_match.group(1),
                                                                                       commandment_type))
                        report_errors = False

                elif not report_errors:
                    report_errors = True

            current_segment.append(row)
        else:
            parsed_data.append(prepare_segment(current_segment))

        return parsed_data

    def get_commandment_map(self, commandment_type):
        """
        Iterate through segments.
        Collect commandment numbers.
        Map each commandment number to current line
        Make sure no duplicates show up
        Check that the numbers are in order
        :param commandment_type:
        :return:
        """
        if commandment_type == 'positive':
            segments = self.positive_segments
        elif commandment_type == 'negative':
            segments = self.negative_segments
        else:
            raise ValueError("commandment_type must be 'positive' or 'negative'")

        mapping = OrderedDict()
        for seg_num, segment in enumerate(segments, 1):
            map_match = re.search('@44\((.*)\)@55', segment)
            if not map_match:
                continue

            values = map_match.group(1).split()
            for value in values:
                value = getGematria(re.sub(u'[^\u05d0-\u05ea]', '', value))
                if value in mapping:
                    print('{} appears twice in {} commandments'.format(value, commandment_type))

                mapping[value] = seg_num

        commandment_values = mapping.keys()
        previous_value = 0
        for value in commandment_values:
            if value - previous_value != 1:
                print('{} followed by {} in {} commandments'.format(previous_value, value, commandment_type))
            previous_value = value

        return dict(mapping)

    def get_formatted_segments(self, commandment_type):
        def format_segment(segment):
            segment = re.sub('@44([^@]+)@55', '<small>\g<1></small>', segment)
            segment = re.sub('@\d{2}', '', segment)
            return segment

        if commandment_type == 'positive':
            return [format_segment(seg) for seg in self.positive_segments]
        elif commandment_type == 'negative':
            return [format_segment(seg) for seg in self.negative_segments]
        else:
            raise ValueError("commandment_type must be 'positive' or 'negative'")


a = Azharot()
p = a.get_commandment_map('positive')
n = a.get_commandment_map('negative')




