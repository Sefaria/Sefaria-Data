#encoding=utf-8
from sources.Shulchan_Arukh.ShulchanArukh import *
import sys
filename = "../../txt_files/Orach_Chaim/part_3/hok_yaakov.txt"
root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
commentary = commentaries.get_commentary_by_title("Chok Yaakov")
if commentary is None:
    commentary = commentaries.add_commentary("Chok Yaakov", u"חק יעקב")

base = root.get_base_text()
errors = []
commentary.remove_volume(3)
with codecs.open(filename, 'r',
                 'utf-8') as infile:
    volume = commentary.add_volume(infile.read(), 3)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00(.{1,8})')
volume.validate_simanim(complete=False)

errors += volume.mark_seifim(u'@22(.{1,8})')
volume.validate_seifim()

errors += volume.format_text('@11|@44', '@33|@55', 'dh')

volume.set_rid_on_seifim()



if len(sys.argv) == 2 and sys.argv[1] == "--run":
    b_vol = base.get_volume(3)
    assert isinstance(b_vol, Volume)
    errors += root.populate_comment_store()
    chok_pattern = u"@14(\[[\u05d0-\u05ea]{1,2}\])"
    errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(chok_pattern, x.text) is not None, base="Orach Chaim", commentary="Chok Yaakov", simanim_only=True)

for i in errors:
    print i

root.export()
