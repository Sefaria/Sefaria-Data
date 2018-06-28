# encoding=utf-8

import re
import requests
from collections import defaultdict
from sources.Shulchan_Arukh.ShulchanArukh import *
import django
django.setup()
from sefaria.model import *


def compile_linkset(book_name, server='https://www.sefaria.org'):
    raw_set = requests.get(u'{}/api/links/Shulchan_Arukh,_Yoreh_Deah?with_text=0'.format(server)).json()
    commentary_reg = re.compile(Ref(book_name).regex())
    filtered_set = [l for l in raw_set if commentary_reg.match(l['ref']) is not None]

    linkset = defaultdict(lambda: [])
    for l in filtered_set:
        linkset[Ref(l['anchorRef']).normal()].append(l)
    return linkset


def check_links_on_seifim(xml_book, commentary_name, marker_pattern, server='https://www.sefaria.org'):
    """
    Check each Seif of commentary to ensure the number of links at each seif match the number of references
    :param Record xml_book:
    :param commentary_name:
    :param marker_pattern:
    :param server
    :return:
    """
    sefaria_simanim = library.get_index(u"Shulchan Arukh, Yoreh De'ah").all_section_refs()
    sefaria_simanim.pop(168)
    xml_simanim = xml_book.get_simanim()
    assert len(sefaria_simanim) == len(xml_simanim)
    issues = []

    remote_linkset = compile_linkset(commentary_name, server)

    for sefaria_siman, xml_siman in zip(sefaria_simanim, xml_simanim):
        sefaria_seifim = sefaria_siman.all_subrefs()
        xml_seifim = xml_siman.get_child()
        if len(sefaria_seifim) != len(xml_seifim):
            issues.append(u"Different number of Seifim between Sefaria and text file at {}. "
                          u"{} seifim on site, {} in text file"
                          .format(sefaria_siman.normal(), len(sefaria_seifim), len(xml_seifim)))
            continue

        for sefaria_seif, xml_seif in zip(sefaria_seifim, xml_seifim):
            num_xml_refs = len(xml_seif.grab_references(marker_pattern))
            num_links = len(remote_linkset[sefaria_seif.normal()])

            if num_xml_refs != num_links:
                issues.append(u"Mismatch at {} for commentary {}. {} in text file; {} links on site"
                              .format(sefaria_seif.normal(), commentary_name, num_xml_refs, num_links))
    return issues


base_text = Root(u'../../Yoreh_Deah.xml').get_base_text()
hetev_pattern = ur'@66\(([\u05d0-\u05ea]{1,3})\)'
problems = check_links_on_seifim(base_text, u"Ba'er Hetev on Shulchan Arukh, Yoreh De'ah", hetev_pattern)
with open('/home/jonathan/sefaria/error-logs/baer-hetev.txt', 'w') as fp:
    fp.write('\n\n'.join(problems))
print "found {} problems".format(len(problems))
