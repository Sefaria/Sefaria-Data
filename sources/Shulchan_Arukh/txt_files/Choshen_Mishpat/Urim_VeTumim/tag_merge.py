# encoding=utf-8

import re
from bisect import bisect_left
from collections import namedtuple
from parsing_utilities.util import PlaceHolder


Tag = namedtuple('Tag', ['text', 'index'])


class HTMLMap(object):

    def __init__(self, input_string):
        self.original_input = input_string
        self.tag_map, self.stripped_string = self._build_tag_map()
        self.word_indices, self.word_list = self._build_word_mapping()

    def _build_tag_map(self):
        current_string = self.original_input
        tag_finder = re.compile(u'(?<!>)(<[^<>]+>)+')
        pattern_holder = PlaceHolder()
        tags = []

        while pattern_holder(tag_finder.search(current_string)) is not None:
            tags.append(Tag(pattern_holder.group(), pattern_holder.start()))
            current_string = current_string[:pattern_holder.start()] + current_string[pattern_holder.end():]

        return tags, current_string

    def _build_word_mapping(self):
        word_indices = [match.end() for match in re.finditer(u'[^\s]+', self.stripped_string)]
        words = self.stripped_string.split()
        assert len(word_indices) == len(words)
        return word_indices, words

    def get_word_by_number(self, index):
        try:
            return self.word_list[index]
        except IndexError:
            return self.word_list[-1]

    def get_word_index(self, index):
        word_index = bisect_left(self.word_indices, index)
        return min(word_index, len(self.word_indices)-1)

    def merge_tags(self, string_to_merge, validate=True):
        other_map = HTMLMap(string_to_merge)
        assert len(self.word_list) == len(other_map.word_list)

        # handle case where some extra characters got added to one of the strings
        index_offsets = [ours - theirs for ours, theirs in zip(self.word_indices, other_map.word_indices)]
        masked_map = [Tag(t.text, t.index + index_offsets[self.get_word_index(t.index)]) for t in other_map.tag_map]

        all_tags = sorted(self.tag_map + masked_map, key=lambda x: x.index, reverse=True)
        current_string = self.stripped_string

        for tag in all_tags:

            if validate:
                word_index = self.get_word_index(tag.index)
                if word_index == 0:
                    second_word_index = 1
                else:
                    second_word_index = word_index - 1

                assert self.get_word_by_number(word_index) == other_map.get_word_by_number(word_index)
                assert self.get_word_by_number(second_word_index) == other_map.get_word_by_number(second_word_index)

            current_string = current_string[:tag.index] + tag.text + current_string[tag.index:]

        return current_string


def merge_tags(string1, string2, validate=True):
    return HTMLMap(string1).merge_tags(string2, validate)
