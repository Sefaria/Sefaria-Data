# -*- coding: utf-8 -*-

import language_tools
from sefaria.model import *

word1 = u'וימן'
word2 = u'יאמר'
print language_tools.weighted_levenshtein(word1, word2, language_tools.weighted_levenshtein_cost)
print language_tools.get_two_letter_word(word1)


test_set_name = "test_set_5_daf"
text_name = "Shabbat"
start_ref = None #Ref("{} 2a".format(text_name))
end_ref   = None #Ref("{} 5a".format(text_name))

#test_discrete()
#make_training_sets("talmudic")
#language_tools.make_cal_db_word_list(text_name)
print "done making training"
ref_list = language_tools.get_ref_list(text_name,start_ref,end_ref)
word_list_in,test_set_lens,bib_links = language_tools.get_test_set(text_name,ref_list,strip_html=False,get_bib_links=True)
language_tools.tag_testing_naive(text_name,bib_links,test_set_lens,word_list_in,ref_list,test_set_name)
#tag_testing_init(word_list_in,test_set_lens,test_set_name=test_set_name)
#get_hmm_initial_state(test_set_name=test_set_name)
#run_baum_welch(test_set_name=test_set_name)
#print_tagged_corpus(test_set_name=test_set_name)
print "yo"
language_tools.print_tagged_corpus_to_html_table(text_name,ref_list,10,test_set_name,"naive")
