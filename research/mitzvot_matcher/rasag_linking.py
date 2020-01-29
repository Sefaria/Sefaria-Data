# coding=utf-8

import django
django.setup()

from sefaria.helper.link import *
from sources.functions import post_link
from sefaria.system.database import db
import regex as re


def get_links(sources):
    """

    :param sources: an array of strings, naming multiple texts or categories to include
    :return:
    """
    # Expand Categories
    categories = text.library.get_text_categories()
    expanded_sources = []
    for source in sources:
        expanded_sources += [source] if source not in categories else text.library.get_indexes_in_category(source)

    links = []
    for book in expanded_sources:
        query = { "$and": [ { "refs": {"$regex":"^Sefer Hamitzvot of Rasag.*" }}, { "refs": {"$regex":"^{}.*".format(book)}  } ] }
        ls = LinkSet(query)
        links += [l.contents() for l in ls]
        for l in links:
            l['generated_by'] = 'rsg_sfm_linking_work'
            l['type'] = "Sifrei Mitzvot"
    return links


def derive_new_rasag_halakhah_links(sources, generated_msg='rsg_sfm_linker'):
    """
    This function returns links between the rasag and the halakhah links of the sources.
    the sources param are the "middleman" rasag-sources-halakhah and this function creates the links rasag-halakhah
    :param sources: a list of texts or categories on Sefaria
    :param generated_msg: a string to put on the link for the generated_by message
    :return: links rasag-halakhah
    """
    new_links = []
    source_links = get_links(sources)
    for link in source_links:
        rsg, otherref = link['refs'] if re.search("Sefer Hamitzvot", link['refs'][0]) else [link['refs'][1], link['refs'][0]]
        ls_otherref = LinkSet(Ref(otherref)).filter('Halakhah')
        # print otherref
        c = set([l.refs[0] for l in ls_otherref] + [l.refs[1] for l in ls_otherref])
        # cluster_refs = [Ref(r) for r in c]
        # create_link_cluster(cluster_refs, 30044, "Sifrei Mitzvot",
        #                     attrs={"generated_by": "rsg_sfm_linker"}, exception_pairs=[("Tur", "Shulchan Arukh")])
        c = c.difference({otherref, rsg})
        for ref_string in list(c):
            if re.search("Sefer Hamitzvot", ref_string) or not re.search("Sefer Hamitzvot", rsg):
                continue
            link=({
                "refs":[
                    rsg,
                    ref_string
                ],
                "type": "Sifrei Mitzvot",
                "auto": True,
                "generated_by": generated_msg
            })
            # print link['refs']
            new_links.append(link)
    print(len(new_links))
    return new_links

if __name__ == "__main__":
    links = get_links(['Tanakh', 'Mishneh Torah'])
    # post_link(links)
    derived_links = derive_new_rasag_halakhah_links(['Mishneh Torah'])
    # post_link(derived_links)
