# -*- coding: utf-8 -*-
import os, sys, re
import django
django.setup()
import pickle
# import urllib2
# from urllib2 import HTTPError
# from collections import namedtuple
# import json
import codecs
import re
from sefaria.system.database import db
# import regex
# from sources.functions import post_index, post_text
# from sefaria.utils.hebrew import strip_nikkud, normalize_final_letters_in_str, gematria, has_cantillation
# from data_utilities.util import numToHeb
# from sefaria.datatype import jagged_array
from sefaria.model import *
# from sefaria.system.exceptions import BookNameError
from collections import defaultdict
# from sefaria.utils.hebrew import strip_cantillation

db.word_form.remove({"generated_by": "prefix_adder_1"})

total_words = 0
num_of_words_we_miss = 0
rewrite_pickles = True
save_wordforms = True


jastrow_clean_wordforms = set()
jastrow_clean_wordforms_to_hw = defaultdict(set)
jastrow_hw_ref_list = defaultdict(set)

klein_clean_wordforms = None
klein_clean_wordforms_to_hw = None

bdb_clean_wordforms = None
bdb_clean_wordforms_to_hw = None

jastrow_wordforms = defaultdict(list)
exact_jastrow_wordforms = defaultdict(list)
klein_wordforms = defaultdict(list)
words_in_klein_and_jastrow = defaultdict(list)
bdb_wordforms = defaultdict(list)

words_that_we_miss = defaultdict(int)
potentially_bad_prefixes = defaultdict(list)
potentially_bad_prefixes_count = defaultdict(int)

# klein = WordFormSet({"lookups.parent_lexicon": "Klein Dictionary"})
# klein_clean_wordforms = set()
# klein_clean_wordforms_to_hw = defaultdict(list)
# for entry in klein:
#     try:
#         klein_clean_wordforms.add(entry.c_form)
#         klein_clean_wordforms_to_hw[entry.c_form].append(entry.lookups[0]['headword'])
#     except AttributeError:
#         pass
# 
# with open('klein_clean_wordforms.pickle', 'wb') as handle:
#     pickle.dump(klein_clean_wordforms, handle, protocol=pickle.HIGHEST_PROTOCOL)
# 
# with open('klein_clean_wordforms_to_hw.pickle', 'wb') as handle:
#     pickle.dump(klein_clean_wordforms_to_hw, handle, protocol=pickle.HIGHEST_PROTOCOL)
#     
# jastrow = 
# jastrow_clean_wordforms = set()
# for entry in WordFormSet({"lookups.parent_lexicon": "Jastrow Dictionary"}):
#     try:
#         jastrow_clean_wordforms.add(entry.c_form)
#         jastrow_clean_wordforms_to_hw[entry.c_form].add(entry.lookups[0]['headword'])
#     except AttributeError:
#         pass
# 
# for link in LinkSet({"generated_by": "Jastrow_parser"}):
#     r = Ref(link.refs[1])
#     if r.is_talmud() and r.is_segment_level():
#         if u'דָּבָר' == re.sub(ur'(Jastrow, )(.*)( 1)', ur'\2', link.refs[0]):
#             print "found"
# #         jastrow_hw_ref_list[re.sub(ur'(Jastrow, )(.*)( 1)', ur'\2', link.refs[0])].add(link.refs[1])
# 
# with open('jastrow_clean_wordforms.pickle', 'wb') as handle:
#     pickle.dump(jastrow_clean_wordforms, handle, protocol=pickle.HIGHEST_PROTOCOL)
# 
# with open('jastrow_clean_wordforms_to_hw.pickle', 'wb') as handle:
#     pickle.dump(jastrow_clean_wordforms_to_hw, handle, protocol=pickle.HIGHEST_PROTOCOL)
# 
# with open('jastrow_hw_ref_list.pickle', 'wb') as handle:
#     pickle.dump(jastrow_hw_ref_list, handle, protocol=pickle.HIGHEST_PROTOCOL)
# 
# bdb = WordFormSet({"lookups.lexicon": "BDB Augmented Strong"})
# bdb_clean_wordforms = set()
# bdb_clean_wordforms_to_hw = defaultdict(list)
# for entry in bdb:
#     try:
#         bdb_clean_wordforms.add(entry.c_form)
#         bdb_clean_wordforms_to_hw[entry.c_form].append(entry.lookups[0]['headword'])
#     except AttributeError:
#         pass
# 
# with open('bdb_clean_wordforms.pickle', 'wb') as handle:
#     pickle.dump(bdb_clean_wordforms, handle, protocol=pickle.HIGHEST_PROTOCOL)
# 
# with open('bdb_clean_wordforms_to_hw.pickle', 'wb') as handle:
#     pickle.dump(bdb_clean_wordforms_to_hw, handle, protocol=pickle.HIGHEST_PROTOCOL)
print "done with pickles"

