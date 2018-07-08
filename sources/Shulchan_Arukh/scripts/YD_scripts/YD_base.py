# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *


def markup(vol, xml_root):
    """
    Mark up ref markers in Shulchan Arukh to itag or xref as needed.
    :param Volume vol:
    :param Root xml_root:
    :return:
    """
    commentaries = xml_root.get_commentaries()
    vol.mark_references(commentaries.commentary_ids[u"Siftei Kohen"], u'@55([\u05d0-\u05ea]{1,3})', group=1)
    vol.mark_references(commentaries.commentary_ids[u"Be'er HaGolah"], u'@44([\u05d0-\u05ea]{1,3})', group=1)
    vol.convert_pattern_to_itag(u"Ba'er Hetev", ur"@66\(([\u05d0-\u05ea]{1,3})\)")
    vol.convert_pattern_to_label_itag(u"Be'er HaGolah", u'@44\(([\u05d0-\u05ea]{1,3})\)\((°)\)')


root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')

filenames = [
    u"txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א מחבר.txt",
    u"txt_files/Yoreh_Deah/part_2/שולחן ערוך יורה דעה חלק ב מחבר.txt",
    u"txt_files/Yoreh_Deah/part_3/שולחן ערוך יורה דעה חלק ג מחבר.txt",
    u"txt_files/Yoreh_Deah/part_4/שולחן ערוך יורה דעה חלק ד מחבר.txt",
]
filenames = dict(zip(range(1, 5), [os.path.join(root_dir, f) for f in filenames]))

codes = [
    u'@55 -Shach',
    u"@66 -Ba'er Hetev",
    u'@71 -Turei Zahav',
    u'@74 -Pithei Teshuva',
    u'@99 -Gra',
    u"@44 -Be'er HaGolah",
    u"%   -Torat HaShlamim"
]
patterns = [
    ur'@55{}',
    ur'@66\({}\)',
    ur'@71\({}\)',
    ur'@74\({}\)',
    ur'@99\[{}\]',
    ur'@44{}',
    ur'%\[{}\]'
]
patterns = [pattern.format(ur'([\u05d0-\u05ea]{1,3})') for pattern in patterns]

if __name__ == "__main__":

    if not os.path.exists(xml_loc):
        raise IOError("xml file does not exist. Please run startup.py")

    root = Root(xml_loc)
    base = root.get_base_text()

    for vol_num in range(1, 5):
        print u"Working on vol. {}".format(vol_num)
        filename = filenames[vol_num]
        assert os.path.exists(filename)

        base.remove_volume(vol_num)
        with codecs.open(filename, 'r', 'utf-8') as infile:
            volume = base.add_volume(infile.read(), vol_num)
        assert isinstance(volume, Volume)
        volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={
            u'@00': {'name': u'topic'}
        })
        print "Validating Simanim"
        volume.validate_simanim()

        errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={
            u'@23': {'name': u'title'},
            u'@01': {'name': u'topic'}
        })
        print "Validating Seifim"
        for e in errors:
            print e
        volume.validate_seifim()

        errors = volume.format_text(u'@33', u'@88', u'ramah')
        for e in errors:
            print e
        for pattern, code in zip(patterns, codes):
            volume.validate_references(pattern, code)
        markup(volume, root)

    root.export()
