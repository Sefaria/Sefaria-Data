#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
gra = commentaries.get_commentary_by_title("Beur HaGra")
if gra is None:
    gra = commentaries.add_commentary("Beur HaGra", u'ביאור הגר"א')

filename = u"../txt_files/Choshen_Mishpat/part_1/שוע חושן משפט חלק א באור הגר''א.txt"
gra.remove_volume(1)
# correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = gra.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@11([\u05d0-\u05ea]{1,2})')
print "Validating Simanim"
volume.validate_simanim()

errors = volume.mark_seifim(u'@66\[([\u05d0-\u05ea]{1,3})\]')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('$^', '$^', 'dh')
for i in errors:
    print i
base = root.get_base_text()
b_vol = base.get_volume(1)
assert isinstance(b_vol, Volume)
# b_vol.mark_references(volume.get_book_id(), u'@69\[([\u05d0-\u05ea]{1,3})\]', group=1)
volume.set_rid_on_seifim()
root.populate_comment_store()
errors = b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@69', x.text) is not None)
for i in errors:
    print i
# volume.locate_references(ur'\("\)')
root.export()
