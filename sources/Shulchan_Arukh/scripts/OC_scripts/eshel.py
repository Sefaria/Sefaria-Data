#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

filename = u"../../txt_files/Orach_Chaim/part_1/eshel_3 volumes with simanim.txt"

root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
eshel = commentaries.get_commentary_by_title("Eshel Avraham on Orach Chayim")
if eshel is None:
    eshel = commentaries.add_commentary("Eshel Avraham on Orach Chayim", u"טז על אורח חיים")

base = root.get_base_text()
base.add_titles("Orach Chaim", u"אורח חיים")

eshel.remove_volume(1)
with codecs.open(filename, 'r',
                 'utf-8') as infile:
    volume = eshel.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

errors = volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,4})')
volume.validate_simanim(complete=False)

errors += volume.mark_seifim(u'@22([\u05d0-\u05ea]{1,3})', cyclical=True)
volume.validate_seifim()

errors += volume.format_text('@11', '@33', 'dh')

for i in range(3):
    b_vol = base.get_volume(i + 1)

    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim(cyclical=True)
    print errors

    errors += root.populate_comment_store()
    eshel_mark = u"@88" if i < 2 else u"@99"
    errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(eshel_mark, x.text) is not None, base="Orach Chaim", commentary="Eshel Avraham on Orach Chaim", simanim_only=True)
    for i in errors:
        print i

root.export()




