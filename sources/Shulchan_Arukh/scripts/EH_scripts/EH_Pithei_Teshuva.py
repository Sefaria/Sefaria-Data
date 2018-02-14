# coding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'part_1': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/שולחן ערוך  פתחי תשובה אבן האזל חלק א.txt",
    'part_2': u"/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן העזר פתחי תשובה חלק ב.txt"
}
root = Root('../../Even_HaEzer.xml')
commentaries = root.get_commentaries()
pithei = commentaries.get_commentary_by_title('Pithei Teshuva', u'פתחי תשובה')
if pithei is None:
    pithei = commentaries.add_commentary('Pithei Teshuva', u'פתחי תשובה')
