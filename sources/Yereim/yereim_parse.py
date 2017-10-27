# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import codecs



def post_y_index():
    # create index record
    record = SchemaNode()
    record.add_title('Sefer Yereim', 'en', primary=True, )
    record.add_title(u'ספר יראים', 'he', primary=True, )
    record.key = 'Sefer Yereim'
    
    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Author's Introduction", 'en', primary = True)
    intro_node.add_title("הקדמת המחבר", 'he', primary = True)
    intro_node.key = "Author's Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    
    #now we add Mitzvah struct:
    mitzvah_struct = JaggedArrayNode()
    mitzvah_struct.key = "default"
    mitzvah_struct.default = True
    mitzvah_struct.depth = 2
    mitzvah_struct.addressTypes = ['Integer','Integer']
    mitzvah_struct.sectionNames = ['Mitzvah','Paragraph']
    record.append(mitzvah_struct)
    
    amud_titles=[{"English Title":"Laws governing forbidden relationships","Hebrew Title":u"עריות"},\
    {"English Title":"Laws governing forbidden foods","Hebrew Title":u"אכילות"},\
    {"English Title":"Laws where deriving benefit is prohibited","Hebrew Title":u"איסורי הנאה"},\
    {"English Title":"Monetary laws","Hebrew Title":u"איסורי ממון"},\
    {"English Title":"Liabilities toward Heaven and toward mankind","Hebrew Title":u"איסורים שאדם עושה רע לשמים ולבריות"},\
    {"English Title":"Liabilities toward Heaven, but not toward mankind","Hebrew Title":u"איסורים הנעשים ואדם נעשה רע לשמים ולא לבריות"},\
    {"English Title":"Liabilities toward Heaven, unrelated to speech","Hebrew Title":u"איסורים שאינו נעשה רע לבריות כי אם לשמים ואינם תלוים בדבור"}]
    #now we make alt structs
    amud_nodes =SchemaNode()
    for amud_index, (amud, amud_range) in enumerate(zip(amud_titles,get_amud_index())):
        amud_node = ArrayMapNode()
        amud_node.add_title(amud["English Title"], "en", primary=True)
        amud_node.add_title(amud["Hebrew Title"], "he", primary=True)
        #amud_node.includeSections = True
        amud_node.depth = 1
        amud_node.addressTypes = ['Integer']
        amud_node.sectionNames=["Vav"]
        amud_node.wholeRef = "Sefer Yereim, "+str(amud_range["Starting Index"][0]+1)+":"+str(amud_range["Starting Index"][1]+1)\
            +"-"+str(amud_range["Ending Index"][0]+1)+":"+str(amud_range["Ending Index"][1]+1)
        subref_list=[]
        for vav in amud_range["Vavim"]:
            subref_list.append("Sefer Yereim, "+str(vav["Start Vav"][0]+1)+":"+str(vav["Start Vav"][1]+1)\
            +"-"+str(vav["End Vav"][0]+1)+":"+str(vav["End Vav"][1]+1))
        amud_node.refs = subref_list
        amud_nodes.append(amud_node)
        
    record.validate()

    index = {
        "title": "Sefer Yereim",
        "categories": ["Halakhah"],
        "alt_structs": {"Amud": amud_nodes.serialize()},
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_y_text():
    with open("יראים מרובע.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf8",'replace'), myFile.readlines()))
    #first post intro
    in_intro=False
    for line in lines:
        if u"הקדמת המחבר הר אליעזר ממיץ" in line:
            in_intro=True
        elif in_intro:
            version = {
                'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
                'language': 'he',
                'text': remove_tags_y(line)
            }
            #post_text_weak_connection('Sefer Yereim, Author\'s Introduction'+en_title, version)
            break
    
    #now rest of text
    in_text=False
    #vavs are added in next siman, even though they come before the siman marker
    #last_tag_was_a_vav=False
    add_to_next=[]
    mitzvas = []
    running_count = 0
    next_one_doesnt_append=False
    add_after_next=0
    for line in lines:
        if not_blank(line):
            if u"@00ספר יראים" in line:
                in_text=True
            elif "BADLABEL" in line:
                add_to_next.append(line)
            #this is the last line
            elif u"@98תם" in line:
                add_to_next.append(line)
                mitzvas.append(add_to_next)
                break

            elif in_text:
               
                if (u"@22" in line or u"@03" in line) and ("SKIP_LABEL" not in line and siman_has_siman_starter(add_to_next)):
                    mitzvas.append(add_to_next)
                    for x in range(add_after_next):
                        mitzvas.append([])
                    add_after_next=0
                    add_to_next=[line+'<br>']
                    if re.search(ur'(?<=סימן )\S+',line):
                        if getGematria(re.search(ur'(?<=סימן )\S+',line).group())!=len(mitzvas)+1:
                            print "NO GOOD! ",len(mitzvas)
                    next_one_doesnt_append=True
                else:
                    if next_one_doesnt_append:
                        add_to_next[-1]=add_to_next[-1]+line
                        next_one_doesnt_append=False
                    else:
                        add_to_next.append(line)
                #sometimes there's more than one siman in a section, we add blanks to account for this
                #we need to account for extra simanim seperately, since sometimes siman markers aren't the start of a new index position
                if u"@22" in line and "SKIP_LABEL" not in line:
                    """
                    if re.search(ur"(?<=(@22|סימן))"+ ur'[ ]?'+ur'[א-ת]+',line):
                        for x in range(getGematria(re.search(ur"(?<=סימן)"+ ur'[ ]?'+ur'[א-ת]+',line).group())-len(mitzvas)-2):
                            mitzvas.append([])
                    """
                    add_after_next=get_siman_count(line)-1
                    add_after_next+=line.count("ADD_EXTRA_AFTER")
    for sindex, siman in enumerate(mitzvas):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    0/1
    return mitzvas
