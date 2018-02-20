# coding=utf-8

from EH_base import move_special_section
from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'part_1': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/שולחן ערוך  פתחי תשובה אבן האזל חלק א.txt",
    'part_2': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן העזר פתחי תשובה חלק ב.txt"
}
root = Root('../../Even_HaEzer.xml')
commentaries = root.get_commentaries()
pithei = commentaries.get_commentary_by_title('Pithei Teshuva')
if pithei is None:
    pithei = commentaries.add_commentary('Pithei Teshuva', u'פתחי תשובה')

for piece in [1,2]:
    pithei.remove_volume(piece)
    with codecs.open(filenames['part_{}'.format(piece)], 'r', 'utf-8') as infile:
        volume = pithei.add_volume(infile.read(), piece)
    assert isinstance(volume, Volume)

    volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})', specials={
        u'@13': {'name': u'Halitza', 'end': u'!end!'},
        u'@14': {'name': u'Get', 'end': u'!end!'},
        u'@15': {'name': u'Names', 'end': u'!end!'}
    })
    print "Validating Simanim"
    volume.validate_simanim(complete=False)

    errors = volume.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)')
    print "Validating Seifim"
    for e in errors:
        print e
    volume.validate_seifim()

    errors = volume.format_text(u'@11', u'@33', u'dh')
    for e in errors:
        print e

    volume.set_rid_on_seifim()

root.populate_comment_store()
for piece in [1,2]:
    base = root.get_base_text()
    b_vol = base.get_volume(piece)
    assert isinstance(b_vol, Volume)
    errors = b_vol.validate_all_xrefs_matched(
        lambda x: x.name == 'xref' and re.search(ur'@66\(([\u05d0-\u05ea]{1,3})\)', x.text) is not None)
    for e in errors:
        print e

name_sec = move_special_section(pithei, u"Pithei Teshuva, Shemot Anashim V'Nashim", u'פתחי תשובה, שמות אנשים ונשים', u'Names')
name_sec.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)', enforce_order=True)
name_sec.validate_seifim()
name_sec.format_text(u'@11', u'@33', u'dh')

get_sec = move_special_section(pithei, u'Pithei Teshuva, Seder HaGet', u'פתחי תשובה, סדר הגט', u'Get')
get_sec.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)', enforce_order=True)
get_sec.validate_seifim()
get_sec.format_text(u'@11', u'@33', u'dh')
get_sec.set_rid_on_seifim(root.get_commentary_id(u"Seder HaGet"), get_sec.get_parent().get_book_id())
base_get_sec = commentaries.get_commentary_by_title(u"Seder HaGet")
base_get_vol = base_get_sec.get_volume(1)

halitza_sec = move_special_section(pithei, u'Pithei Teshuva, Seder Halitzah', u'פתחי תשובה, סדר חליצה', u'Halitza')
halitza_sec.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)', enforce_order=True)
halitza_sec.validate_seifim()
halitza_sec.format_text(u'@11', u'@33', u'dh')
halitza_sec.set_rid_on_seifim(root.get_commentary_id(u"Seder Halitzah"), halitza_sec.get_parent().get_book_id())
base_halitza = commentaries.get_commentary_by_title(u"Seder Halitzah")
base_halitza_vol = base_halitza.get_volume(1)

root.populate_comment_store()
errors = base_get_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(ur'@66\(([\u05d0-\u05ea]{1,3})\)', x.text) is not None)
errors += base_halitza_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(ur'@66\(([\u05d0-\u05ea]{1,3})\)', x.text) is not None)
for e in errors:
    print e

root.export()
