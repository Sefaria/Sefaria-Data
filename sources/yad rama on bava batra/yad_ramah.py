# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
from bs4 import BeautifulSoup
import re
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	


gematria = {}
gematria['א'] = 1
gematria['ב'] = 2
gematria['ג'] = 3
gematria['ד'] = 4
gematria['ה'] = 5
gematria['ו'] = 6
gematria['ז'] = 7
gematria['ח'] = 8
gematria['ט'] = 9
gematria['י'] = 10
gematria['כ'] = 20
gematria['ל'] = 30
gematria['מ'] = 40
gematria['נ'] = 50
gematria['ס'] = 60
gematria['ע'] = 70
gematria['פ'] = 80
gematria['צ'] = 90
gematria['ק'] = 100
gematria['ר'] = 200
gematria['ש'] = 300
gematria['ת'] = 400

inv_gematria = {}
for key in gematria.keys():
	inv_gematria[gematria[key]] = key

errors = open('errors', 'w')

if len(sys.argv) == 2:
	args = sys.argv[1]
elif len(sys.argv) == 3:
	args = sys.argv[1] + " "+sys.argv[2]
title = "Yad Ramah on "+args
heb_title = u"בבא בתרא"

new_daf_p = re.compile("\[\W{2,6},\W{2}\]")
new_comment_p = re.compile("\W.*?\.")
current_perek = 0
perakim = {}
current_daf = 1
current_amud = 2
current_comment = 0
start_title = "YR"
num_files = 72
dappim = []
prev_line=""
prev_match = ""
comment_file = open('possible_gematrias', 'w')
comm_count=0
first_line_in_file = True
comm_dict = {}
dh_dict = {}
comm_dict_no_dh={}
daf_dict = {}


def addTextToDicts(text, perek, comment, daf):
    if not perek in comments_order:
        comments_order[perek] =  []
    comments_order[perek].append(comment)
    if perek not in daf_dict:
        daf_dict[perek] = {}
    try:
        dh, text = text.split(".", 1)
        dh_dict[perek][comment] = dh
        comm_dict[perek][comment] = text
        if not daf in daf_dict[perek]:
            daf_dict[perek][daf] = []
        daf_dict[perek][daf].append(dh)
    except:
        comm_dict_no_dh[perek][comment] = text
        if not daf in daf_dict[perek]:
            daf_dict[perek][daf] = []
        daf_dict[perek][daf].append("")

comments_order = {}
text=""
bad_text = re.compile(".*>.*?<")
bad_text_2 = re.compile(".*<.*?>")
for count in range(num_files):
    f = open(start_title+str(1+count)+".txt", 'r')
    first_line_in_file = True
    for line in f:
        line = line.replace("\n", "")
        if bad_text.match(line):
            line = line.replace(bad_text.match(line).group(0), " ")
        if bad_text_2.match(line):
            line = line.replace(bad_text_2.match(line).group(0), " ")
        line = line.replace(">","").replace("<","")
        words = line.split(" ")
        perek = line.find("פרק")
        if perek < 5 and perek >= 0 and len(words) < 5 and line.find("בפרק") == -1:
            prev_perek = current_perek
            current_perek += 1
            perek_name = line.replace("#", "")
            perakim[current_perek] = perek_name
            comm_dict[current_perek] = {}
            dh_dict[current_perek] = {}
            comm_dict_no_dh[current_perek] = {}
            comments_order[current_perek] = []
            if current_perek > 1:
                addTextToDicts(text, prev_perek, current_comment, current_daf)
                text = ""
            first_comment = True
            continue
        daf_changed = False
        for word in words:
            if new_daf_p.match(word):
                prev_daf = current_daf
                prev_amud = current_amud
                match = new_daf_p.match(word).group(0)
                line = line.replace(match, "")
                daf_info = match.replace("[","").replace("]", "")
                current_daf = getGematria(daf_info.split(",")[0])
                current_amud = getGematria(daf_info.split(",")[1])
                current_daf *= 2
                if current_amud == 1:
                    current_daf -= 1
                daf_changed = True
        if new_comment_p.match(line):
            comment = new_comment_p.match(line).group(0).replace("\xef\xbb\xbf","").replace(" ", "").replace(".","")
            length_good = len(comment) <= 6
            if length_good and comment.find('"')==-1 and (prev_line.find("#")>=0 or first_line_in_file):
                prev_comment = current_comment
                current_comment = getGematria(comment)
                if current_comment == 100:
                    print line
                line = line.replace(comment+".", "")
                if not first_comment:
                    if daf_changed:
                        addTextToDicts(text, current_perek, prev_comment, prev_daf)
                    else:
                        addTextToDicts(text, current_perek, prev_comment, current_daf)
                    text = ""
                first_comment = False
        prev_line = line
        line = line.replace(":#", ":<br>")
        line = line.replace(": #", ":<br>")
        line = line.replace(".#", ".<br>")
        line = line.replace(". #", ".<br>")
        line = line.replace(",#", ",<br>")
        line = line.replace(", #", ",<br>")
        line = line.replace("#", "")
        text += line
        first_line_in_file = False
