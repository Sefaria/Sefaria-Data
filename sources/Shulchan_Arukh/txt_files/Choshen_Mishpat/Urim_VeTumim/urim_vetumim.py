# encoding=utf-8

import os
from sources.Shulchan_Arukh.ShulchanArukh import *


def startup(datafile):
    Root.create_skeleton(datafile)
    data_root = Root(datafile)
    data_base = data_root.get_base_text()
    data_base.add_titles(u"Shulchan Arukh, Choshen Mishpat", u"שולחן ערוך חושן משפט")
    data_commentaries = data_root.get_commentaries()
    data_commentaries.add_commentary(u"Urim", u"אורים")
    data_commentaries.add_commentary(u"Turim", u"תומים")
    return data_root

