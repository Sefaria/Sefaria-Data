# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

commentary_list = [
    (u"Siftei Kohen", u"שפתי כהן"),
    (u"Be'er HaGolah", u"באר הגולה"),
    (u"Beur HaGra", u'ביאור הגר"א'),
    (u"Turei Zahav", u"טורי זהב")
]

commentary_list = [dict(zip(('en_title', 'he_title'), c)) for c in commentary_list]

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')

if not os.path.exists(xml_loc):
    Root.create_skeleton(xml_loc)
root = Root(xml_loc)
base = root.get_base_text()
base.add_titles("Shulchan Arukh, Yoreh Deah", u"שולחן ערוך יורה דעה")
xml_commentaries = root.get_commentaries()
for commentary in commentary_list:
    c = xml_commentaries.get_commentary_by_title(commentary['en_title'])
    if c is None:
        xml_commentaries.add_commentary(**commentary)
root.export()