comment_file.close()


root = SchemaNode()
root.key = title
root.add_title(title, "en", primary=True)
root.add_title(u"יד רמה על "+heb_title, "he", primary=True)
for current_perek in perakim:
    perek_name = perakim[current_perek]
    new_perek_node = SchemaNode()
    new_perek_node.key = "Perek"+str(current_perek)
    new_perek_node.add_title(perek_name.decode('utf-8'), "he", primary=True)
    new_perek_node.add_title("Perek "+str(current_perek), "en", primary=True)
    for comment_key in comments_order[current_perek]:
        comment_node = JaggedArrayNode()
        comment_node.add_title("Comment "+str(comment_key), "en", primary=True)
        comment_node.add_title(u"פירוש "+numToHeb(comment_key), "he", primary=True)
        comment_node.key = 'Comment'+str(current_perek)+','+str(comment_key)
        comment_node.depth = 1
        comment_node.addressTypes = ["Integer"]
        comment_node.sectionNames = ["Paragraph"]
        comment_node.validate()
        new_perek_node.append(comment_node)
    new_perek_node.validate()
    root.append(new_perek_node)

root.validate()

index = {
    "title": title,
    "categories": ["Commentary2", "Talmud", "Yad Ramah"],
    "schema": root.serialize()
}
post_index(index)

how_many=0
for current_perek in range(10):	
    current_perek+=1
    count=0
    for comment_key in comments_order[current_perek]:
        how_many+=1
        try:
            comm = comm_dict[current_perek][comment_key]
            dh = dh_dict[current_perek][comment_key]
            comm = "<b>"+dh+"</b>. " + comm
        except:
            comm = comm_dict_no_dh[current_perek][comment_key]
        if comm.find("<br>") == 0:
            comm = comm[4:]
        comm = comm.replace("<br><br>", "<br>")
        text = {
            "versionTitle": title,
            "versionSource": "http://www.sefaria.org/",
            "language": "he",
            "text": [comm],
            }
        post_text(title+", Perek "+str(current_perek)+", Comment "+str(comment_key), text)

'''
need to add in blanks when creating daf_dict
then 
'''

match_obj=Match(in_order=True, min_ratio=80, guess=False, range=True)
skipped_arr = []
result = {}

for current_perek in range(10):
    current_perek+=1
    print current_perek
    search_for = 0
    for daf in sorted(daf_dict[current_perek].keys()):
        print daf
        text = get_text("Bava Batra."+AddressTalmud.toStr("en", daf))
        dh_list = daf_dict[current_perek][daf]
        result[daf] = match_obj.match_list(dh_list, text, "Bava Batra "+AddressTalmud.toStr("en", daf))
        print result[daf]
        for key in result[daf]:
            if result[daf][key].find("0:") >= 0:
                result[daf][key] = result[daf][key].replace("0:","")
            search_for += 1
            line_n = result[daf][key]
            count = 0
            for comment_key in comments_order[current_perek]:
                count+=1
                if count < search_for:
                    continue
                post_link({
                    "refs": [
                             "Bava Batra."+AddressTalmud.toStr("en", daf)+"."+str(line_n),
                            title+", Perek "+str(current_perek)+", Comment "+str(comment_key)
                        ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "Yad Ramah Linker",
                 })
                break
