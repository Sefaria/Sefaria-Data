#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
kzot = commentaries.get_commentary_by_title("Ketzot HaChoshen")
if kzot is None:
    kzot = commentaries.add_commentary("Ketzot HaChoshen", u"קצות החושן")

filename = u"../../txt_files/Choshen_Mishpat/part_3/קצות החושן שולחן ערוך חושן משפט חלק ג.txt"
kzot.remove_volume(3)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = kzot.add_volume(infile.read(), 3)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea"]{1,3})')
print "Validating Simanim"
volume.validate_simanim(False)

errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})\)')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('@32', '@33', 'dh')
for i in errors:
    print i
base = root.get_base_text()
b_vol = base.get_volume(3)
assert isinstance(b_vol, Volume)
# b_vol.mark_references(volume.get_book_id(), u'@58([\u05d0-\u05ea]{1,3})\)')
volume.set_rid_on_seifim()
volume.unlink_seifim(["b0-c3-si350-ord2", "b0-c3-si350-ord3", "b0-c3-si350-ord4"])
print "Cross linking"
root.populate_comment_store()
errors = b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@58', x.text) is not None)
for i in errors:
    print i
root.export()
