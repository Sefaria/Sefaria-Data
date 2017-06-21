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
        h_node.add_title('Amendments', 'en', primary=True)
        h_node.add_title(u'הגהות', 'he', primary=True)
        h_node.key = 'Amendments'
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
                w_ref+="Amendments, "
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
        for line in lines:
            if u"הגהות דשייכי" in line:
                perek_list.append(perek_box)
                self.text = perek_list
                perek_box=[]
                perek_list=[]
                in_hagahot=True
            for paragraph in line.split(u":"):
                if not_blank(paragraph):
                    perek_box.append(fix_markers(paragraph)+u":")
            for remez in re.findall(ur"@20.*?@01",line):
                #designed so entries are index locations (starting at 0)
                remez_index.append({"Remez":getGematria(remez.replace(u"רמז","")),"Perek":len(perek_list),"Paragraph":len(perek_box),"Hagahot":in_hagahot})
            for daf_ref in re.findall(ur"@10.*?@01",line):
                
                if u"ע\"א" in daf_ref:
                    amud="a"
                elif u"ע\"ב" in daf_ref:
                    amud="b"
                else:
                    amud="a-b"
                """
                daf_refs.append({"Daf":getGematria(clean_daf_ref(daf_ref)),"Amud":amud,"Perek":len(perek_list),"Paragraph":len(perek_box),"Hagahot":in_hagahot})
                """
                if in_hagahot:
                    perek= get_perek(Ref(self.record_name_en+" "+str(getGematria(clean_daf_ref(daf_ref)))+amud))
                    if perek-1!=len(perek_list):
                        perek_list.append(perek_box)
                        perek_box=[]
                        #if difference is exactly 1, we need to add. Otherwise, leave it alone
                        for x in range(perek-len(perek_list)-1):
                            perek_list.append([])
            if u"סליק פירקא" in line:
                perek_list.append(perek_box)
                perek_box = []
        perek_list.append(perek_box)
        self.hagahot=perek_list
        self.remez_index = remez_index
        self.daf_refs = daf_refs
        
        #to print text:
        for pindex, perek in enumerate(self.text):
            for cindex, comment in enumerate(perek):
                print "TEXT",pindex, cindex, comment
        for pindex, perek in enumerate(perek_list):
            for cindex, comment in enumerate(perek):
                print "HAGAHA",pindex, cindex, comment
        
        segment_remez_refs(remez_index)
    def mord_post_text(self):
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': self.text
        }
        #post_text_weak_connection('Mordechai on '+self.record_name_en, version)
        
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': self.hagahot
        }
        post_text_weak_connection('Mordechai on '+self.record_name_en+', Amendments', version)
    def mord_link_text(self):
        for link_ref in self.daf_refs:
            print link_ref
            link = (
                    {
                    "refs": [
                             self.record_name_en+" "+str(link_ref["Daf"])+link_ref["Amud"],
                             'Mordechai on '+self.record_name_en+", "+str(link_ref["Perek"]+1)+":"+str(link_ref["Paragraph"]+1),
                             ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "sterling_tos_rid_linker"
                    })
            post_link(link, weak_network=True)
            
        main_tc = TextChunk(Ref('Mordechai on '+self.record_name_en))
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
    in_hagahot=False
    return_list = []
    starting_ref = refs[0]
    for index in range(1,len(refs)):
        finished=False
        remez_count+=1
        if (remez_count>9 and refs[index-1]["Paragraph"]!=refs[index]["Paragraph"] and refs[index-1]["Paragraph"]!=starting_ref["Paragraph"]) or (refs[index]["Hagahot"]!=in_hagahot):
            in_hagahot=refs[index]["Hagahot"]
            return_list.append({"Starting Ref":starting_ref, "Ending Ref":refs[index-1]})
            starting_ref=refs[index]
            finished=True
            remez_count=0
    if not finished:
        return_list.append({"Starting Ref":starting_ref, "Ending Ref":refs[index-1]})
    return return_list

def make_remez_range(remez_segment):
    return str(remez_segment["Starting Ref"]["Perek"]+1)+":"+str(remez_segment["Starting Ref"]["Paragraph"]+1)+"-"\
        +str(remez_segment["Ending Ref"]["Perek"]+1)+":"+str(remez_segment["Ending Ref"]["Paragraph"]+1)
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def fix_markers(s):
    return s.replace(u"@01",u"</small>").replace(u"@10",u"<small>").replace(u'@20',u"<small>")
def get_perek(ref):
    range_dict = get_perek_ranges(ref.book)
    for chapter_range in range_dict.keys():
        if Ref(chapter_range).contains(ref):
            return range_dict[chapter_range]
def get_perek_ranges(tractate_name):
    return {node['wholeRef']:int(node['titles'][0]['text'].split()[1]) for node in library.get_index(tractate_name).alt_structs["Chapters"]['nodes']}
posting_term=False
posting_index=False
posting_text=True
linking=False

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

    