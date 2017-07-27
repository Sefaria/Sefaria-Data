# encoding=utf-8

from sefaria.model import *
from sources.Shulchan_Arukh.ShulchanArukh import *


"""
Load up Ba'er Hetev on Shulchan Arukh, Choshen Mishpat
Get each section
For each section, count segments
Load appropriate Siman
Count Markers in each Siman
Compare the two

Vol 1: 1-74
Vol 2: 75-170
Vol 3: 171-427
Load all Simanim into one list
A simple method can be used to extract the correct regex with which to locate the Ba'er Hetev markders

"""

def count_markers(siman):
    """
    Count number of markers for Ba'er Hetev in a given Siman
    :param Siman siman: Siman to be examined
    :return: int
    """
    if siman.num <= 74:
        pattern = ur"@63\[([\u05d0-\u05ea]{1,3})\]"
    elif 75 <= siman.num <= 170:
        pattern = ur"-\[([\u05d0-\u05ea]{1,3})\]"
    else:
        pattern = ur"@55\[([\u05d0-\u05ea]{1,3})\]"

    return len(siman.locate_references(pattern))


def load_simanim():
    simanim = []
    base = Root("../../Choshen_Mishpat.xml").get_base_text()
    for volume in base.get_child():
        simanim.extend(volume.get_child())
    return simanim

baer_simanim = library.get_index("Ba'er Hetev on Shulchan Arukh, Choshen Mishpat").all_section_refs()
no_issues = True
for base, commentary in zip(load_simanim(), baer_simanim):
    base_refs = count_markers(base)
    comments = len(commentary.all_segment_refs())
    if base_refs == comments:
        continue
    else:
        no_issues = False
        print "Mismatch in Siman {}: {} Markers in Shulchan Arukh, but {} segments in Ba'er Hetev".format(
            base.num, base_refs, comments
        )
if no_issues:
    print "No Issues Found!"



