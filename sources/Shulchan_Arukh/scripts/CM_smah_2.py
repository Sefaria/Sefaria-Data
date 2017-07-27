#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
smah = commentaries.get_commentary_by_title("Me'irat Einayim")
if smah is None:
    smah = commentaries.add_commentary("Me'irat Einayim", u"מאירת עיניים")

filename = u"../../txt_files/Choshen_Mishpat/part_2/שולחן ערוך חושן משפט חלק ב סמ''ע מושלם.txt"
smah.remove_volume(2)
# correct_marks_in_file(filename, u'@22([\u05d0-\u05ea]{1,3})', u'@11([\u05d0-\u05ea]{1,3})@33', overwrite=False)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = smah.add_volume(infile.read(), 2)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})')
print "Validating Simanim"
volume.validate_simanim()

errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})@33')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('$.^', '$.^', 'dh')
for i in errors:
    print i

base = root.get_base_text()
b_vol = base.get_volume(2)
assert isinstance(b_vol, Volume)
# b_vol.mark_references(volume.get_book_id(), u'@55([\u05d0-\u05ea]{1,3})', group=1)
volume.set_rid_on_seifim()
root.populate_comment_store()
errors = b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@55', x.text) is not None)
for i in errors:
    print i
# volume.locate_references(ur'\("\)')
root.export()
