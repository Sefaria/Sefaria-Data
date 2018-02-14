# encoding=utf-8

"""
objective: identify links that need to be moved
moved = delete and re-add

Walk through the inline-references
For each reference, establish what comment it belongs to
We know which Seif it was found - that establishes Vilna Seif.
Load the Shulchan Arukh link for comment. If it doesn't match the Vilna Seif - correct.
If it doesn't exist - add
"""

import requests
from sefaria.model import *
from sources.functions import getGematria
from sources.functions import post_link
from sources.Shulchan_Arukh.ShulchanArukh import *
def check_links(seif, pattern, commentary):
    """

    :param Seif seif:
    :param pattern:
    :param commentary
    :return:
    """
    add, remove = [], []
    siman = seif.get_parent().num
    reflinks = seif.grab_references(pattern)
    for l in reflinks:
        comment_num = getGematria(l.group(1))
        comment_ref = Ref(u'{} {}:{}'.format(commentary, siman, comment_num))
        comment_links = LinkSet(comment_ref).filter(u"Shulchan Arukh, Orach Chayim")

        if len(comment_links) == 1:
            prod_seif = comment_links[0].ref_opposite(comment_ref)
            if prod_seif.sections[-1] != seif.num:
                remove.append(comment_links[0])
                add.append((u'Shulchan Arukh, Orach Chayim {}:{}'.format(siman, seif.num), comment_ref.normal()))
        elif len(comment_links) == 0:
            add.append((u'Shulchan Arukh, Orach Chayim {}:{}'.format(siman, seif.num), comment_ref.normal()))
        else:
            raise AssertionError("{} has {} comments".format(comment_ref.normal(), len(comment_links)))
    return {'add': add, 'remove': remove}

server = 'http://localhost:8000'
root = Root('../../Orach_Chaim.xml')
to_add, to_remove = [], []
base_text = root.get_base_text()
simanim = base_text.get_simanim()
for siiman in simanim:
    print siiman.num,
    if siiman.num % 10 == 0:
        print u'\n'
    seifim = siiman.get_child()
    for seiif in seifim:
        result = check_links(seiif, u'@55([\u05d0-\u05ea]{1,3})', u"Magen Avraham")
        to_add.extend(result['add'])
        to_remove.extend(result['remove'])

for i in to_remove:
    r = requests.delete('{}/api/links/{}'.format(server, i._id))
    print r.text

to_add = [{
    'refs': i,
    'type': 'commentary',
    'auto': True,
    'generated_by': 'Vilna Link Fixer'
} for i in to_add]
r = post_link(to_add, server=server)
