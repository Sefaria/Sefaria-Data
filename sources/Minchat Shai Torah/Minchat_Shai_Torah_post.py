# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *

seforim = [u"בראשית",u"שמות",u"ויקרא",u"במדבר",u"דברים"]
seforim_en = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
def get_parsed_text():
    books = []
    book_list = []
    sefer_count = -1
    line_count=-1
    current_perek=0
    current_pasuk=0
    with open('מנחת שי תורה.txt') as myfile:
        lines = myfile.readlines()
    for ascii_line in lines:
        line_count+=1
        line = ascii_line.decode('utf-8')
        if u"@99" in line and is_start_of_sefer(line):
            if len(book_list)>0:
                books.append(book_list)
            sefer_count+=1
            book_list=make_perek_array(seforim_en[sefer_count])
        elif u"@11" in line:
            current_perek = getGematria(line)
            current_pasuk=0
        elif u"@22" in line:
            current_pasuk = getGematria(line)
        else:
            try:
                book_list[current_perek-1][current_pasuk-1].append(line)
            except:
                print u"ERROR! "+str(current_perek)+" "+str(current_pasuk)+" "+seforim[sefer_count]+" "+seforim_en[sefer_count]
                print line
                print "line is "+str(line_count)
    #add last sefer
    books.append(book_list)
    return books
def is_start_of_sefer(s):
    if not isinstance(s,unicode):
        s = s.decode('utf8')
    for sefer in seforim:
        if sefer in s:
            return True
    return False

def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def get_parsha_index():
    parsha_indices = []
    index_box = []
    last_perek = 1
    last_pasuk = 1
    just_finished_parsha=True
    changed_pasuk = False
    parsha_count = -1
    with open('מנחת שי תורה.txt') as myfile:
        lines = myfile.readlines()
    for line in lines:
        if "@99" in line:
            if len(index_box)>0:
                index_box[-1].append(str(last_perek)+":"+str(last_pasuk))
                if is_start_of_sefer(line):
                    parsha_indices.append(index_box)
                    index_box = []
                    last_perek = 1
                    last_pasuk = 1
            just_finished_parsha=True
            changed_pasuk=False
            parsha_count+=1
        else:
            if "@11" in line:
                last_perek = getGematria(line)
                last_pasuk=1
            elif "@22" in line:
                last_pasuk = getGematria(line)
                changed_pasuk=True
            if just_finished_parsha and changed_pasuk:
                index_box.append([eng_parshiot[parsha_count],str(last_perek)+":"+str(last_pasuk)])
                just_finished_parsha=False
    #add last index
    index_box[-1].append(str(last_perek)+":"+str(last_pasuk))
    parsha_indices.append(index_box)
    return parsha_indices
def post_index_ms(sefer_count):
    # create index record
    ms_schema = JaggedArrayNode()
    ms_schema.add_title('Minchat Shai on '+seforim_en[sefer_count], 'en', primary=True)
    ms_schema.add_title(u"מנחת שי"+u" על "+seforim[sefer_count], 'he', primary=True)
    ms_schema.key = 'Minchat Shai on '+seforim_en[sefer_count]
    ms_schema.depth = 3
    ms_schema.addressTypes = ["Integer", "Integer", "Integer"]
    ms_schema.sectionNames = ["Perek", "Pasuk", "Comment"]
    toc_zoom = 2
    #parsha alt struct
    parsha_nodes = SchemaNode()
    for parsha_index in get_parsha_index()[sefer_count]:
        parsha_node = ArrayMapNode()
        parsha_node.add_title(parsha_index[0], "en", primary=True)
        parsha_node.add_title(heb_parshiot[eng_parshiot.index(parsha_index[0])], "he", primary=True)
        parsha_node.includeSections = False
        parsha_node.depth = 0
        parsha_node.wholeRef = "Minchat Shai on "+seforim_en[sefer_count]+", "+str(parsha_index[1])+"-"+str(parsha_index[2])
        parsha_nodes.append(parsha_node)
    ms_schema.validate()
    
    index = {
        "title": 'Minchat Shai on '+seforim_en[sefer_count],
        "alt_structs": {"Parsha": parsha_nodes.serialize()},
        "categories":['Commentary2', 'Tanakh','Minchat Shai'],
        "schema": ms_schema.serialize()
    }
    post_index(index,weak_network=True)
def post_text_ms(text_array, sefer_count):
    version = {
        'versionTitle': 'Minchat Shai',
        'versionSource': 'http://www.sefaria.org/',
        'language': 'he',
        'text': text_array
    }
    
    post_text('Minchat Shai on '+seforim_en[sefer_count], version, weak_network=True)

#post indices
for x in range(0,5):
    post_index_ms(x)
#post texts
for index, book in enumerate(get_parsed_text()[1:2]):
    post_text_ms(book,index)

