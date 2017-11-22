#encoding=utf-8
from sources.Shulchan_Arukh.ShulchanArukh import *
import sys
filename = "../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג חק יעקב מושלם.txt"
root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
commentary = commentaries.get_commentary_by_title("Chok Yaakov on Orach Chayim")
if commentary is None:
    commentary = commentaries.add_commentary("Chok Yaakov on Orach Chayim", u"חוק יעקב על אורח חיים")

base = root.get_base_text()
base.add_titles("Orach Chaim", u"אורח חיים")
errors = []
commentary.remove_volume(1)
with codecs.open(filename, 'r',
                 'utf-8') as infile:
    volume = commentary.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

errors += volume.mark_simanim(u'@00(.{1,6})')
volume.validate_simanim(complete=False)

errors += volume.mark_seifim(u'@22(\*)', cyclical=True)
volume.validate_seifim()

errors += volume.format_text(start_special='', end_special='', name="reg_text")
volume.set_rid_on_seifim(cyclical=True)



for i in range(3):
    b_vol = base.get_volume(i+1)
    assert isinstance(b_vol, Volume)
    if len(sys.argv) == 2 and sys.argv[1] == "--run":
        errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search("\*", x.text) is not None, base="Orach Chaim", commentary="Chok Yaakov on Orach Chaim", simanim_only=True)

if len(sys.argv) == 2 and sys.argv[1] == "--run":
    errors += root.populate_comment_store()

for i in errors:
    print i

root.export()
