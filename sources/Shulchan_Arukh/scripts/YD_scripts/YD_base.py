# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

if __name__ == "__main__":
    root_dir = loc(loc(loc(os.path.abspath(__file__))))
    xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')
    if not os.path.exists(xml_loc):
        raise IOError("xml file does not exist. Please run startup.py")

    root = Root(xml_loc)
    base = root.get_base_text()

    filenames = [
        u"txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א מחבר.txt",
        u"txt_files/Yoreh_Deah/part_2/שולחן ערוך יורה דעה חלק ב מחבר.txt",
        u"txt_files/Yoreh_Deah/part_3/שולחן ערוך יורה דעה חלק ג מחבר.txt",
        u"txt_files/Yoreh_Deah/part_4/שולחן ערוך יורה דעה חלק ד מחבר.txt",
    ]
    filenames = dict(zip(range(1, 5), [os.path.join(root_dir, f) for f in filenames]))

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
