# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from sources.Scripts.replaceCollecTitlesWithSharedTitles import *

SERVER = "http://localhost:8000"
VERSION_TITLE = "Validation Tester, Jerusalem 2019"
VERSION_SOURCE = "http://nmrapoport.org"

#heb_parshiot = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
#u"ויגש", u"ויחי"]

#eng_parshiot = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
#"Vayeshev", "Miketz", "Vayigash", "Vayechi"]

heb_parshiot = ["רפפורט"]
eng_parshiot = ["Rapoport"]

def post_index_to_server(en, he):
    root = SchemaNode()
    comm_en = "Noah on {}".format(en)
    comm_he = "נח על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.key = "Noah on Rapoport"

    for parsha in eng_parshiot:
        parsha_node = JaggedArrayNode()
        parsha_node.add_title(parsha, 'en', primary = True)
        parsha_node.add_title(heb_parshiot[eng_parshiot.index(parsha)], 'he',  primary = True)
        parsha_node.key = parsha
        parsha_node.depth = 2
        parsha_node.addressTypes = ['Integer', 'Integer']
        parsha_node.sectionNames = ['Comment','Paragraph']
        root.append(parsha_node)

    root.validate()
    index = {
        "dependence": "Commentary",
        "title": comm_en,
        "default_struct": "Chapters",
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary", "Rapoport"]
    }
    post_index(index, server=SERVER)


def post_text_to_server(text, en):
    send_text = {
        "text": text,
        "versionTitle": VERSION_TITLE,
        "versionSource": VERSION_SOURCE,
        "language": "en"
    }
    post_text("Noah on {}".format(en), send_text, server=SERVER)


if __name__ == "__main__":
    # add_term("Rapoport", u"רפפורט")

    # add_category("Rapoport", ["Tanakh", "Commentary", "Rapoport"], u"רפפורט")
    #
    # post_index_to_server("Rapoport", u"רפפורט")
    # post_text_to_server("Noah Rapoport", "Rapoport")

    i = library.get_index("Noah on Rapoport")
    try:
        i.collective_title
    except AttributeError:
        print("The test index does not currently have a collective title.")

    makeCollectiveTitleShared([i])

    assert i.collective_title
    print("The test index now has a collective title: {}.".format(i.collective_title))
