# -*- coding: utf-8 -*-
# import unicodecsv, re
from sefaria.model import *
import codecs

filepath = '/Users/kevinwolf/Documents/Sefaria/data.Sefaria/lexicon/jastrow ref titles'
with codecs.open(filepath, 'r', encoding='utf-8') as fr:
    for line in fr:
        abrv, longform = line.split('=')
        abrv = abrv.strip()
        longform = longform
        if Ref().is_ref(abrv):
            print u"{} is a ref".format(abrv)
        if Ref().is_ref(longform):
            print u"{} its a ref".format(longform)
