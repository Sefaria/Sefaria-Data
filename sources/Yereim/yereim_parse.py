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
        "alt_structs": {"Amudim and Vavim": amud_nodes.serialize()},
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
                #under these condictions, we start a new siman
                if (u"@22" in line or u"@03" in line or u'@02' in line) and ("SKIP_LABEL" not in line and siman_has_siman_starter(add_to_next)):
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
                        if len(add_to_next)>0:
                            if u'@22' in add_to_next[-1] and u'<br>' not in add_to_next[-1]:
                                add_to_next[-1]=add_to_next[-1]+u'<br>'+line
                            else:
                                add_to_next.append(line)
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
    """
    for sindex, siman in enumerate(mitzvas):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    """
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
        s=s.replace(regmatch, u"<i data-commentator=\"Toafot Re\'em\" data-order=\""+str(getGematria(regmatch))+"\"></i>")
    
    #bold if line is some sort of heading
    header_labels = [u'@22', u'@03', u'@24', u'@02', u'@27', u'@18']
    for header_label in header_labels:
        if header_label in s:
            s=re.sub(ur'({}.*?)\n'.format(header_label),ur'<b>\1</b>\n',s)
    s=remove_extra_space(s)
    if u'@11' in s and u"@33" in s:
        s.replace(u'@11',u'<b>').replace(u'@33',u"</b>")
    #switch brackets and paraentices
    s = switch_strings(s, u'(',u'[')
    s = switch_strings(s, u')',u']')
    
    return re.sub(ur"@\d{1,4}",u"",s).replace(u"BADLABEL",u"").replace(u"SKIP_LABEL",u"").replace(u'ADD_EXTRA_AFTER',u'')
def get_data_orders(s):
    #here we get data-order numbers in the paragraph
    found_order_numbers = []
    for regmatch in re.findall(ur"@77 *\([א-ת\* ]{1,4}\)",s):
        found_order_numbers.append(getGematria(regmatch))
    return found_order_numbers
def switch_strings(input_string, string_a, string_b):
    input_string= input_string.replace(string_a,u'IN_BETWEEN')
    input_string= input_string.replace(string_b, string_a)
    input_string= input_string.replace(u'IN_BETWEEN',string_b)
    return input_string
def remove_tags_ty(s):
    return remove_extra_space(re.sub(ur"@\d{1,4}",u"",s))
def remove_extra_space(s):
    #s = s.replace(u'\t',u'').replace(ur'\xe2\x80\x83',u'')
    b=s.encode('utf8')
    b=b.replace('\xe2\x80\x83','')
    s=b.decode('utf8')
    return re.sub(ur'\s+',u' ',s)
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
    """
    for siman in final_text:
        for paragraph in siman:
            print paragraph
    """
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': final_text
    }
    post_text('Sefer Yereim', version,weak_network=True)#, skip_links=True, index_count="on")
    #post_text_weak_connection('Sefer Yereim', version)#,weak_network=True)#, skip_links=True, index_count="on")
    
def post_ty_index():
    # create index record
    record = SchemaNode()
    record.add_title('Toafot Re\'em', 'en', primary=True, )
    record.add_title(u'תועפות ראם', 'he', primary=True, )
    record.key = 'Toafot Re\'em'
    
    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary = True)
    intro_node.add_title("הקדמת המבאר", 'he', primary = True)
    intro_node.key = "Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    #add node for comments on author's introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Comments on Author's Introduction", 'en', primary = True)
    intro_node.add_title("הערות על הקדמת המחבר", 'he', primary = True)
    intro_node.key = "Comments on Author's Introduction"
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
        "categories": ["Halakhah","Commentary"],
        "dependence": "Commentary",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_intros():
    with open("יראים מרובע.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf8",'replace'), myFile.readlines()))
    mevaar_intro=[]
    author_intro=[]
    in_mevaar_intro=False
    in_author_intro=False
    for line in lines:
        if not in_mevaar_intro and not in_author_intro and u"@00" in line:
            in_mevaar_intro=True
        elif in_mevaar_intro:
            if u"@00" in line:
                in_mevaar_intro=False
                in_author_intro=True
                author_intro.append(remove_tags_y(line))
            elif not_blank(line):
                mevaar_intro.append(re.sub(ur"@\d{1,4}",u"",line))
        elif in_author_intro:
            if u"@00" in line:
                break
            elif not_blank(line):
                author_intro.append(remove_tags_y(line))
    """
    for paragraph in mevaar_intro:
        print "MI", paragraph
    for paragraph in author_intro:
        print "AI", paragraph
    """
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': mevaar_intro
    }
    #post_text('Toafot Re\'em, Introduction', version,weak_network=True)#, skip_links=True, index_count="on")
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': author_intro
    }
    post_text('Sefer Yereim, Author\'s Introduction', version,weak_network=True)#, skip_links=True, index_count="on")
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
                siman_data_order_paragraphs[sindex].append(pindex+1)
                #print sindex, data_order
    
    #checking for siman with more than 30 links:
    """
    siman_link_records={}
    for sindex, siman in enumerate(siman_data_order_paragraphs):
        for paragraph_label in siman:
            if '{} {}'.format(sindex+1, paragraph_label) in siman_link_records:
                siman_link_records['{} {}'.format(sindex+1, paragraph_label)]+=1
            else:
                siman_link_records['{} {}'.format(sindex+1, paragraph_label)]=1
    print "HERE ARE EXTRAS:"
    for key in siman_link_records.keys():
        if siman_link_records[key]>29:
            print key, ' has ', siman_link_records[key], ' links'
    1/0
    """
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
                #Here we check if there are more TR refs than footnotes in body text.
                if len(siman_data_order_paragraphs[current_siman-1])<1:
                    if current_siman not in too_many_box:
                        too_many_box.append(current_siman)
                #elif len(ty_list[current_siman-1])>1:
                #    ty_list[current_siman-1][1]=[ty_list[current_siman-1][1],remove_tags_ty(line)]
                else:
                    ty_list[current_siman-1].append([current_order_number, [remove_tags_ty(line)], siman_data_order_paragraphs[current_siman-1].pop(0)])
    """
    test for discrepencies in Yereim and TR
    for thindex, that in enumerate(siman_data_order_paragraphs):
        if len(that)<0:
            print "TOO MANY REFS in ", current_siman
    for siman in too_many_box:
        print siman
    
    for sindex, siman in enumerate(ty_list):
        for cindex, comment in enumerate(siman):
            print sindex, cindex, comment[0], comment[1][0]
    """
    return ty_list
