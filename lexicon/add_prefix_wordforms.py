# -*- coding: utf-8 -*-
import os, sys, re
import pickle
import urllib2
from urllib2 import HTTPError
from collections import namedtuple
import json
import codecs
import re
from sources.functions import post_index, post_text
from sefaria.utils.hebrew import strip_nikkud, normalize_final_letters_in_str, gematria, has_cantillation
from data_utilities.util import numToHeb
from sefaria.datatype import jagged_array
from sefaria.model import *
from sefaria.system.exceptions import BookNameError

with open('../data/dictionary-wordform-pickles/jastrow_wordforms.pickle', 'rb') as handle:
    jastrow_wordforms = pickle.load(handle)

with open('../data/dictionary-wordform-pickles/klein_wordforms.pickle', 'rb') as handle:
    klein_wordforms = pickle.load(handle)
    
with open('../data/dictionary-wordform-pickles/new_jastrow_wordforms.pickle', 'rb') as handle:
    jastrow_clean_wordforms = pickle.load(handle)

with open('../data/dictionary-wordform-pickles/new_klein_wordforms.pickle', 'rb') as handle:
    # dict of all words to their rids
    klein_clean_wordforms = pickle.load(handle)

with codecs.open('prefix_refs_talmud.txt', 'rb', 'utf-8') as fr: 
    for line in fr:
        if len(line) > 2:
            ref_txt, txt = line.split(u'~~')
            ref = Ref(ref_txt)
