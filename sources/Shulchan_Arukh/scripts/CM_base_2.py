# encoding=utf-8


from sources.Shulchan_Arukh.ShulchanArukh import *
from data_utilities.util import he_ord



root = Root('../Choshen_Mishpat.xml')
base = root.get_base_text()
filename = u'../txt_files/Choshen_Mishpat/part_2/שולחן ערוך חושן משפט חלק ב מחבר מושלם.txt'

with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = base.add_volume(infile.read(), 2)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={u'@01': {'name': u'topic'}})
print 'Validating Simanim'
volume.validate_simanim()

volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@23': {'name': u'title'}})
print 'Validating Seifim'
volume.validate_seifim()
# root.export()

codes = [u'@44', u'@55', u'@66', u'@77', u'@99', u']*]', u'-[*]', u'/*)']
patterns = [ur'@44({})', ur'@55({})', ur'@66\(({})\)', ur'@77\(({})\)', ur'@99\[({})\]', ur'\]({})\]', ur'-\[({})\]',
            ur'/({})\)']
patterns = [i.format(ur'[\u05d0-\u05ea]{1,3}') for i in patterns]

for code, pattern in zip(codes, patterns):
    if code == u'@44':
        volume.validate_references(pattern, code, key_callback=he_ord)
    else:
        volume.validate_references(pattern, code)

errors = volume.format_text('@33', '@88', 'ramah')
for i in errors:
    print i
