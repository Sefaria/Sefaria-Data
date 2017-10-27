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

# check that the number of links to Ba'er Hetev at each Seif in Shulchan Arukh matches the number of references in source file
sefaria_simanim = library.get_index(u"Shulchan Arukh, Orach Chayim").all_section_refs()
assert len(simanim) == len(sefaria_simanim)

# walk through simanim
problems = 0
for sefaria_siman, xml_siman in zip(sefaria_simanim, simanim):

    # walk through seifim
    sefaria_seifim = sefaria_siman.all_subrefs()
    xml_seifim     = xml_siman.get_child()
    if len(sefaria_seifim) != len(xml_seifim):
        print "Mismatched Seifim in {}".format(sefaria_siman.normal())
        continue

    for sefaria_seif, xml_seif in zip(sefaria_seifim, xml_seifim):
        # grab references from xml seif
        total_xml_refs = len(xml_seif.grab_references(u'@66\([\u05d0-\u05ea]{1,3}\)'))
        # load LinkSet for Sefaria seif
        ls = LinkSet(sefaria_seif)
        # filter LinkSet for Ba'er Hetev
        total_baer_links = len(ls.filter("Ba'er Hetev on Shulchan Arukh, Orach Chayyim"))
        # compare number
        if total_xml_refs != total_baer_links:
            problems += 1
            print u'Problem in {}'.format(sefaria_seif.normal())
print u'{} problems found'.format(problems)