def siman_has_siman_starter(s_list):
    #here we check if this siman list has a siman starter marker, to detirmine if this siman marker is a new siman or not
    for line in s_list:
        if u"@22" in line:
            return True
    return False
def remove_tags_y(s):
    #here we return the edited sting as well as the data-order numbers found in the paragraph, so that parser can index them.
    for regmatch in re.findall(ur"@77 *\([א-ת\* ]{1,4}\)",s):
        s=s.replace(regmatch, u"<i \"data-commentator=Toafot Re\'em\" \"data-order="+str(getGematria(regmatch))+"\"></i>")
    return re.sub(ur"@\d{1,4}",u"",s).replace(u"BADLABEL",u"").replace(u"SKIP_LABEL",u"")
def get_data_orders(s):
    #here we get data-order numbers in the paragraph
    found_order_numbers = []
    for regmatch in re.findall(ur"@77 *\([א-ת\* ]{1,4}\)",s):
        found_order_numbers.append(getGematria(regmatch))
    return found_order_numbers
def remove_tags_ty(s):
    return re.sub(ur"@\d{1,4}",u"",s)
    """
    def bold_dh(some_string):
        splits = {
            "pi_split":some_string.split(u"פי"+u"'"),
            "pirush_split": some_string.split(u"פירוש"),
            "i_kashiya_split": some_string.split(u"אי קשיא"),
            "kashiya_li_split": some_string.split(u"קשיא לי"),
            "period_split": [some_string.split(u".")[0]+".",''],
            }
        #if re.match(ur".*?"+ur"ו?כו"+"\'?",some_string):
        if re.search(ur".*?כו"+ur"\'?(?=[ \.])",some_string):
            splits["chulei_split"]= [re.search(ur".*?כו?"+"\'?(?=[ \.])",some_string).group(),'']
        split_dh=get_smallest(splits)
        if len(split_dh.split(" "))<30:
            return u"<b>"+split_dh+u"</b>"+some_string[len(split_dh):]
        return some_string
    """
def get_siman_count(line):
    line = re.sub(ur"\[.*?\]",u"",line)
    line = re.sub(ur"\(.*?\)",u"",line)
    line = re.sub(ur"@\d{1,3}",u"",line)
    line = line.replace(u'סימן','').replace(u'.',u'')
    line = re.sub(ur"[A-Za-z_]+",u'',line)
    return len(filter(lambda(x): not_blank(x), line.split(u' ')))
def get_smallest(dic):
    return_dh = ""
    keyp = ""
    smallest_so_far = int
    for key in dic.keys():
        if len(dic[key][0])<smallest_so_far:
            smallest_so_far=len(dic[key][0])
            return_dh = dic[key][0]
            keyp=key
    return return_dh
def get_amud_index():
    text = parse_y_text()
    amud_index=[]
    amud_dict={}
    for sindex, siman in enumerate(text):
        for pindex, paragraph in enumerate(siman):
            if u"@02" in paragraph and u"BADLABEL" not in paragraph:
                if len(amud_dict.keys())>0:
                    amud_dict["Ending Index"]=last_index
                    #set end of last vav to last index
                    amud_dict["Vavim"][-1]["End Vav"]=last_index
                    amud_index.append(amud_dict)
                amud_dict={"Title":remove_tags_y(paragraph), "Starting Index": [sindex, pindex], "Vavim":[{"Start Vav":[sindex, pindex]}]}
            if u"@03" in paragraph and "BADLABEL" not in paragraph:
                amud_dict["Vavim"][-1]["End Vav"]=last_index
                amud_dict["Vavim"].append({"Start Vav":[sindex, pindex]})
            last_index=[sindex, pindex]
    amud_dict["Ending Index"]=last_index
    #set end of last vav to last index
    amud_dict["Vavim"][-1]["End Vav"]=last_index
    amud_index.append(amud_dict)
    return amud_index
