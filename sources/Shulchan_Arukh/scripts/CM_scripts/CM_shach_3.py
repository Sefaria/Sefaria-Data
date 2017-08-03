#encoding=utf-8
"""
!!!! Used `~` to denote html markers in base text, fix when rendering to json !!!!
"""

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
shach = commentaries.get_commentary_by_title("Siftei Kohen")
if shach is None:
    shach = commentaries.add_commentary("Siftei Kohen", u"שפתי כהן")

filename = u'../../txt_files/Choshen_Mishpat/part_3/שך חושן משפט חלק ג מוכן.txt'
shach.remove_volume(3)
# correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = shach.add_volume(infile.read(), 3)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
print "Validating Simanim"
volume.validate_simanim(False)

errors = volume.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('@11', '@33', 'dh')
for i in errors:
    print i
base = root.get_base_text()
b_vol = base.get_volume(3)
assert isinstance(b_vol, Volume)
volume.set_rid_on_seifim()
root.populate_comment_store()
b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@57', x.text) is not None)
volume.locate_references(ur'\("\)')
root.export()
