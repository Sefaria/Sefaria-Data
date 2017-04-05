# encoding=utf-8


from sources.Shulchan_Arukh.ShulchanArukh import *
from data_utilities.util import he_ord

def markup(b_vol):
    commentaries = root.get_commentaries()
    b_vol.mark_references(commentaries.commentary_ids["Me'irat Einayim"], u'@55([\u05d0-\u05ea]{1,3})', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Ktsot HaHoshen"], u'/([\u05d0-\u05ea]{1,3})\)', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Pithei Teshuva"], u'\]([\u05d0-\u05ea]{1,3})\]', group=1)

root = Root('../Choshen_Mishpat.xml')
base = root.get_base_text()
filename = u'../txt_files/Choshen_Mishpat/part_2/שולחן ערוך חושן משפט חלק ב מחבר מושלם.txt'

codes = [u'@44', u'@55', u'@66', u'@77', u'@99', u']*]', u'-[*]', u'/*)']
patterns = [ur'@44({})', ur'@55({})', ur'@66\(({})\)', ur'@77\(({})\)', ur'@99\[({})\]', ur'\]({})\]', ur'-\[({})\]',
            ur'/({})\)']
patterns = [i.format(ur'[\u05d0-\u05ea]{1,3}') for i in patterns]
patterns[0] = ur'@44([\u05d0-\u05ea])'

# correct_marks_in_file(filename, u'@22', patterns[0], error_finder=out_of_order_he_letters)
# for pattern in patterns[1:]:
#     correct_marks_in_file(filename, u'@22', pattern)
base.remove_volume(2)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = base.add_volume(infile.read(), 2)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={u'@01': {'name': u'topic'}})
print 'Validating Simanim'
volume.validate_simanim()

bad = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@23': {'name': u'title'}})
print 'Validating Seifim'
for i in bad:
    print i
volume.validate_seifim()
# root.export()



for code, pattern in zip(codes, patterns):
    if code == u'@44':
        volume.validate_references(pattern, code, key_callback=he_ord)
    else:
        volume.validate_references(pattern, code)

errors = volume.format_text('@33', '@88', 'ramah')
for i in errors:
    print i
markup(volume)
root.export()
