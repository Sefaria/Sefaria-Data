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

    commentaries = xml_root.get_commentaries()
    beer = commentaries.get_commentary_by_title(u"Be'er HaGolah")
    volume = beer.get_volume(vol)

    for siman in volume.get_child():
        for seif in siman.get_child():
            num_marks = len(seif.grab_references(mark_pattern))
            if num_marks > 0:
                mark_locations[(siman.num, seif.num)] = num_marks
    return mark_locations
