import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.system.database import db
from sefaria.model.schema import AddressTalmud
import time
from datetime import datetime, timezone
from sefaria.system.database import db
from sources.functions import post_index





def fill_vilna_to_ref_map():
    for masechet in yerusalmi_masechtot:
        talmud_addr = AddressTalmud(0)
        index = library.get_index("Jerusalem Talmud " + masechet)
        alt_struct = index.get_alt_structure("Vilna")
        amud_to_chapter_map = {}
        for chapter in alt_struct.children:
            starting_address = chapter.startingAddress
            starting_index = talmud_addr.toNumber('en', starting_address)
            for amud_offset, amud_ref in enumerate(chapter.refs):
                amud_str = talmud_addr.toStr('en', starting_index + amud_offset)
                if amud_str in amud_to_chapter_map:
                    # prev chapter and next chapter are on same amud
                    # combine refs
                    amud_ref = Ref(amud_to_chapter_map[amud_str]).to(Ref(amud_ref)).normal()
                amud_to_chapter_map[amud_str] = amud_ref
                vilna_to_ref_map["Jerusalem Talmud " + masechet + " " + amud_str] = amud_ref
                # print(masechet, amud_str, amud_ref)


if __name__ == '__main__':
    print("hello world")
    # index = library.get_index("Jerusalem Talmud Niddah")
    index = post_index({"title": "Jerusalem Talmud Niddah"}, method='GET', server='https://yerushalmi-yomi.cauldron.sefaria.org')
    vilna = index['alt_structs']['Vilna']

    new_chpater = {'nodeType': 'ArrayMapNode', 'depth': 1,
                   'wholeRef': 'Jerusalem Talmud Niddah 4:1:1-7:1', 'addressTypes': ['Talmud'], 'sectionNames': ['Daf'],
                   'refs': ['Jerusalem Talmud Niddah 4:1:1-6:1', 'Jerusalem Talmud Niddah 4:6:1-7:1'],
                   'startingAddress': '12b', 'match_templates': [],
                   'titles': [{'text': 'Chapter 4', 'lang': 'en', 'primary': True}, {'text': 'בנות כותים', 'lang': 'he', 'primary': True}]}
    vilna['nodes'].append(new_chpater)

    post_index(index, server='https://yerushalmi-yomi.cauldron.sefaria.org')

    print(vilna)










