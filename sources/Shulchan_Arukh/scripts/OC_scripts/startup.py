# coding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

commentary_list = [
    ("Turei Zahav", u"טורי זהב"),
    ("Eshel Avraham", u"אשל אברהם"),
    ("Be'er HaGolah", u"באר הגולה"),
    ("Ateret Zekenim", u"עטרת זקנים"),
    ("Chok Yaakov", u"חק יעקב"),
    ("Sha'arei Teshuvah", u"שערי תשובה")

]
commentary_list = [dict(zip(('en_title', 'he_title'), c)) for c in commentary_list]

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Orach_Chaim.xml')

if not os.path.exists(xml_loc):
    Root.create_skeleton(xml_loc)
root = Root(xml_loc)
base = root.get_base_text()
base.add_titles("Shulchan Arukh, Orach Chayim", u"שולחן ערוך אורח חיים")
xml_commentaries = root.get_commentaries()
for commentary in commentary_list:
    c = xml_commentaries.get_commentary_by_title(commentary['en_title'])
    if c is None:
        xml_commentaries.add_commentary(**commentary)
root.export()
