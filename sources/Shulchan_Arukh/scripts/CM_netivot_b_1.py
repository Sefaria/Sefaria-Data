#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
netivot = commentaries.get_commentary_by_title("Netivot HaMishpat, Beurim")
if netivot is None:
    netivot = commentaries.add_commentary("Netivot HaMishpat, Beurim", u"נתיבות המשפט, ביאורים")

filename = u"../txt_files/Choshen_Mishpat/part_1/נתיבות המשפט ביאורים חושן משפט חלק א.txt"
netivot.remove_volume(1)
# correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = netivot.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
print "Validating Simanim"
volume.validate_simanim(complete=False)

errors = volume.mark_seifim(u'@22([\u05d0-\u05ea]{1,3})\)')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('@11', '@33', 'dh')
for i in errors:
    print i
base = root.get_base_text()
b_vol = base.get_volume(1)
assert isinstance(b_vol, Volume)
volume.set_rid_on_seifim()
root.populate_comment_store()
errors = b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@71', x.text) is not None)
for i in errors:
    print i
# root.export()
