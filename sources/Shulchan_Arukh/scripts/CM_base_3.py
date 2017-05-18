# encoding=utf-8


from sources.Shulchan_Arukh.ShulchanArukh import *
from data_utilities.util import he_ord

def markup(b_vol):
    commentaries = root.get_commentaries()
    b_vol.mark_references(commentaries.commentary_ids["Ktsot HaHoshen"], u'@58([\u05d0-\u05ea]{1,3})\)', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Me'irat Einayim"], u'@54([\u05d0-\u05ea]{1,3})', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Siftei Cohen"], ur'@57\(([\u05d0-\u05ea]{1,3})\)', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Pithei Teshuva"], ur'@56([\u05d0-\u05ea]{1,3})\]', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Netivot HaMishpat, Hidushim"], ur'@52\(([\u05d0-\u05ea]{1,3})\)', group=1)
    b_vol.mark_references(commentaries.commentary_ids["Netivot HaMishpat, Beurim"], ur'@53([\u05d0-\u05ea]{1,3})\)',
                          group=1)
    b_vol.mark_references(commentaries.commentary_ids["Be'er HaGolah"], ur'@50([\u05d0-\u05ea])')
    b_vol.mark_references(commentaries.commentary_ids["Beur HaGra"], u'@51\[([\u05d0-\u05ea]{1,3})\]', group=1)
    return

root = Root('../Choshen_Mishpat.xml')
base = root.get_base_text()
filename = u'../txt_files/Choshen_Mishpat/part_3/שלחן ערוך חושן משפט חלק ג מחבר.txt'
codes = [u'@50', u'@57', u'@58', u'@51', u'@53', u'@52', u'@54', u'@56', u'@55']
patterns = [u'@50({})', ur'@57\(({})\)', ur'@58({})\)', ur'@51\[({})\]', ur'@53({})\)', ur'@52\(({})\)', ur'@54({})',
            ur'@56({})\]', ur'@55\[({})\]']
patterns = [i.format(ur'[\u05d0-\u05ea]{1,3}') for i in patterns]
patterns[0] = ur'@50([\u05d0-\u05ea])'
# correct_marks_in_file(filename, u'@00', patterns[0], error_finder=out_of_order_he_letters, start_mark=u'!start!')
# for pattern in patterns[1:]:
#     correct_marks_in_file(filename, u'@00', pattern, start_mark=u'!start!')

base.remove_volume(3)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = base.add_volume(infile.read(), 3)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})', start_mark=u'!start!', specials={u'@99': {'name': u'topic'}})
print 'Validating Simanim'
volume.validate_simanim()

bad = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@22': {'name': u'title'}, u'@91': {'name': u'topic'}})
print 'Validating Seifim'
for i in bad:
    print i
volume.validate_seifim()
# root.export()

volume.validate_references(ur'@50([\u05d0-\u05ea])', u'@50', key_callback=he_ord)
for code, pattern in zip(codes[1:], patterns[1:]):
    volume.validate_references(pattern, code)

errors = volume.format_text('@33', '@44', 'ramah')
for i in errors:
    print i
markup(volume)
volume.convert_pattern_to_itag("Ba'er Hetev on Shulchan Arukh, Choshen Mishpat", ur"@55\[([\u05d0-\u05ea]{1,3})\]")
root.export()
