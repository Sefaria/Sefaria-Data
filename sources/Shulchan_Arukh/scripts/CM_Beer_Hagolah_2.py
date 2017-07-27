# encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

root = Root('../../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()

b_hagolah = commentaries.get_commentary_by_title("Be'er HaGolah")
filename = u'../../txt_files/Choshen_Mishpat/part_2/שולחן ערוך חושן משפט חלק ב באר הגולה.txt'
b_hagolah.remove_volume(2)
with codecs.open(filename, 'r', 'utf-8') as infile:
    volume = b_hagolah.add_volume(infile.read(), 2)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@12([\u05d0-\u05ea]{1,3})')
print "Validating Simanim"
volume.validate_simanim()

volume.mark_seifim(u'@11([\u05d0-\u05ea\u2022])', cyclical=True)
# volume.validate_seifim(verbose=True, cyclical=True)

base_text = root.get_base_text()
b_volume = base_text.get_volume(2)
for base_siman, com_siman in zip(b_volume.get_child(), volume.get_child()):
    assert base_siman.num == com_siman.num
    total_footnotes = len(re.findall(u'@44', unicode(base_siman)))
    comments = len(com_siman.get_child())
    if total_footnotes != comments:
        print "mismatch in siman {}. {} footnotes and {} comments".format(base_siman.num, total_footnotes, comments)

volume.format_text('$^', '$^', 'dh')
volume.set_rid_on_seifim(cyclical=True)
root.populate_comment_store()
errors = b_volume.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@44', x.text) is not None)
for i in errors:
    print i
root.export()