with open('bdb_clean_wordforms.pickle', 'rb') as handle:
    bdb_clean_wordforms = pickle.load(handle)

with open('bdb_clean_wordforms_to_hw.pickle', 'rb') as handle:
    bdb_clean_wordforms_to_hw = pickle.load(handle)
    
with open('klein_clean_wordforms.pickle', 'rb') as handle:
    klein_clean_wordforms = pickle.load(handle)
    
with open('klein_clean_wordforms_to_hw.pickle', 'rb') as handle:
    klein_clean_wordforms_to_hw = pickle.load(handle)

with open('jastrow_clean_wordforms.pickle', 'rb') as handle:
    jastrow_clean_wordforms = pickle.load(handle)

with open('jastrow_clean_wordforms_to_hw.pickle', 'rb') as handle:
    jastrow_clean_wordforms_to_hw = pickle.load(handle)
    
with open('jastrow_hw_ref_list.pickle', 'rb') as handle:
    jastrow_hw_ref_list = pickle.load(handle)

    
percentage_that_are_ambiguous = 0
avg_num_results = 0

a = u'דָּבָר'
b = u'דבר'

old_jastrow_wordforms = None
old_klein_wordforms = None
old_words_in_klein_and_jastrow = None
old_bdb_wordforms = None
old_words_that_we_miss = None
# with open('jastrow_wordforms.pickle', 'rb') as handle:
#     old_jastrow_wordforms = pickle.load(handle)
# with open('klein_wordforms.pickle', 'rb') as handle:
#     old_klein_wordforms = pickle.load(handle) 
# with open('words_in_klein_and_jastrow.pickle', 'rb') as handle:
#     old_words_in_klein_and_jastrow = pickle.load(handle)
# with open('bdb_wordforms.pickle', 'rb') as handle:
#     old_bdb_wordforms = pickle.load(handle)
# with open('words_that_we_miss.pickle', 'rb') as handle:
#     old_words_that_we_miss = pickle.load(handle)
# 
# for key, value in sorted(old_words_that_we_miss.iteritems(), key=lambda (k,v): (v,k), reverse=True):
#     print "%s: %s" % (key, value)

# def find_and_add_hw(ref, word, prefix=u'', found=False):
#     in_jastrow = False
#     if word in jastrow_clean_wordforms:       
#         jastrow_wordforms[prefix+word].append(ref)
#         in_jastrow = True
#     if word in klein_clean_wordforms:
#         klein_wordforms[prefix+word].append(ref)
#         if in_jastrow:
#             words_in_klein_and_jastrow[prefix+word].append(ref)
#     # elif word in bdb_clean_wordforms:
#     #     bdb_wordforms[prefix+word].append(ref)
#     elif not (found or in_jastrow):
#         words_that_we_miss[word] += 1
#         num_of_words_we_miss += 1
     
        
# def get_inline_ref(link_ref):
#     link_title = link_ref.index.get_title("he")
#     link_node = library.get_schema_node(link_title, "he")
#     title_nodes = {t: link_node for t in link_ref.index.all_titles("he")}
#     all_reg = library.get_multi_title_regex_string(set(link_ref.index.all_titles("he")), "he")
#     reg = regex.compile(all_reg, regex.VERBOSE)
#     # not strictly necessary to strip all html and cantillation
#     source_text = re.sub(ur"<[^>]+>", u"", strip_cantillation(source_tc.text, strip_vowels=True))
#     
#     linkified = library._wrap_all_refs_in_string(title_nodes, reg, source_text, "he")