def post_ty_text():
    #here we post intro comments:
    with open('יראים מוכן.txt') as myFile:
        lines = list(map(lambda x: x.decode("utf8",'replace'), myFile.readlines()))
    intro_box = []
    for line in lines[1:]: #first line is title
        if u'@00עמוד עריות' in line:
            break
        elif not_blank(line) and u"@11" not in line:
            intro_box.append(remove_tags_ty(line))
        
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': intro_box
    }
    #post_text('Toafot Re\'em, Comments on Author\'s Introduction', version,weak_network=True, skip_links=True, index_count="on")
    #post_text_weak_connection('Toafot Re\'em', version)#,weak_network=True)#, skip_links=True, index_count="on")
        
        
    ty_list = parse_ty_text()
    ty_text=[[] for x in range(len(ty_list))]
    for siman, comment_list in enumerate(ty_list):
        for comment in comment_list:
            ty_text[siman].append(comment[1][0])
    """
    for sindex, siman in enumerate(ty_text):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    """
    version = {
        'versionTitle': 'Sefer Yereim HaShalem, Vilna, 1892-1901',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001196456',
        'language': 'he',
        'text': ty_text
    }
    post_text('Toafot Re\'em', version,weak_network=True, skip_links=True, index_count="on")
    #post_text_weak_connection('Toafot Re\'em', version)#,weak_network=True)#, skip_links=True, index_count="on")
    
def link_ty():
    #first, link intro. 1st comment on 1st paragraph, the rest on the second.
    link = {
    'refs': ['Sefer Yereim, Author\'s Introduction 1', 'Toafot Re\'em, Comments on Author\'s Introduction 1'],
    'type': 'commentary',
    'inline_reference': {
        'data-commentator': "Toafot Re\'em",
        'data-order': 1
        }
    }
    post_link(link, weak_network=True)
    
    for pindex in range(2,17):
        link = {
        'refs': ['Sefer Yereim, Author\'s Introduction 2', 'Toafot Re\'em, Comments on Author\'s Introduction {}'.format(pindex)],
        'type': 'commentary',
        'inline_reference': {
            'data-commentator': "Toafot Re\'em",
            'data-order': pindex
            }
        }
        post_link(link, weak_network=True)
    for siman, comment_list in enumerate(parse_ty_text()):
        for comment_index, comment in enumerate(comment_list):
            print 'Sefer Yereim {}:{}'.format(siman+1, comment[2]), 'Toafot Re\'em {}:{}'.format(siman+1, comment_index+1)
            link = {
            'refs': ['Sefer Yereim {}:{}'.format(siman+1, comment[2]), 'Toafot Re\'em {}:{}'.format(siman+1, comment_index+1)],
            'type': 'commentary',
            'inline_reference': {
                'data-commentator': "Toafot Re\'em",
                'data-order': comment[0]
                }
            }
            post_link(link, weak_network=True)
            
                
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
#parse_ty_text()
#post_ty_index()
post_intros()
#post_y_index()
#post_y_text()
#post_ty_text()
#link_ty()
#link_ty()
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

headers: @22, @03, @24, @02, @27, @18
"""