def post_y_text():
    raw_text = parse_y_text()
    final_text = []
    for siman in raw_text:
        final_text.append(list(map(lambda(x):remove_tags_y(x),siman)))
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': final_text
    }
    #post_text_weak_connection
    post_text('Sefer Yereim', version,weak_network=True, skip_links=True, index_count="on")
def post_ty_index():
    # create index record
    record = SchemaNode()
    record.add_title('Toafot Re\'em', 'en', primary=True, )
    record.add_title(u'תועפות ראם', 'he', primary=True, )
    record.key = 'Toafot Re\'em'
    
    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Commentor's Introduction", 'en', primary = True)
    intro_node.add_title("הקדמת המחבר", 'he', primary = True)
    intro_node.key = "Commentor's Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    
    #now we add Mitzvah struct:
    mitzvah_struct = JaggedArrayNode()
    mitzvah_struct.key = "default"
    mitzvah_struct.default = True
    mitzvah_struct.depth = 2
    mitzvah_struct.addressTypes = ['Integer','Integer']
    mitzvah_struct.sectionNames = ['Mitzvah','Paragraph']
    record.append(mitzvah_struct)
    
    record.validate()

    index = {
        "title": 'Toafot Re\'em',
        "categories": ["Halakhah"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_ty_text():
    #here we make a 2d array
    #the position of the sub array in the array corresponds to the siman it is indexed under.
    #For this reason, there are blank index places to account for combined ty_list.
    #each outer array contains arrays correpsonding to comments, each comment has order-number, text data, as well as paragraph index
    
    #first, index data-order paragraphs:
    ty_list=[[] for x in range(464)]
    siman_data_order_paragraphs = [[] for x in range(464)]
    for sindex, siman in enumerate(parse_y_text()):
        for pindex, paragraph in enumerate(siman):
            for data_order in get_data_orders(paragraph):
                siman_data_order_paragraphs[sindex].append(pindex)
                print sindex, data_order
                
    with open('יראים מוכן.txt') as myFile:
        lines = list(map(lambda x: x.decode("utf8",'replace'), myFile.readlines()))
    siman_box=[]
    too_many_box = []
    in_text=False
    current_siman=1
    current_order_number = 1
    for line in lines:
        if u"@00עמוד עריות" in line:
            in_text=True
        elif in_text and u"@00" not in line:
            if u"@22" in line:
                if re.search(ur"(?<=סימן)"+ ur' '+ur'[\S]+',line):
                    current_siman=getGematria(re.search(ur"(?<=סימן)"+ ur'[ ]?'+ur'[א-ת]+',line).group())
                else:
                    current_siman+=1
            elif u"@11" in line:
                current_order_number = getGematria(line)
            elif not_blank(line):
                #print "NOW APPENDING ", current_siman
                if len(siman_data_order_paragraphs[current_siman-1])<1:
                    if current_siman not in too_many_box:
                        too_many_box.append(current_siman)
                elif len(ty_list[current_siman-1])>1:
                    ty_list[current_siman-1][1]=[ty_list[current_siman-1][1],remove_tags_ty(line)]
                else:
                    ty_list[current_siman-1].append([current_order_number, [remove_tags_ty(line)], siman_data_order_paragraphs[current_siman-1].pop(0)])
    for thindex, that in enumerate(siman_data_order_paragraphs):
        if len(that)<0:
            print "TOO MANY REFS in ", current_siman
    for siman in too_many_box:
        print siman
    return ty_list
def post_ty_text():
    ty_list = parse_ty_text()
    ty_text=[[] for x in range(len(ty_list))]
    for siman, comment_list in enumerate(ty_list):
        for comment in comment_list:
            ty_text[siman].append(comment[1])
    
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': ty_text
    }
    post_text('Toafot Re\'em', version,weak_network=True, skip_links=True, index_count="on")
def link_ty():
    for siman, comment_list in enumerate(parse_ty_text()):
        for comment_index, comment in enumerate(comment_list):
            link = {
            'refs': ['Sefer Yereim {}:{}'.format(siman, comment[2]), 'Toafot Re\'em {}:{}'.format(siman, comment_index)],
            'type': 'commentary',
            'inline_reference': {
                'data-commentator': "Toafot Re\'em",
                'data-order': comment[0]
                }
            }
                
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);

#parse_y_text()
#post_ty_index()
#post_ty_text()
#post_y_text()
link_ty()
"""
method we ended up not using;
def get_siman_count(line):
    line = re.sub(ur"\[.*?\]",u"",line)
    line = re.sub(ur"\(.*?\)",u"",line)
    line = re.sub(ur"@\d{1,3}",u"",line)
    line = line.replace(u'סימן','').replace(u'.',u'')
    return len(filter(lambda(x): not_blank(x), line.split(u' ')))

Here we record abnormailities:

-no siman 179
-two siman 257
"""