# encoding=utf-8

"""
@66(<letter>) is used consistently throughout all three volumes
"""

from sefaria.model import *
from sources.Shulchan_Arukh.ShulchanArukh import *

base_text = Root("../../Orach_Chaim.xml").get_base_text()
simanim = base_text.get_simanim()

baer_simanim = Ref("Ba'er Hetev on Shulchan Arukh, Orach Chayyim").all_subrefs()
no_issues = True

for base, commentary in zip(simanim, baer_simanim):
    refs_in_base = len(base.locate_references(u'@66\([\u05d0-\u05ea]{1,3}\)'))
    num_comments = len(commentary.all_segment_refs())

    if refs_in_base == num_comments:
        continue
    else:
        no_issues = False
        print "Mismatch in Siman {}: {} markers in Shulchan Arukh, but {} segments in Ba'er Hetev".format(
            base.num, refs_in_base, num_comments
        )
if no_issues:
    print "No Issues Found!"
