# coding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

commentary_list = [
    ("Be'er HaGolah", u'באר הגולה'),
    ("Be'er HaGolah, Seder HaGet", u"באר הגולה, סדר הגט"),
    ("Be'er HaGolah, Seder Halitzah", u"באר הגולה, סדר חליצה"),
    ("Beur HaGra", u'ביאור הגר"א'),
    ("Beur HaGra, Seder HaGet", u'ביאור הגר"א, סדר הגט'),
    ("Beur HaGra, Seder Halitzah", u'ביאור הגר"א, סדר חליצה'),
    ("Pithei Teshuva", u"פתחי תשובה"),
    ("Pithei Teshuva, Seder HaGet", u"פתחי תשובה, סדר הגט"),
    ("Pithei Teshuva, Seder Halitzah", u"פתחי תשובה, סדר חליצה"),
    ("Pithei Teshuva, Shemot Anashim V'Nashim", u"פתחי תשובה, שמות אנשים ונשים"),
    ("Turei Zahav", u"טורי זהב"),
    ("Turei Zahav, Seder HaGet", u"טורי זהב, סדר הגט"),
    ("Turei Zahav", "Shemot Anashim V'Nashim", u"טורי זהב, שמות אנשים ונשים"),
]
commentary_list = [dict(zip(('en_title', 'he_title'), c)) for c in commentary_list]

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Even_HaEzer.xml')

if not os.path.exists(xml_loc):
    Root.create_skeleton(xml_loc)
root = Root(xml_loc)
base = root.get_base_text()
base.add_titles("Shulchan Arukh, Even HaEzer", u"שולחן ערוך אבן העזר")
xml_commentaries = root.get_commentaries()
for commentary in commentary_list:
    c = xml_commentaries.get_commentary_by_title(commentary['en_title'])
    if c is None:
        xml_commentaries.add_commentary(**commentary)
root.export()
