# -*- coding: utf8 -*-
#
__author__ = 'eliav'
import re
import sys
from fuzzywuzzy import fuzz
from sefaria.model import *

masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")
rashi = TextChunk(Ref("Rashi on %s" % masechet), "he").text
shas = TextChunk(Ref("%s" % masechet), "he").text
count = 0
too_match = 0
matched = 0
non_match = 0
list_of_many_finds={}
links_list = []
found_list =[]


def convert_inf_to_daf(index):
    if index%2==0:
        amud="a"
    else:
        amud = "b"
    daf = (index/2) + 1
    return str(daf) + amud


def index_to_daf():
    for daf_num,  daf in enumerate(shas):
        rashi_daf = rashi[daf_num]
        for rashi_line in rashi_daf:
            for rashi_dh in rashi_line:
                dh = re.split(ur"(?:-|–)",rashi_dh)[0]
                match(dh,shas[daf_num],daf_num,)


def match(dh,shas,index, ratio=100):
    found_dict = {}
    list_of_found_links = []
    found_dict['index']= index
    found_dict['dh'] = dh
    found = 0
    global too_match
    global matched
    global non_match
    global count
    for line_n, line in enumerate(shas):
        if dh in line and line in dh:
            found += 1
            the_line=line_n
            list_of_found_links.append(line_n)
        elif fuzz.partial_ratio(dh,line) >= ratio and fuzz.partial_ratio(line,dh) >= ratio:
             found +=1
             the_line=line_n
             list_of_found_links.append(line_n)
        elif fuzz.partial_ratio(dh,line) >= ratio:
             found+=1
             the_line=line_n
             list_of_found_links.append(line_n)
        elif fuzz.partial_ratio(line, dh) >= ratio:
             found+=1
             the_line=line_n
             list_of_found_links.append(line_n)
    if found > 1:
        found_dict['lines']=list_of_found_links
        too_match +=1
        list_of_many_finds[index]=dh
        found_dict["more_than_one"]="TRUE"
        found_list.append(found_dict)
    if found ==1:
        found_dict['lines']=list_of_found_links
        found_dict["more_than_one"]="FALSE"
        dafamud = convert_inf_to_daf(index)
       # if len(links_list)>0:
           # previos = re.split(":",links_list[len(links_list)-1])[1]
            #if int(previos) > the_line+1:
             #   print "previos", previos, "this",  the_line+1
        link = "Rashi on %s" % masechet +" " + dafamud +":"+ str(the_line+1) + " " + dh
        links_list.append(link)
        print "found!!",dafamud,":", the_line," ", dh
        matched+=1
        found_list.append(found_dict)
    if found == 0:
        if ratio > 60:
            match(dh,shas, index, ratio-2)
        else:
            list_of_found_links.append(-1)
            found_dict['lines']=list_of_found_links
            found_dict["more_than_one"]="FALSE"
            print len(dh)
            non_match += 1
            found_list.append(found_dict)


def get_comments():
    comments =[]
    rf = Ref('Rashi on %s' % masechet)
    tc = rf.text(lang='he').text
    for i,chap in enumerate(tc):
        for j,line in enumerate(chap):
            for k, com in enumerate(line):
                if isinstance(com, basestring) and len(com.strip()) > 0:
                    dafamud=convert_inf_to_daf(i)
                    dh = re.split(ur"(?:-|–)",com)[0]
                    placement= u"Rashi on %s " % masechet + dafamud + ":" + str(j+1) + " " + dh
                    comments.append(placement)
    return comments


def double_dict(found_list):
    file = open("multiple.txt",'w')
    for i, diction in enumerate(found_list):
        print found_list[i]
        if found_list[i]["more_than_one"]=="TRUE":
            if found_list[i]["index"]== found_list[i-1]["index"]:
                #for line in diction['lines']:
                    pre_line = found_list[i-1]['lines']
                    print "pre_lines", pre_line
                    if len(found_list[i-1]['lines'])==1:
                        lines = [j for j in found_list[i]['lines'] if j >= pre_line[0]]
                        if len(lines)!=0:
                            print "lines", lines
                            file.write(str(found_list[i]["index"]) +" "+ found_list[i]['dh'].encode('utf-8') + " " + "the difference between current dh and previus is: " + str(lines) + '\n')
                            the_line= min(lines, key=lambda x:x-pre_line[0])
                            found_list[i]['lines'] =[the_line]
                            link =  "Rashi on %s" % masechet +" " +convert_inf_to_daf(found_list[i]["index"]) +":"+ str(the_line+1) + " " + found_list[i]["dh"]
                            print link
                            found_list[i]["more_than_one"]="FALSE"
                            links_list.append(link)
                        else:
                            print "no answer " +  str(found_list[i]["index"])+   found_list[i]['dh'].encode('utf-8')
                    else:
                        if found_list[i]["index"]== found_list[i+1]["index"]:
                            print "line after ", found_list[i+1]["lines"], "line: ",found_list[i]["lines"]
            else:
                print str(found_list[i]["index"])+ " " +str(min(found_list[i]["lines"]))
                link = "Rashi on %s" % masechet +" " +convert_inf_to_daf(found_list[i]["index"]) +":"+ str(min(found_list[i]["lines"])+1)
                print "new link:", link
                found_list[i]["more_than_one"]="FALSE"
                links_list.append(link)

if __name__ == '__main__':
    index_to_daf()
    print "length of links_list is:", len(links_list)
    double_dict(found_list)
    print "placed", len(links_list), "of the rashi's"
    comments= get_comments() #get real rashi's
    print "full number of rashi's is:", len(comments)
    print "found too much:", len([i for i in found_list if i['more_than_one']=='TRUE']), "did not match at all:", non_match
    diff1 = list(set(links_list).difference(comments))
    file =open('file.txt', 'w')
    for k in diff1:
       file.write(k.encode('utf-8')+"\n")
    print "placed: " + str(round(float(len(links_list))/float(len(comments)),2)*100) +"%"
    acuracy = 1 -  float(len(diff1) /float(len(links_list)))
    print "acuracy: "+ str(round(acuracy,2)*100) + "%"
    print links_list[0], comments[0]
