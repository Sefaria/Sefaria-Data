# -*- coding: utf-8 -*-
import codecs, re
from sefaria.model import *

def sanity_check():
    mesechtot = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Rosh Hashanah", "Yoma", "Sukkah", "Beitzah", "Taanit",
            "Moed Katan", "Yevamot", "Ketubot", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia",
                 "Bava Batra", "Sanhedrin","Makkot", "Shevuot", "Avodah Zarah", "Menachot", "Chullin"]

    for mesechta in mesechtot:
        rif_text = codecs.open('data/txt/{}.txt'.format(mesechta),'rb',encoding='utf8')
        rif_index = library.get_index("Rif {}".format(mesechta))

        num_text = len(re.split(ur'[:]',rif_text.read()))
        num_index = len(rif_index.all_segment_refs())

        print "{} Index {} Text {}".format(mesechta, num_index, num_text)

sanity_check()