def basic_word_form(form, hw, refs, parent_lexicon, generated_by="prefix_adder_1"):
    word_form_obj = WordForm({
        'lookups': [{"headword": hw, "parent_lexicon": parent_lexicon}],
        "generated_by": generated_by,
        "form": form,
        "c_form": form,
        "refs": refs
         })
    if save_wordforms:
        word_form_obj.save()
    
try:    
    with codecs.open('prefix_refs_talmud.txt', 'rb', 'utf-8') as fr: 
        done = False
        for line in fr:
            # if num_of_words_we_miss > 2000:
            #     break
            if len(line) > 2:
                ref_txt, txt = line.split(u'~~')
                # re.sub(ur'[\']', ur'׳', txt)
                clean_txt = re.sub(ur'[-\[\](){}<>A-Za-z:./,]', u'', txt)
                ref = Ref(ref_txt)
                biblical_links = LinkSet(ref).filter("Tanakh")
                pasuk_match = dict()
                bdb_words_found = defaultdict(list)
                
                has_pasukim = False              
                for link in biblical_links:
                    has_pasukim = True
                    biblical_ref = Ref(link.refs[1])
                    text_chunk = TextChunk(biblical_ref, lang='he', vtitle='Tanach with Text Only').text
                    
                    if isinstance(text_chunk, unicode):
                        pasuk_match[str(biblical_ref)] = set(re.split(ur'[-־\s]', text_chunk))
                    
                    # could be a few segments
                    elif not biblical_ref.is_section_level():
                        biblical_ref = biblical_ref.starting_ref()
                        for t in text_chunk:
                            pasuk_match[str(biblical_ref)] = set(re.split(ur'[-־\s]', t))
                            biblical_ref = biblical_ref.next_segment_ref()
                
                for word in set(re.split(ur'[-־\s]', clean_txt)):
                    if len(word) > 0:
                        total_words += 1
                        prefix = u''
                        found_in_bdb = False
                        
                        if u'┉' in word:
                            prefix, word = word.split(u'┉')
                        
                        if has_pasukim:
                            for biblical_ref, pasuk in pasuk_match.iteritems():
                                
                                if (prefix+word) in pasuk:
                                    bdb_words_found[(prefix+word, biblical_ref)].append(ref.normal())
                                    found_in_bdb = True
                                
                                # elif word in pasuk:
                                #     # print(u"word '{}' without prefix in pasuk {} {} from seg {}".format(prefix+word, biblical_ref, pasuk, clean_txt))
                                #     bdb_words_found[(word, biblical_ref)].append(ref.normal())
                                #     found_in_bdb = True
                        
                        in_jastrow = False
                        if word in jastrow_clean_wordforms:
                            in_jastrow = True
                            found_exact = False
                            for hw in jastrow_clean_wordforms_to_hw[word]:
                                if ref.normal() in jastrow_hw_ref_list[hw]:
                                    exact_jastrow_wordforms[(prefix+word, hw)].append(ref.normal())
                                    found_exact = True
                                    # print u"exact match for {} {} {}".format(prefix+word, hw, ref)

                            # TODO: how should this be saved
                            if not found_exact:
                                jastrow_wordforms[(prefix+word, word)].append(ref.normal())
                        
                        if word in klein_clean_wordforms:
                            klein_wordforms[(prefix+word, word)].append(ref.normal())
                            # if in_jastrow:
                            #     words_in_klein_and_jastrow[prefix+word].append(ref)
                                
                        elif not in_jastrow:
                            if ((prefix+word) in jastrow_clean_wordforms) or ((prefix+word) in klein_clean_wordforms):
                                potentially_bad_prefixes[(prefix+word, word)].append(ref.normal())
                            # print u"only with prefix word is found {} {}".format((prefix+word), ref)
                        
                            if word in bdb_clean_wordforms:
                                bdb_words_found[(prefix+word, word)].append(ref.normal())
                            
                            elif not found_in_bdb:
                                words_that_we_miss[word] += 1
                                num_of_words_we_miss += 1
                
                #TODO: possibly play with number of words found
                if len(bdb_words_found) > 1:
                    for pair, refs in bdb_words_found.iteritems():
                        bdb_wordforms[pair] = refs
                else:
                    for pair, refs in bdb_words_found.iteritems():
                        words_that_we_miss[pair[1]] += 1
                        num_of_words_we_miss += 1
