# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, u'Yoreh_Deah.xml')

filename = os.path.join(root_dir, u"txt_files/Yoreh_Deah/part_3/תורת השלמים שולחן ערוך יורה דעה חלק ג.txt")

root = Root(xml_loc)
commentaries = root.get_commentaries()
torat = commentaries.get_commentary_by_title(u"Torat HaShalmim")
assert isinstance(torat, Commentary)
torat.remove_volume(3)
with codecs.open(filename, 'r', 'utf-8') as fp:
    volume = torat.add_volume(fp.read(), 3)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
volume.validate_simanim()
print "Validating Seifim"
errors = volume.mark_seifim(u'@22\[([\u05d0-\u05ea]{1,3})\]')
for e in errors:
    print e
volume.validate_seifim()
errors = volume.format_text(u'@11', u'@33', u'dh')
for e in errors:
    print e

volume.set_rid_on_seifim()
base = root.get_base_text()
b_vol = base.get_volume(3)
assert isinstance(b_vol, Volume)
root.populate_comment_store(verbose=True)
errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'%', x.text) is not None)
for e in errors:
    print e
root.export()
