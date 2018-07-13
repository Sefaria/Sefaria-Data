# -*- coding: utf-8 -*-
import re, codecs
from sefaria.model import *
from research.talmud_pos_research.language_classifier import cal_tools
from gensim.models import word2vec

def tokenize_words(str):
    str = str.replace(u"־"," ")
    str = re.sub(r"</?[^>]+>","",str) #get rid of html tags
    str = re.sub(r"\([^\(\)]+\)","",str) #get rid of refs
    str = str.replace('"',"'")
    word_list = filter(bool,re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]",str))
    return word_list


def make_training_set():
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if
                       not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

    all_of_shas = []
    for mesechta in mesechtot_names:
        dafs = [[word for seg in daf for word in tokenize_words(seg)] for daf in TextChunk(Ref(mesechta),"he").text ]
        all_of_shas += dafs

    model = word2vec.Word2Vec(all_of_shas,size=1000)
    model.save('word2vec_trained.bin')

def get_headword(word):
    similar = model.most_similar(word,topn=30)
    print word, u'-'.join([s[0] for s in similar])
    for temp_sim,_ in similar:
        try:
            head_word = headword_hashtable[temp_sim]
            return head_word
        except KeyError:
            pass
    return 'UNK'

def make_headword_hashtable():
    headword_hashtable = {}
    with open('../language_classifier/noahcaldb.txt','rb') as cal:
        for line in cal:
            line_obj = cal_tools.parseCalLine(line,True,withshinsin=False)
            headword_hashtable[line_obj['word']] = line_obj['head_word']
    return headword_hashtable

#make_training_set()
model = word2vec.Word2Vec.load('word2vec_trained.bin')
headword_hashtable = make_headword_hashtable()

r = Ref('Berakhot 20b')
text = [w for seg in TextChunk(r,'he').text for w in tokenize_words(seg)]
for w in text:
    if w not in headword_hashtable:
        try:
            print get_headword(w)
        except KeyError:
            print w, "NOT IN VOCAB"