except Exception as e:
    print(e)

num_of_ambig_in_jastrow = 0
for c_form_word, refs in jastrow_wordforms.iteritems():
    hws = set(jastrow_clean_wordforms_to_hw[c_form_word[1]])
    if len(hws) > 1:
        num_of_ambig_in_jastrow += 1
    elif len(hws) < 1:
        print hw
    avg_num_results += len(hws) * len(refs)
    for hw in hws:
        basic_word_form(c_form_word[0], hw, refs, "Jastrow Dictionary")
        
for c_form_hw, refs in exact_jastrow_wordforms.iteritems():
    avg_num_results += len(refs)
    basic_word_form(c_form_hw[0], c_form_hw[1], refs, "Jastrow Dictionary", generated_by="jastrow_jackpot")    

num_of_ambig_in_klein = 0
for c_form_word, refs in klein_wordforms.iteritems():
    hws = set(klein_clean_wordforms_to_hw[c_form_word[1]])
    if len(hws) > 1:
        num_of_ambig_in_klein += 1
    elif len(hws) < 1:
        print hw
    avg_num_results += len(hws) * len(refs)
    
    for hw in hws:
        basic_word_form(c_form_word[0], hw, refs, "Klein Dictionary")

for c_form_word, refs in bdb_wordforms.iteritems():
    if re.search(ur'[a-zA-Z]', c_form_word[1]):
        wfs = WordFormSet({'refs': c_form_word[1], 'c_form': c_form_word[0]})
        avg_num_results += len(wfs) * len(refs)
        if len(wfs) > 1:
            for wf in wfs:
                basic_word_form(c_form_word[0], wf.lookups[0]['headword'], refs, "BDB Augmented Strong", generated_by="matching_bdb_pasuk")
            # print u"more than one wf for {} {}".format(c_form_word[1], c_form_word[0])
        elif len(wfs) < 1:
            pass
            # print u"no wf for {} {} from {}".format(c_form_word[1], c_form_word[0], refs)
            
        else:
            basic_word_form(c_form_word[0], wfs[0].lookups[0]['headword'], refs, "BDB Augmented Strong", generated_by="matching_bdb_pasuk")
    else:    
        hws = set(bdb_clean_wordforms_to_hw[c_form_word[1]])
        avg_num_results += len(hws) * len(refs)
        if len(hws) < 1:
            print c_form_word[0], hw, refs
        for hw in hws:
            basic_word_form(c_form_word[0], hw, refs, "BDB Augmented Strong", generated_by="only_bdb_match")
        
print(avg_num_results)
print(len(potentially_bad_prefixes))

print "total words: {}".format(total_words)
print "number of words we missed: {}".format(num_of_words_we_miss)
print "percent of words we catch: {}".format(1-(num_of_words_we_miss/float(total_words)))
print "average number of results per word: {}".format(avg_num_results/float(total_words-num_of_words_we_miss-len(potentially_bad_prefixes)))
print "percent of ambig results in jastrow: {}".format(num_of_ambig_in_jastrow/float(len(jastrow_wordforms)))
print "percent of ambig results in klein: {}".format(num_of_ambig_in_klein/float(len(klein_wordforms)))

if rewrite_pickles:
    with open('jastrow_wordforms.pickle', 'wb') as handle:
        pickle.dump(jastrow_wordforms, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('klein_wordforms.pickle', 'wb') as handle:
        pickle.dump(klein_wordforms, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('words_in_klein_and_jastrow.pickle', 'wb') as handle:
        pickle.dump(words_in_klein_and_jastrow, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('bdb_wordforms.pickle', 'wb') as handle:
        pickle.dump(bdb_wordforms, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('words_that_we_miss.pickle', 'wb') as handle:
        pickle.dump(words_that_we_miss, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('potentially_bad_prefixes.pickle', 'wb') as handle:
        pickle.dump(potentially_bad_prefixes, handle, protocol=pickle.HIGHEST_PROTOCOL)
# for bib_obj, refs in bdb_wordforms:
#     word_form = WordForm.load({"c_form": bib_obj[0], "refs": re.compile("^" + bib_obj + "$")})
#     refs = list(set(refs))

#TODO: possibly fix א then no headword
