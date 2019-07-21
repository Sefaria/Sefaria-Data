# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *

def addAliyotOnkelos(index_name):
    index = library.get_index(index_name)
    sefer_name = index_name.split()[1]
    sefer = library.get_index(sefer_name)
    index.set_alt_structure("Parasha", sefer.get_alt_structure("Parasha").copy())
    setRefs(index)
    index.save()

def setRefs(index):
    parshiyot = index.get_alt_structure("Parasha").children
    for parasha in parshiyot:
        whole_ref = parasha.wholeRef.replace(u"\u2013", u"-")
        new_whole_ref = "Onkelos {}".format(whole_ref)
        parasha.wholeRef = new_whole_ref

        for aliyah in parasha.refs:
            aliyah2 = aliyah.replace(u"\u2013", u"-")
            new_aliyah = "Onkelos {}".format(aliyah2)
            parasha.refs[parasha.refs.index(aliyah)] = new_aliyah

onkelos = ["Onkelos Genesis", "Onkelos Exodus", "Onkelos Leviticus", "Onkelos Numbers", "Onkelos Deuteronomy"]

for index_name in onkelos:
    addAliyotOnkelos(index_name)