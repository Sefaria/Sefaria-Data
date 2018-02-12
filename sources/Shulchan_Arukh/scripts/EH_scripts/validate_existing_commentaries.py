# coding=utf-8

import regex
import requests
from fuzzywuzzy import fuzz
from sefaria.model import *
from collections import defaultdict, Counter
from sources.functions import getGematria
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


def compile_linkset(book_name, server='https://www.sefaria.org'):
    raw_set = requests.get(u'{}/api/links/Shulchan_Arukh,_Even_HaEzer?with_text=0'.format(server)).json()
    commentary_reg = re.compile(Ref(book_name).regex())
    filtered_set = [l for l in raw_set if commentary_reg.match(l['ref']) is not None]

    linkset = defaultdict(lambda: [])
    for l in filtered_set:
        linkset[Ref(l['anchorRef']).normal()].append(l)
    return linkset


def check_links_on_seifim(xml_book, commentary_name, marker_pattern, server='http://www.sefaria.org'):
    """
    Check each Seif of commentary to ensure the number of links at each seif match the number of references
    :param Record xml_book:
    :param commentary_name:
    :param marker_pattern:
    :param server
    :return:
    """
    sefaria_simanim = library.get_index(u"Shulchan Arukh, Even HaEzer").all_section_refs()
    xml_simanim = xml_book.get_simanim()
    assert len(sefaria_simanim) == len(xml_simanim)
    issues = 0

    remote_linkset = compile_linkset(commentary_name, server)

    for sefaria_siman, xml_siman in zip(sefaria_simanim, xml_simanim):
        sefaria_seifim = sefaria_siman.all_subrefs()
        xml_seifim = xml_siman.get_child()
        if len(sefaria_seifim) != len(xml_seifim):
            print u"Different number of Seifim between Sefaria and text file at {}. {} seifim on site, {} in text file"\
                .format(sefaria_siman.normal(), len(sefaria_seifim), len(xml_seifim))
            continue

        for sefaria_seif, xml_seif in zip(sefaria_seifim, xml_seifim):
            num_xml_refs = len(xml_seif.grab_references(marker_pattern))
            num_links = len(remote_linkset[sefaria_seif.normal()])

            if num_xml_refs != num_links:
                issues += 1
                print u"Mismatch at {} for commentary {}. {} in text file; {} links on site".format(
                    sefaria_seif.normal(), commentary_name, num_xml_refs, num_links
                )
    return issues


u"""
Large discrepancies were found between the existing link data and what is described in our files. It was then decided to
discard the links that were up on the site and to just go with the ones described in the files.

To account for possible bad data, it is necessary to attempt a match of the dh to the text which appears after the appropriate
mark.

Algorithm:
1) Go to siman of מחבר
2) Go to seif
3) Search for inline refs to commentary  -- a single regex should do for this
4) For each inline ref:
    determine commentary ref and retrieve text   -- requires name of commentary
    fuzzy match of dh to word/phrase after inline ref marker
"""
def search_for_matches(seif_text, basic_pattern):
    full_pattern = u'{} (?>[@!/][^ ]* )*(?P<dh>[^ ]+)'.format(basic_pattern)
    return re.finditer(full_pattern, seif_text)


def determine_match(commentary_name, commentary_regex):
    issues = 0
    full_pattern = u'{} (?>[@!/*][^ ]* )*(?P<dh>[^ ]+)'.format(commentary_regex)
    full_mechaber = Root('../../Even_HaEzer.xml').get_base_text()
    error_counter = Counter()

    for siman_num, siman in enumerate(full_mechaber.get_simanim()):
        for seif_num, seif in enumerate(siman.get_child()):
            matches = regex.finditer(full_pattern, unicode(seif))

            for regex_match in matches:
                c_ref = Ref(u'{} {}:{}'.format(commentary_name, siman_num+1, getGematria(regex_match.group('ref'))))
                try:
                    c_text = c_ref.text('he').text.split()[0]
                except IndexError:
                    continue
                c_text = re.sub(u'[^\u05d0-\u05ea]', u'', c_text)
                dh_text = re.sub(u'[^\u05d0-\u05ea]', u'',regex_match.group('dh'))

                ratio = fuzz.ratio(dh_text, c_text)

                if ratio < 75.0:
                    issues += 1
                    print u"Potential mismatch:"
                    print u"Shulchan Arukh, Even HaEzer {}:{}   {}".format(siman_num+1, seif_num+1, dh_text)
                    print u"{}   {}".format(c_ref.normal(), c_text)
                    print u"Score: {}".format(ratio)
                    error_counter[(dh_text, c_text)] += 1
    print u"Total issues: {}".format(issues)
    return error_counter


base_text = Root("../../Even_HaEzer.xml").get_base_text()
params = [
    (u'Beit Shmuel', ur'@55(?P<ref>[\u05d0-\u05ea]{1,3})'),
    (u"Ba'er Hetev on Shulchan Arukh, Even HaEzer", ur'@82(?P<ref>[\u05d0-\u05ea]{1,3})\)'),
    (u'Chelkat Mechokek', ur'@77\((?P<ref>[\u05d0-\u05ea]{1,3})\)')
]

for param_set in params[1:]:
    # counts = determine_match(*param_set)
    # for i,j in counts.most_common(7):
    #     print u'{};{}   {}'.format(i[0], i[1], j)
    # print sum([j for i,j in counts.most_common(7)])


    # thingy = compare_num_comments(base_text, *param_set)
    probs =  check_links_on_seifim(base_text, *param_set)
    print u'{} issues for {}'.format(probs, param_set[0])

