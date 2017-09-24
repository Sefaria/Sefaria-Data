# encoding=utf-8

"""
@55 is used consistently as the mark in all three volumes
"""

from sefaria.model import *
from sources.Shulchan_Arukh.ShulchanArukh import *

base_text = Root("../../Orach_Chaim.xml").get_base_text()
simanim = base_text.get_simanim()

magen_simanim = Ref("Magen Avraham").all_subrefs()
no_issues = True

for base, commentary in zip(simanim, magen_simanim):
    refs_in_base = len(base.locate_references(u'@55[\u05d0-\u05ea]{1,3}'))
    num_comments = len(commentary.all_segment_refs())

    if refs_in_base == num_comments:
        continue
    else:
        no_issues = False
        print "Mismatch in Siman {}: {} markers in Shulchan Arukh, but {} segments in Magen Avraham".format(
            base.num, refs_in_base, num_comments
        )

if no_issues:
    print "No issues found!"
