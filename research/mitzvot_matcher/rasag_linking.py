# coding=utf-8

import django
django.setup()

from sefaria.model import *
from sefaria.helper.link import *
from sources.functions import post_link
from sefaria.system.database import db


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
    return links

def derive_halakhah_links():
    new_links = []
    tanakh_links = get_links(['Tanakh'])
    for link in tanakh_links:
        rsg, pasuk = link['refs']
        ls_pasuk = LinkSet(Ref(pasuk)).filter('Halakhah')
        print pasuk
        c = set([l.refs[0] for l in ls_pasuk] + [l.refs[1] for l in ls_pasuk])
        cluster_refs = [Ref(r) for r in c]
        create_link_cluster(cluster_refs, 30044, "Sifrei Mitzvot",
                            attrs={"generated_by": "rsg_sfm_linker"}, exception_pairs=[("Tur", "Shulchan Arukh")])
        link=({
            "refs":[
                "",
                ""
            ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by":"rsg_sfm_linker"
        })
        # break
    return

if __name__ == "__main__":
    derive_halakhah_links()
    # links = get_links()
    # post_link(links)
