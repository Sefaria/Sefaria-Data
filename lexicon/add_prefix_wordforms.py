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

jastrow_clean_wordforms = None
klein_clean_wordforms = None

# lookups_dict = {
#                   "headword": self._current_entry['headword'],
#                   "parent_lexicon": lexicon_name
#                 }
#         
#         word_form_obj = WordForm({
#             'lookups': [lookups_dict],
#             "generated_by": generated_by,
#         })
#         # maybe add rid "rid": self._current_entry['rid']
#         if 'language_code' in self._current_entry:
#             setattr(word_form_obj,'language_code', self._current_entry['language_code'])
#         if refs:
#             setattr(word_form_obj, 'refs', refs)

with open('dict/Jastrow/data/jastrow_clean_wordforms.pickle', 'rb') as handle:
    jastrow_clean_wordforms = pickle.load(handle)

with open('dict/Klein/pickles/clean_wordforms.pickle', 'rb') as handle:
    # dict of all words to their rids
    klein_clean_wordforms = pickle.load(handle)

with codecs.open('prefix_refs_talmud.txt', 'rb', 'utf-8') as fr: 
    for line in fr:
        if len(line) > 2:
            ref_txt, txt = line.split(u'~~')
            ref = Ref(ref_txt)
            if u'┉' in txt:
                for word in txt:
                    if u'┉' in txt:
                        prefix, hw = word.split(u'┉')
                        
                        
                # for 
