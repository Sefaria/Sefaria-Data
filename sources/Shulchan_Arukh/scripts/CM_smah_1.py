#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
smah = commentaries.get_commentary_by_title("Me'irat Einayim")
if smah is None:
    smah = commentaries.add_commentary("Me'irat Einayim", u"מאירת עיניים")

filename = u'../txt_files/Choshen_Mishpat/part_1/סמע חושן משפט חלק א מוכן.txt'
smah.remove_volume(1)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = smah.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,2})')
print "Validating Simanim"
volume.validate_simanim()

errors = volume.mark_seifim(u'@22([\u05d0-\u05ea]{1,3})')
print "Validating Seifim"
for i in errors:
    print i
volume.validate_seifim()

errors = volume.format_text('@11', '@33', 'dh')
for i in errors:
    print i
