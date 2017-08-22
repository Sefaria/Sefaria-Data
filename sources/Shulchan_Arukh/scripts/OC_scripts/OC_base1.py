# encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../../Orach_Chaim.xml')
base = root.get_base_text()
filename = u'../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א.txt'

base.remove_volume(1)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = base.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={u'@00': {'name': u'topic'}})
print "Validating Simanim"
volume.validate_simanim()

bad = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@23': {'name': u'title'}})
print 'Validating Seifim'
for i in bad:
    print i
volume.validate_seifim()

codes = [ur'@44', ur'@77', ur'@88', ur'@66', ur'@55']
patterns = [ur'@44({})', ur'@77\(({})\)', ur'@88({})\]', ur'@66\(({})\)', ur'@55({})']
patterns = [i.format(ur'[\u05d0-\u05ea]{1,3}') for i in patterns]
volume.validate_references(patterns[0], codes[0], key_callback=he_ord)
for pattern, code in zip(patterns[1:], codes[1:]):
    volume.validate_references(pattern, code)


root.export()
