# coding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'part_1': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/אבן העזר חלק א ביאור הגר''א.txt",
    'part_2': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב ביאור הגרא.txt"
}
root = Root('../../Choshen_Mishpat.xml')
commentaries = root.get_commentaries()
gra = commentaries.get_commentary_by_title("Beur HaGra")
if gra is None:
    gra = commentaries.add_commentary("Beur HaGra", u'ביאור הגר"א')

for piece in [1,2]:
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
    for i in errors:
        print i
    volume.validate_seifim()
