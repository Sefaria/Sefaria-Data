# coding=utf-8

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
        u'@14': {'name': u'Get', 'end': u'!end!'}
    })
    print "Validating Simanim"
    volume.validate_simanim(complete=False)

    errors = volume.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)')
    print "Validating Seifim"
    for e in errors:
        print e
    volume.validate_seifim()
