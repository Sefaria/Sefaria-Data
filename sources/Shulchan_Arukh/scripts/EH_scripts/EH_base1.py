# coding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *


if __name__ == "__main__":
    root_dir = loc(loc(loc(os.path.abspath(__file__))))
    xml_loc = os.path.join(root_dir, 'Even_HaEzer.xml')
    if not os.path.exists(xml_loc):
        raise IOError("xml file does not exist. Please run startup.py")

    root = Root(xml_loc)
    base = root.get_base_text()
    filename = os.path.join(root_dir, u'txt_files/Even_Haezer/part_1/אבן העזר חלק א מחבר.txt')
    assert os.path.exists(filename)

    base.remove_volume(1)
    with codecs.open(filename, 'r' 'utf-8') as infile:
        volume = base.add_volume(infile.read(), 1)
    assert isinstance(volume, Volume)
