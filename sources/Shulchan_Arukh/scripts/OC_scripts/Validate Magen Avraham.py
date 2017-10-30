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

# check that the number of links to Ba'er Hetev at each Seif in Shulchan Arukh matches the number of references in source file
sefaria_simanim = library.get_index(u"Shulchan Arukh, Orach Chayim").all_section_refs()
assert len(simanim) == len(sefaria_simanim)

# walk through simanim
problems = 0
print u"The following locations indicate a mismatch between links to Magen Avraham on Sefaria and the number of marks in the source file:\n"
for sefaria_siman, xml_siman in zip(sefaria_simanim, simanim):

    # walk through seifim
    sefaria_seifim = sefaria_siman.all_subrefs()
    xml_seifim = xml_siman.get_child()
    if len(sefaria_seifim) != len(xml_seifim):
        # print "Mismatched Seifim in {}".format(sefaria_siman.normal())
        continue

    for sefaria_seif, xml_seif in zip(sefaria_seifim, xml_seifim):
        # grab references from xml seif
        total_xml_refs = len(xml_seif.grab_references(u'@55[\u05d0-\u05ea]{1,3}'))
        # load LinkSet for Sefaria seif
        ls = LinkSet(sefaria_seif)
        # filter LinkSet for Ba'er Hetev
        total_magen_links = len(ls.filter("Magen Avraham"))
        # compare number
        if total_xml_refs != total_magen_links:
            problems += 1
            print u"Magen Avraham mismatch: {}  {} in xml; {} on site".format(sefaria_seif.normal(), total_xml_refs, total_magen_links)
print u'{} problems found'.format(problems)

