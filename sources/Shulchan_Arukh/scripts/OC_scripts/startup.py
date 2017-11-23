# coding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

commentary_list = [
    ("Taz on Orach Chayim", u"טז על אורח חיים"),
    ("Eshel Avraham on Orach Chayim", u"אשל אברהם על אורח חיים"),
    ("Be'er HaGolah", u"באר הגולה"),
    ("Ateret Zekenim on Orach Chayim", u"עטרת אברהם על אורח חיים")

]
commentary_list = [dict(zip(('en_title', 'he_title'), c)) for c in commentary_list]

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Orach_Chaim.xml')

if not os.path.exists(xml_loc):
    Root.create_skeleton(xml_loc)
root = Root(xml_loc)
xml_commentaries = root.get_commentaries()
for commentary in commentary_list:
    c = xml_commentaries.get_commentary_by_title(commentary['en_title'])
    if c is None:
        xml_commentaries.add_commentary(**commentary)
root.export()
