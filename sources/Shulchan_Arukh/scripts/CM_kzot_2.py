#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
kzot = commentaries.get_commentary_by_title("Ktsot HaHoshen")
if kzot is None:
    kzot = commentaries.add_commentary("Ktsot HaHoshen", u"קצות החושן")

filename = u"../txt_files/Choshen_Mishpat/part_2/שולחן ערוך חושן משפט חלק ב קצות החושן.txt"
kzot.remove_volume(2)
# correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = kzot.add_volume(infile.read(), 2)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea"]{1,3})')
print "Validating Simanim"
volume.validate_simanim()

errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})\)@33')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('@11', '@33', 'dh')
for i in errors:
    print i
base = root.get_base_text()
b_vol = base.get_volume(2)
assert isinstance(b_vol, Volume)
# b_vol.mark_references(volume.get_book_id(), u'/([\u05d0-\u05ea]{1,3})\)', group=1)
volume.set_rid_on_seifim()
volume.unlink_seifim(["b0-c3-si82-ord10", "b0-c3-si82-ord11", "b0-c3-si82-ord12", "b0-c3-si82-ord13",
                      "b0-c3-si82-ord14", "b0-c3-si82-ord15", "b0-c3-si82-ord16", "b0-c3-si82-ord17",
                      "b0-c3-si155-ord12", "b0-c3-si155-ord13", "b0-c3-si155-ord14"])
root.populate_comment_store()
errors = b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'/([\u05d0-\u05ea]{1,3})\)', x.text) is not None)
for i in errors:
    print i
root.export()
