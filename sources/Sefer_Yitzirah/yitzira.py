# encoding=utf-8

from parsing_utilities.sanity_checks import TagTester
import codecs


def check_order(tag, section_pattern):

    assert isinstance(tag, TagTester)

    # jump to the second appearance of section_pattern, as the first is the legend
    [tag.skip_to_next_segment(section_pattern) for _ in range(2)]

    return tag.in_order_many_sections(u'00', 1)
