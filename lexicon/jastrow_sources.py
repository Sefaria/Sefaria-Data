# -*- coding: utf-8 -*-
# import unicodecsv, re
from sefaria.model import *
import codecs


def find_insert_idx(word):
    end_insert = 0
    while (end_insert < len(word)) \
            and (not any(end_delimiter == word[end_insert]
                         for end_delimiter in [u'.', u',', u'('])):
        end_insert += 1
    return end_insert

get_titles = False
if get_titles:
    filepath = '/Users/kevinwolf/Documents/Sefaria/data.Sefaria/lexicon/jastrow ref titles'
    with codecs.open(filepath, 'r', encoding='utf-8') as fr:
        with codecs.open('./jastrow_refs.txt', 'w', 'utf-8') as fw:
            for line in fr:
                values = line.split('=')
                abrv = values[0].strip()
                idx = find_insert_idx(values[1])
                longform = values[1][:idx].strip()
                ref = ''
                if Ref().is_ref(abrv):
                    ref = Ref(abrv)
                    print u"{} is a short ref for {}".format(abrv, Ref(abrv)._normal)
                if Ref().is_ref(longform):
                    print u"{} is a long ref for {}".format(longform, Ref(longform)._normal)
                    ref = Ref(longform)
                
                if ref:
                    fw.write(u"{} = {} = {}\n".format(abrv, longform, ref._normal))
                else:
                    fw.write(u"{} = {} = \n".format(abrv, longform))

add_titles = True
if add_titles:
    filepath = './jastrow_titles_final.txt' 
    with codecs.open(filepath, 'r', encoding='utf-8') as fr:
        for line in fr:
            values = line.split('=')
            abrv = values[0].strip()
            # idx = find_insert_idx(values[1])
            longform = values[1].strip()
            if len(values) == 3:
                sefaria_ref = values[2]
                if Ref().is_ref(sefaria_ref):
                    ref_ind = Ref(sefaria_ref).index
                    if not Ref.is_ref(abrv + ' 1'):
                        ref_ind.nodes.add_title(abrv, 'en')
                        print "added " + abrv
                    if not Ref().is_ref(longform):
                        ref_ind.nodes.add_title(longform, 'en')
                        print "added " + longform
                    ref_ind.save()
                elif sefaria_ref != "\n":
                    print "not ref " + sefaria_ref
    
