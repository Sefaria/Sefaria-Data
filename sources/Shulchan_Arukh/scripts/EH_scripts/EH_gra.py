# coding=utf-8

from EH_base import move_special_section
from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'part_1': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/אבן העזר חלק א ביאור הגר''א.txt",
    'part_2': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב ביאור הגרא.txt"
}
root = Root('../../Even_HaEzer.xml')
commentaries = root.get_commentaries()
gra = commentaries.get_commentary_by_title("Beur HaGra")
if gra is None:
    gra = commentaries.add_commentary("Beur HaGra", u'ביאור הגר"א')

for piece in [1,2]:
    # correct_marks_in_file(filenames['part_{}'.format(piece)], u'@22([\u05d0-\u05ea]{1,3})',
    #                       u'@11([\u05d0-\u05ea]{1,3})\)', overwrite=False)
    gra.remove_volume(piece)
    with codecs.open(filenames['part_{}'.format(piece)], 'r', 'utf-8') as infile:
        volume = gra.add_volume(infile.read(), piece)
    assert isinstance(volume, Volume)

    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={
        u'@13': {'name': u'Halitza', 'end': u'!end!'},
        u'@14': {'name': u'Get', 'end': u'!end!'}
    })
    print "Validating Simanim"
    volume.validate_simanim()

    errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})\)')
    print "Validating Seifim"
    for e in errors:
        print e
    volume.validate_seifim()

    if piece == 1:
        errors = volume.format_text(u'@77', u'@33', u'dh')
    else:
        errors = volume.format_text(u'@44', u'@33', u'dh')
    for e in errors:
        print e

    base = root.get_base_text()
    b_vol = base.get_volume(piece)
    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim()
    root.populate_comment_store(verbose=False)
    errors = b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'!([\u05d0-\u05ea]{1,3})\)', x.text) is not None)
    for e in errors:
        print e
root.export()
