# -*- coding: utf-8 -*-
import unicodecsv as csv
import urllib2
from get_section_titles import get_he_section_title_array
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def match_titles(he_sections, tur_table_csv_url):
    response = urllib2.urlopen(tur_table_csv_url)
    reader = csv.reader(response)
    tur_table = list(reader)
    
    #make corresponding list to use for fuzzywuzzy
    tur_he_title_list = []
    for row in tur_table:
        tur_he_title_list.append(row[0])
    
    tur_he_title_list.pop(0)
    
    #make array to reutrn
    he_and_en_title_list = []
    
    #match titles
    for section in he_sections:
        result = get_highest(section, tur_he_title_list)
        if result[1] >= 70:
            he_and_en_title_list.append([u"%s" % section, tur_table[tur_he_title_list.index(result[0])+1][2]])
        else:
            he_and_en_title_list.append([u"%s" % section, ""])
    
    return he_and_en_title_list;

def get_highest(term, input_list):
    score=-1
    for item in input_list:
        this_score = fuzz.ratio(term, item)
        if this_score>score:
            return_touple = [item, this_score]
            score = this_score
    return return_touple
    
def make_title(order):
    return "Likutei_Halachot_"+order+".csv";
#returns appropiate link from GitHub
def make_link(order):
    order_array=order.split(" ")
    return 'https://raw.githubusercontent.com/Sefaria/Sefaria-Data/master/sources/Tur/tur%20'+order_array[0]+'%20'+order_array[1]+'.csv';
    
he_sections = get_he_section_title_array()
orders= ["orach chaim","yoreh deah","even haezer","choshen mishpat"]
#loop through orders and create csv files
for index, order in enumerate(orders):
    myfile = open(make_title(order), 'wb')
    wr = csv.writer(myfile)
    for row in match_titles(he_sections[index], make_link(order)):
        wr.writerow(row)
    myfile.close()
""""
oc = match_titles(he_sections[0], 'https://raw.githubusercontent.com/Sefaria/Sefaria-Data/master/sources/Tur/tur%20orach%20chaim.csv')
yd = match_titles(he_sections[1], 'https://raw.githubusercontent.com/Sefaria/Sefaria-Data/master/sources/Tur/tur%20yoreh%20deah.csv')
eh = match_titles(he_sections[2], 'https://raw.githubusercontent.com/Sefaria/Sefaria-Data/master/sources/Tur/tur%20even%20haezer.csv')
cm = match_titles(he_sections[3], 'https://raw.githubusercontent.com/Sefaria/Sefaria-Data/master/sources/Tur/tur%20choshen%20mishpat.csv')
"""


"""for row in oc:
    print row"""