# -*- coding: utf-8 -*-
import cal_tools
import language_tools
from sefaria.model import *

word1 = u'וימן'
word2 = u'יאמר'
print language_tools.weighted_levenshtein(word1, word2, language_tools.weighted_levenshtein_cost)
print language_tools.get_two_letter_word(word1)

"""
test_set_name = "test_set_9_11"
text_names = ["Berakhot","Shabbat","Eruvin","Pesachim"]

for text_name in text_names:
    print text_name
    start_ref = None #Ref("{} 2a".format(text_name))
    end_ref   = None #Ref("{} 7a".format(text_name))

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
"""

language_tools.make_pos_hashtable_cal()
"""
print cal_tools.parseCalLine("7100101062246	4	)d_ c+nqp#3 V03 )dmqypn)",False)
print cal_tools.parseCalLine("7100101062234	1	d_ c+mny V02 dmmnynwN",False)
print cal_tools.parseCalLine("7100101057217	9	br) N05+byn p02 bbnyyhw",False)
print cal_tools.parseCalLine("7100201078125	4	^ ^ br)",False)
print cal_tools.parseCalLine("7100101062206	6	)d_ c+rtx V01 )drtx)",False)
print cal_tools.parseCalLine("7100201119123	11	d_ p+m(ly N01+$bh N02 dm(ly@$bt)",False)
print cal_tools.parseCalLine("7100101036121	0	w_ c+h) I+)mr V01 wh)'",False)
print cal_tools.parseCalLine("7100101043203	1	xylp)@dym) N05+l) a xylpy@dym)",False)
print cal_tools.parseCalLine("7100101044238	8	l_ p03+by N01+! ! lby@brwK",False)
"""
