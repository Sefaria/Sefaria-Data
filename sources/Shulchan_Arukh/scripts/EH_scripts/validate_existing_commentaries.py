# coding=utf-8

from sefaria.model import *
from sources.Shulchan_Arukh.ShulchanArukh import *


def compare_num_comments(xml_book, commentary_name, marker_pattern):
    """
    Checks that the number of references to a commantaryin a given Siman matches the number of Segments within the
    equivalent Siman in the commentary. First step of validating an existing commentary against Shulchan Arukh.
    :param Record xml_book:
    :param basestring commentary_name:
    :param basestring marker_pattern: The regex pattern used to identify the markers within the given text
    :return:
    """
    base_simanim = xml_book.get_simanim()
    try:
        commentary_simanim = Ref(commentary_name).all_subrefs()
    except KeyError:
        commentary_simanim = Ref(commentary_name).default_child_ref().all_subrefs()
    assert len(base_simanim) >= len(commentary_simanim)
    no_issues = True

    for base_siman, commentary_siman in zip(base_simanim, commentary_simanim):
        refs_in_base = len(base_siman.locate_references(marker_pattern))
        num_comments = len(commentary_siman.all_subrefs())

        if refs_in_base == num_comments:
            continue
        else:
            no_issues = False
            print u"Mismatch in Siman {}: {} markers in Shulchan Arukh, but {} segments in {}".format(
                base_siman.num, refs_in_base, num_comments, commentary_name
            )
    if len(base_simanim) > len(commentary_simanim):
        for base_siman in base_simanim[len(commentary_simanim):]:
            refs_in_base = len(base_siman.locate_references(marker_pattern))
            if refs_in_base != 0:
                print "Siman {}: References found after end of commentary {}".format(
                    base_siman.num, commentary_name
                )
                no_issues = False
    return no_issues

def check_links_on_seifim(xml_book, commentary_name, marker_pattern):
    """
    Check each Seif of commentary to ensure the number of links at each seif match the number of references
    :param Record xml_book:
    :param commentary_name:
    :param marker_pattern:
    :return:
    """
    sefaria_simanim = library.get_index(u"Shulchan Arukh, Even HaEzer").all_section_refs()
    xml_simanim = xml_book.get_simanim()
    assert len(sefaria_simanim) == len(xml_simanim)
    issues = 0

    for sefaria_siman, xml_siman in zip(sefaria_simanim, xml_simanim):
        sefaria_seifim = sefaria_siman.all_subrefs()
        xml_seifim = xml_siman.get_child()
        if len(sefaria_seifim) != len(xml_seifim):
            print u"Different number of Seifim between Sefaria and text file at {}. {} seifim on site, {} in text file"\
                .format(sefaria_siman.normal(), len(sefaria_seifim), len(xml_seifim))
            continue

        for sefaria_seif, xml_seif in zip(sefaria_seifim, xml_seifim):
            num_xml_refs = len(xml_seif.grab_references(marker_pattern))
            num_links = len(LinkSet(sefaria_seif).filter(commentary_name))

            if num_xml_refs != num_links:
                issues += 1
                print u"Mismatch at {} for commentary {}. {} in text file; {} links on site".format(
                    sefaria_seif.normal(), commentary_name, num_xml_refs, num_links
                )
    return issues


base_text = Root("../../Even_HaEzer.xml").get_base_text()
params = [
    (u'Beit Shmuel', ur'@55([\u05d0-\u05ea]{1,3})'),
    (u"Ba'er Hetev on Shulchan Arukh, Even HaEzer", ur'@82([\u05d0-\u05ea]{1,3})\)'),
    (u'Chelkat Mechokek', ur'@77\(([\u05d0-\u05ea]{1,3})\)')
]

for param_set in params:
    # thingy = compare_num_comments(base_text, *param_set)
    probs =  check_links_on_seifim(base_text, *param_set)
    print u'{} issues for {}'.format(probs, param_set[0])

