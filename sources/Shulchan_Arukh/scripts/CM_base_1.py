# encoding=utf-8


from sources.Shulchan_Arukh.ShulchanArukh import *
from data_utilities.util import he_ord

def markup(b_vol):
    commentaries = root.get_commentaries()
    b_vol.mark_references(commentaries.commentary_ids["Siftei Cohen"], ur'@65\(([\u05d0-\u05ea]{1,3})\)', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Me'irat Einayim"], u'@62([\u05d0-\u05ea]{1,3})', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Ktsot HaHoshen"], u'@67([\u05d0-\u05ea]{1,3})\)', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Pithei Teshuva"], u'@64([\u05d0-\u05ea]{1,3})\]', group=1)
    return

root = Root('../Choshen_Mishpat.xml')
base = root.get_base_text()
filename = u'../txt_files/Choshen_Mishpat/part_1/שולחן ערוך חושן משפט חלק א מחבר.txt'

codes = [u'@69', u'@70', u'@71', u'@62', u'@63', u'@64', u'@65', u'@67']
patterns = [ur'@69\[({})\]', ur'@70\(({})\)', ur'@71({})\)', ur'@62({})', ur'@63\[({})\]', ur'@64({})\]',
            ur'@65\(({})\)', ur'@67({})\)']
patterns = [i.format(ur'[\u05d0-\u05ea]{1,3}') for i in patterns]
# for pattern in patterns:
#     correct_marks_in_file(filename, u'@22', pattern, start_mark=u'!start!')

base.remove_volume(1)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = base.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', start_mark=u'!start!', specials={u'@00': {'name': u'topic'}})
print 'Validating Simanim'
volume.validate_simanim()

bad = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@23': {'name': u'title'}})
print 'Validating Seifim'
for i in bad:
    print i
volume.validate_seifim()
# root.export()

volume.validate_references(ur'@68([\u05d0-\u05ea])', u'@68', key_callback=he_ord)
for code, pattern in zip(codes, patterns):
    volume.validate_references(pattern, code)

errors = volume.format_text('@33', '@34', 'ramah')
for i in errors:
    print i
markup(volume)
# root.populate_comment_store()
root.export()
