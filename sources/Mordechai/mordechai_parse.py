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
import re
import codecs



def mord_post_term():
    term_obj = {
        "name": "Mordechai",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Mordechai",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מרדכי',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
class Tractate:
    def __init__(self):
        #later, we should be able to extract this info from the file name
        self.record_name_en = "Bava Batra"
        self.record_name_he = u"בבא בתרא"
        self.file_name = "מרדכי בבא בתרא - ערוך לתג - סופי.txt"
        self.mord_parse_text()
    def mord_post_index(self):   
        record = SchemaNode()
        record.add_title('Mordechai on '+self.record_name_en, 'en', primary=True)
        record.add_title(u'מרדכי על'+' '+self.record_name_he, 'he', primary=True)
        record.key = 'Mordechai on '+self.record_name_en
        #add default
        default_node = JaggedArrayNode()
        default_node.key = "default"
        default_node.default = True
        default_node.depth = 2
        default_node.addressTypes = ["Integer", "Integer"]
        default_node.sectionNames = ["Chapter", "Paragraph"]
        record.append(default_node)
        #add hagahot node
        h_node = JaggedArrayNode()
        h_node.add_title('Hagahot Mordechai', 'en', primary=True)
        h_node.add_title(u'הגהות מרדכי', 'he', primary=True)
        h_node.key = 'Hagahot Mordechai'
        h_node.depth = 2
        h_node.addressTypes = ["Integer", "Integer"]
        h_node.sectionNames = ["Chapter", "Paragraph"]
        record.append(h_node)
        
        #now we make alt structs
        remez_nodes = SchemaNode()

        for remez_segment in segment_remez_refs(self.remez_index):
            remez_node = ArrayMapNode()
            remez_node.includeSections = False
            remez_node.depth = 0
            w_ref = "Mordechai on "+self.record_name_en+", "
            if remez_segment["Starting Ref"]["Hagahot"]:
                w_ref+="Hagahot Mordechai, "
            remez_node.wholeRef = w_ref+make_remez_range(remez_segment)
            en_title = "Remez "+str(remez_segment["Starting Ref"]["Remez"])+" Through "+str(remez_segment["Ending Ref"]["Remez"])
            he_title = u"רמז"+u" "+numToHeb(remez_segment["Starting Ref"]["Remez"])+u" עד "+numToHeb(remez_segment["Ending Ref"]["Remez"])
            remez_node.key = en_title
            remez_node.add_title(en_title, 'en', primary = True)
            remez_node.add_title(he_title, 'he', primary = True)
            remez_nodes.append(remez_node)
        record.validate()   
        index = {
            "title":'Mordechai on '+self.record_name_en,
            "base_text_titles": [
              self.record_name_en
            ],
            "alt_structs": {"Remez": remez_nodes.serialize()},
            "dependence": "Commentary",
            "categories":["Talmud","Bavli","Commentary","Mordechai"],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def mord_parse_text(self):
        with open(self.file_name) as myfile:
            lines = list(map(lambda x: x.decode('utf8', 'replace'), myfile.readlines()))
        perek_list=[]
        perek_box =[]
        remez_index=[]
        daf_refs=[]
        in_hagahot = False
        last_paragraph = {}
        for line in lines:
            if u"הגהות דשייכי" in line:
                remez_index[-1]["Terminating Ref"]=last_paragraph
                daf_refs[-1]["Terminating Ref"]=last_paragraph
                perek_list.append(perek_box)
                self.text = perek_list
                perek_box=[]
                perek_list=[]
                in_hagahot=True
            for paragraph in line.split(u":"):
                if not_blank(paragraph):
                    for remez in re.findall(ur"@20.*?@01",paragraph):
                        #designed so entries are index locations (starting at 0)
                        if len (remez_index)>0 and "Terminating Ref" not in remez_index[-1]:
                            remez_index[-1]["Terminating Ref"]=last_paragraph
                        remez_index.append({"Remez":getGematria(remez.replace(u"רמז","")),"Perek":len(perek_list),"Paragraph":len(perek_box),"Hagahot":in_hagahot})
                    for daf_ref in re.findall(ur"@10.*?@01",paragraph):
                        if u"ע\"א" in daf_ref:
                            amud="a"
                        elif u"ע\"ב" in daf_ref:
                            amud="b"
                        else:
                            amud="a-b"
                        if len(daf_refs)>0:
                            if "Terminating Ref" not in daf_refs[-1]:
                                daf_refs[-1]["Terminating Ref"]=last_paragraph
                        daf_refs.append({"Daf":getGematria(clean_daf_ref(daf_ref)),"Amud":amud,"Perek":len(perek_list),"Paragraph":len(perek_box),"Hagahot":in_hagahot})
                    last_paragraph={"Perek":len(perek_list),"Paragraph":len(perek_box)}
                    if paragraph[-1]==u".":
                        paragraph=paragraph[:-1]
                    perek_box.append(fix_markers(paragraph)+u":")    
                    

            if u"סליק " in line:
                if "Terminating Ref" not in daf_refs[-1]:
                    daf_refs[-1]["Terminating Ref"]=last_paragraph
                perek_list.append(perek_box)
                #bug with double paragraph
                if u"סליק פרק ו' וז" in line:
                    perek_list.append([])
                perek_box = []
                #last_paragraph={"Perek":len(perek_list),"Paragraph":len(perek_box)}
        perek_list.append(perek_box)
        self.hagahot=perek_list
        self.daf_refs = daf_refs
        remez_index[-1]["Terminating Ref"]=last_paragraph
        self.remez_index = remez_index
        """
        #to print text:
        for pindex, perek in enumerate(self.text):
            for cindex, comment in enumerate(perek):
                print "TEXT",pindex, cindex, comment
        for pindex, perek in enumerate(perek_list):
            for cindex, comment in enumerate(perek):
                print "HAGAHA",pindex, cindex, comment
        """
        print "Daf Refs:"
        for ref in daf_refs:
            print ref
        segment_remez_refs(remez_index)
    def mord_post_text(self):
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': self.text
        }
        post_text_weak_connection('Mordechai on '+self.record_name_en, version)
        
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': self.hagahot
        }
        post_text_weak_connection('Mordechai on '+self.record_name_en+', Hagahot Mordechai', version)
    def mord_link_text(self):
        matched_count = 0.00
        total = 0.00
        not_matched=[]
        for ref in self.daf_refs:
            tractate_chunk = TextChunk(Ref(self.record_name_en+"."+str(ref["Daf"])+ref["Amud"]),"he")
            m_chunk = TextChunk(Ref('Mordechai on '+self.record_name_en+make_daf_ref_range(ref)),"he")
            print 'Mordechai on '+self.record_name_en+" "+make_daf_ref_range(ref)
            matches = match_ref(tractate_chunk,m_chunk,base_tokenizer,dh_extract_method=dh_extract_method,verbose=True)
            
            if "comment_refs" in matches and ref["Hagahot"]:
                amud = "a" if ref["Amud"]=="a-b" else ref["Amud"]
                last_ref = Ref(self.record_name_en+"."+str(ref["Daf"])+amud+" 1")
                daf_not_matched = []
                for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                    print base,comment
                    if base:
                        link = (
                                {
                                "refs": [
                                         base.normal(),
                                         comment.normal(),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_mordechai_linker"
                                })
                        post_link(link, weak_network=True)
                        matched_count+=1
                        while len(daf_not_matched)>0:
                            link = (
                                    {
                                    "refs": [
                                             last_ref.normal()+"-"+base.ending_ref().normal_last_section(),
                                             daf_not_matched.pop().normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_mordechai_linker"
                                    })
                            matched_count+=1
                            post_link(link, weak_network=True)
                        last_ref = base
                    else:
                        daf_not_matched.append(comment)
                        if link_index==len(matches["matches"])-1:
                            while len(daf_not_matched)>0:
                                link = (
                                        {
                                        "refs": [
                                                 last_ref.normal()+"-"+str(len(TextChunk(Ref(last_ref.normal().split(":")[:-1][0])).text)),
                                                 daf_not_matched.pop().normal(),
                                                 ],
                                        "type": "commentary",
                                        "auto": True,
                                        "generated_by": "sterling_"+self.record_name_en+"_mordechai_linker"
                                        })
                                matched_count+=1
                                post_link(link, weak_network=True)
                    total+=1
            else:
                #not_matched.append(get_daf_en(amud_index))
                total+=1
        if total!=0:
            print "Ratio: "+str(matched_count/total)
        else:
            print "Ratio: No Matches..."
        print "Not Matched:"
        for nm in not_matched:
            print nm
            """
            print link_ref
            link = (
                    {
                    "refs": [
                             self.record_name_en+" "+str(link_ref["Daf"])+link_ref["Amud"],
                             'Mordechai on '+self.record_name_en+", "+str(link_ref["Perek"]+1)+":"+str(link_ref["Paragraph"]+1),
                             ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "sterling_mordechai_linker"
                    })
            post_link(link, weak_network=True)
            """
def make_talmud_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc2 = tc.text[index]
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def clean_daf_ref(s):
    return s.replace(u"דף",u"").replace(u"ע\"א",u"").replace(u"ע\"ב",u"")
def segment_remez_refs(refs):
    remez_count = 0
    return_list = []
    starting_ref = refs[0]
    for index, ref in enumerate(refs[1:]):
        if ref["Hagahot"]!=refs[index-1]["Hagahot"]:
            last_before_hagahot=refs[index-1]
    for index in range(1,len(refs)):
        finished=False
        remez_count+=1
        skip_next=False
        if (remez_count>9 and refs[index-1]["Paragraph"]!=refs[index]["Paragraph"] and refs[index-1]["Paragraph"]!=starting_ref["Paragraph"]) or refs[index-1]==last_before_hagahot:
            in_hagahot=refs[index]["Hagahot"]
            return_list.append({"Starting Ref":starting_ref, "Ending Ref":refs[index-1]})
            starting_ref=refs[index]
            finished=True
            remez_count=0
    return_list.append({"Starting Ref":starting_ref, "Ending Ref":refs[-1]})
    return return_list
def make_remez_range(remez_segment):
    return str(remez_segment["Starting Ref"]["Perek"]+1)+":"+str(remez_segment["Starting Ref"]["Paragraph"]+1)+"-"\
        +str(remez_segment["Ending Ref"]["Terminating Ref"]["Perek"]+1)+":"+str(remez_segment["Ending Ref"]["Terminating Ref"]["Paragraph"]+1)
def make_daf_ref_range(daf_range):
    return_string= ", Hagahot Mordechai " if daf_range["Hagahot"] else ' '
    return return_string+str(daf_range["Perek"]+1)+":"+str(daf_range["Paragraph"]+1)+"-"+str(daf_range["Terminating Ref"]["Perek"]+1)+":"+\
        str(daf_range["Terminating Ref"]["Paragraph"]+1)
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def m_filter(some_string):
    #asssume every piece of text has a DH
    return True 
def remove_extra_space(s):
    while u"  " in s:
        s = s.replace(u"  ",u" ")
    return s
def dh_extract_method(some_string):
    some_string=re.sub(ur"[\[\]\(\)\*]",u"",some_string)
    some_string = re.sub(ur"<small>.*?</small>",u"",remove_extra_space(some_string))
    splits = {
        "pi_split":some_string.split(u"פי"+u"'"),
        "pirush_split": some_string.split(u"פירוש"),
        "period_split": some_string.split(u"."),
        "chulei_split": some_string.split(u"כו"+"'")
        }
    split_dh=get_smallest(splits)
    if len(split_dh.split(u" "))<10 and len(split_dh.split(u" "))>1:
        dh = split_dh
    else:
        dh=u' '.join(some_string.split(u" ")[0:4])
    return dh
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
def base_tokenizer(some_string):
    some_string = remove_extra_space(some_string).replace("<b>","").replace("</b>","").replace(":","")
    return filter(not_blank,some_string.split(" "))
def fix_markers(s):
    return s.replace(u"@01",u"</small>").replace(u"@10",u"<small>").replace(u'@20',u"<small>").replace(u"\n","")
def get_perek(ref):
    range_dict = get_perek_ranges(ref.book)
    for chapter_range in range_dict.keys():
        if Ref(chapter_range).contains(ref):
            return range_dict[chapter_range]
def get_perek_ranges(tractate_name):
    return {node['wholeRef']:int(node['titles'][0]['text'].split()[1]) for node in library.get_index(tractate_name).alt_structs["Chapters"]['nodes']}
posting_term=False
posting_index=False
posting_text=False
linking=True

tractate = Tractate()

if posting_term:
    mord_post_term()
if posting_index:
    tractate.mord_post_index()
if posting_text:
    tractate.mord_post_text()
if linking:
    tractate.mord_link_text()
    
print SEFARIA_SERVER+"/admin/reset/Mordechai on "+tractate.record_name_en
"""
EXTRA CODE
 for daf_ref in re.findall(ur"@10.*?@01",line):
     
     if u"ע\"א" in daf_ref:
         amud="a"
     elif u"ע\"ב" in daf_ref:
         amud="b"
     else:
         amud="a-b"
     
     daf_refs.append({"Daf":getGematria(clean_daf_ref(daf_ref)),"Amud":amud,"Perek":len(perek_list),"Paragraph":len(perek_box),"Hagahot":in_hagahot})
     
     if in_hagahot:
         perek= get_perek(Ref(self.record_name_en+" "+str(getGematria(clean_daf_ref(daf_ref)))+amud))
         if perek-1!=len(perek_list):
             perek_list.append(perek_box)
             perek_box=[]
             #if difference is exactly 1, we need to add. Otherwise, leave it alone
             for x in range(perek-len(perek_list)-1):
                 perek_list.append([])
"""   