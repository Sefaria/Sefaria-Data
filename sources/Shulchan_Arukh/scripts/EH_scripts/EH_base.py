# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

"""
Marks:

start_ramah        @33
end_ramah          @88

Beur HaGra         !.)
Taz                @91[.]
Be'er HaGolah      @44.
Pithei Teshuva     @66(.)

Marks to existing commentaries:
Beit Shmuel        @55.
Chelkat Mechokek   @77(.)
Ba'er Hetev        @82.)
"""

def move_special_section(book, en_title, he_title, special_name=None):
    """
    :param Record book:
    :param en_title:
    :param he_title:
    :param special_name:
    :return: Siman
    """
    if not special_name:
        special_name = en_title
    if isinstance(book, BaseText):
        all_commentaries = book.get_parent().get_commentaries()
    else:
        all_commentaries = book.get_parent()

    special_book = all_commentaries.get_commentary_by_title(en_title)
    if special_book is None:
        special_book = all_commentaries.add_commentary(en_title, he_title)
    special_book.remove_volume(1)

    special_element = root.get_base_text().Tag.find(special_name).extract()
    special_element.name = u'siman'
    special_element['num'] = 1

    special_vol = BeautifulSoup('', 'xml').new_tag('volume')
    special_vol['num'] = 1
    special_vol.append(special_element)
    special_book.Tag.append(special_vol)

    return Siman(special_element)

if __name__ == "__main__":
    root_dir = loc(loc(loc(os.path.abspath(__file__))))
    xml_loc = os.path.join(root_dir, 'Even_HaEzer.xml')
    if not os.path.exists(xml_loc):
        raise IOError("xml file does not exist. Please run startup.py")

    root = Root(xml_loc)
    base = root.get_base_text()
    filenames = {
        1: os.path.join(root_dir, u'txt_files/Even_Haezer/part_1/אבן העזר חלק א מחבר.txt'),
        2: os.path.join(root_dir, u'txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב מחבר.txt')
    }
    codes = [u'!.) -Gra', u'@91[.] -Taz', u'@66(.) -Pithei Teshuva', u'@55 -Beit Shmuel',
             u'@77(.) -Chelkat Mechokek', u'@82.) -Ba\'er Hetev']
    patterns = [ur'!{}', ur'@91\[{}\]', ur'@66\({}\)', ur'@55{}', ur'@77\({}\)', ur'@82{}\)']
    patterns = [pattern.format(ur'([\u05d0-\u05ea]{1,3})') for pattern in patterns]

    for i in [1,2]:
        filename = filenames[i]
        assert os.path.exists(filename)

        base.remove_volume(i)
        with codecs.open(filename, 'r', 'utf-8') as infile:
            volume = base.add_volume(infile.read(), i)
        assert isinstance(volume, Volume)

        volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={
            u'@00': {'name': u'topic'},
            u'@13': {'name': u'Halitza', 'end': u'!end!'},
            u'@14': {'name': u'Get', 'end': u'!end!'}
        })
        print "Validating Simanim"
        volume.validate_simanim()

        errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@12': {'name': u'title'}})
        print "Validating Seifim"
        for e in errors:
            print e
        volume.validate_seifim()

        errors = volume.format_text('@33', '@88', 'ramah')
        for e in errors:
            print e

        volume.validate_references(ur'@44([\u05d0-\u05ea])', u'@44 -Be\'er HaGolah', key_callback=he_ord)
        for pattern, code in zip(patterns, codes):
            volume.validate_references(pattern, code)

    # correct_marks_in_file(filenames[2], u'@22', ur'@44([\u05d0-\u05ea])', overwrite=False, error_finder=out_of_order_he_letters)

    # To handle the special "Get" and "Halitza" sections, just treat them as independant works.
    print u"Validating Seder HaGet"
    get_sec = move_special_section(base, 'Seder HaGet', u'סדר הגט', u'Get')
    get_sec.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', enforce_order=True)
    get_sec.validate_seifim()
    get_sec.format_text('@33', '@88', 'ramah')
    get_sec.validate_references(ur'@44([\u05d0-\u05ea])', u'@44 -Be\'er HaGolah', key_callback=he_ord)
    for pattern, code in zip(patterns, codes):
        get_sec.validate_references(pattern, code)

    print u"Validating Seder Halitzah"
    halitza_sec = move_special_section(base, 'Seder Halitzah', u'סדר חליצה', u'Halitza')
    halitza_sec.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', enforce_order=True)
    halitza_sec.validate_seifim()
    halitza_sec.format_text('@33', '@88', 'ramah')
    halitza_sec.validate_references(ur'@44([\u05d0-\u05ea])', u'@44 -Be\'er HaGolah', key_callback=he_ord)
    for pattern, code in zip(patterns, codes):
        halitza_sec.validate_references(pattern, code)

    root.export()
