# encoding=utf-8

"""
Goal: Compare "special" marks in Mechaber to special marks in Be'er Hetev. Once a "special" mark is identified in
Mechaber, leave a mark so it can be converted into an <i> tag.

For Be'er HaGolah, use xml data. Walk through all seifim and search for the mark. Data can be saved in a dict, with keys
(<siman>, <seif>) : <num-marks>

For Mechaber, use a StructuredDocument. Each siman should be split by Be'er Hagolah markers. We then list all Be'er
HaGolah markers. A "special" mark found in segment i would then correspond to Be'er Mark i-1.
* Note -> This breakup of the siman will create 1 more segment than markers. The extra segment will be text that appears
before the first mark. A mark here can be attached to the first Be'er comment.
"""
import os
import re
from os.path import dirname as loc
from data_utilities.util import StructuredDocument
from collections import defaultdict
from sources.Shulchan_Arukh.ShulchanArukh import *
from data_utilities.util import numToHeb, getGematria


root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')


def marks_in_beer(xml_root, mark_pattern, vol, mark_locations=None):
    """
    :param Root xml_root:
    :param mark_pattern:
    :param vol:
    :param mark_locations:
    :return: dict
    """
    if mark_locations is None:
        mark_locations = defaultdict(lambda: 0)
    assert isinstance(mark_locations, defaultdict)
    mark_pattern = re.escape(mark_pattern)

    commentaries = xml_root.get_commentaries()
    beer = commentaries.get_commentary_by_title(u"Be'er HaGolah")
    volume = beer.get_volume(vol)

    for siman in volume.get_child():
        for seif in siman.get_child():
            num_marks = len(seif.grab_references(mark_pattern))
            if num_marks > 0:
                mark_locations[(siman.num, seif.num)] = num_marks
    return mark_locations


def marks_to_beer_in_base(filename, mark_pattern, siman_mark=u'@22([\u05d0-\u05ea]{1,3})', mark_locations=None):
    if mark_locations is None:
        mark_locations = defaultdict(lambda: 0)
    assert isinstance(mark_locations, defaultdict)
    mark_pattern = re.escape(mark_pattern)

    document = StructuredDocument(filename, siman_mark)
    beer_pattern = re.compile(u'@44[\u05d0-\u05ea]{1,3}')
    for siman_num in document.get_chapter_values():
        siman = document.get_section(siman_num)
        beer_segments = beer_pattern.findall(siman)
        beer_segments = [1] + [getGematria(re.match(u'@44([\u05d0-\u05ea]{1,3})', b).group(1)) for b in beer_segments]
        siman_fragments = beer_pattern.split(siman)
        assert len(beer_segments) == len(siman_fragments)

        for beer_segment, fragment in zip(beer_segments, siman_fragments):
            num_marks = len(re.findall(mark_pattern, fragment))
            if num_marks > 0:
                mark_locations[(siman_num, beer_segment)] = num_marks

    return mark_locations


filenames = [
    u"txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א מחבר.txt",
    u"txt_files/Yoreh_Deah/part_2/שולחן ערוך יורה דעה חלק ב מחבר.txt",
    u"txt_files/Yoreh_Deah/part_3/שולחן ערוך יורה דעה חלק ג מחבר.txt",
    u"txt_files/Yoreh_Deah/part_4/שולחן ערוך יורה דעה חלק ד מחבר.txt",
]
filenames = dict(zip(range(1, 5), [os.path.join(root_dir, f) for f in filenames]))

root = Root(xml_loc)
for vol_num in range(1, 5):
    print u"Checking vol {}".format(vol_num)
    my_file = filenames[vol_num]
    beer_marks = marks_in_beer(root, u'(°)', vol_num)
    base_marks = marks_to_beer_in_base(my_file, u'(#)')
    all_locations = list(set(beer_marks.keys() + base_marks.keys()))
    for location in sorted(all_locations):
        if beer_marks[location] != base_marks[location]:
            print u'Problem at Siman {} Seif {}'.format(*location)
