# -*- coding: utf8 -*-
__author__ = 'eliav'
import re
import sys
import json
import urllib2
from fuzzywuzzy import fuzz
from sefaria.model import *
sys.path.insert(1, '../g')
#import helperFunctions as Helper
#import hebrew

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


def real_refs():
    refs = []
    p = LinkSet(Ref("Rashi on %s" %masechet) ).filter("%s" %masechet)
    for link in p:
        refs.append(link.contents()['refs'][1])
    return refs


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
        if len(links_list)>0:
            previos = re.split(":",links_list[len(links_list)-1])[1]
            if int(previos) > the_line+1:
                print "previos", previos, "this",  the_line+1
        link = "Rashi on %s" % masechet +" " + dafamud +":"+ str(the_line+1)
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


def double(list):
    for index, dh in list.iteritems():
        print "this is dh", dh
        i =0
        for rasilines in rashi[index]:
            for dibur in rasilines:
                while i< len(shas[index]):
                    if dibur in shas[index][i] or shas[index][i] in dibur:
                        if dh in dibur:
                            dafamud = convert_inf_to_daf(index)
                            print "this is the same dibur hamatchil", dafamud,'.', i
                            the_link = "Rashi on %s" % masechet + " " + dafamud + ":" + str(i+1)
                            links_list.append(the_link)
                            print the_link
                            #add to links_list
                        print "found" + str(index) + dibur
                        i+=1
                        break
                    elif fuzz.partial_ratio(dibur,shas[index][i]) >= 60 and fuzz.partial_ratio(dibur,shas[index][i]) >= 60:
                        if dh in dibur:
                            dafamud = convert_inf_to_daf(index)
                            print "this is the same dibur hamatchil", dafamud,'.', i
                            the_link = u"Rashi on %s" % masechet + " ", dafamud + ":" + str(i+1)
                            links_list.append(the_link)
                            print the_link
                            #add to links_list
                        print "found: " + str(index) + dibur + " in line: " + str(i)
                        i+=1
                        break
                    "did not find" + str(index) + dibur
                    i+=1


def get_comments():
    comments =[]
    rf = Ref('Rashi on %s' % masechet)
    tc = rf.text(lang='he').text
    for i,chap in enumerate(tc):
        for j,line in enumerate(chap):
            for k, com in enumerate(line):
                if isinstance(com, basestring) and len(com.strip()) > 0:
                    if i%2==0:
                        amud ="a"
                    else:
                        amud="b"
                    daf = (i/2) + 1
                    placement= u"Rashi on %s " % masechet+  str(daf)+amud+ ":"+ str(j+1) #+ ":" + str(k+1)
                    comments.append(placement)
    return comments


def double_dict(found_list):
    file = open("multiple.txt",'w')
    for i, diction in enumerate(found_list):
        print found_list[i]
        if found_list[i]["more_than_one"]=="TRUE":
            if found_list[i]["index"]== found_list[i-1]["index"]:
                for line in diction['lines']:
                    for pre_line in found_list[i-1]['lines']:
                            if line - pre_line > 0:
                                if len(found_list[i-1]['lines'])==1:
                                    file.write(str(found_list[i]["index"]) +" "+ found_list[i]['dh'].encode('utf-8') + " " + "the difference between current dh and previus is: " + str(line) + '\n')
                                    the_line= min(found_list[i]["lines"], key=lambda x:abs(x-found_list[i-1]["lines"][0]))
                                    link =  "Rashi on %s" % masechet +" " +convert_inf_to_daf(found_list[i]["index"]) +":"+ str(the_line+1)
                                    print link
                                    links_list.append(link)
                                    break
                                else:
                                    if found_list[i]["index"]== found_list[i+1]["index"]:
                                        print "line after ", found_list[i+1]["lines"], "line: ",found_list[i]["lines"]
            else:
                print str(found_list[i]["index"])+ " " +str(min(found_list[i]["lines"]))
                link = "Rashi on %s" % masechet +" " +convert_inf_to_daf(found_list[i]["index"]) +":"+ str(min(found_list[i]["lines"])+1)
                print "new link:", link
                links_list.append(link)
                break

if __name__ == '__main__':
    #refs = real_refs()
    index_to_daf()
    double(list_of_many_finds)
    print "length of links_list is:", len(links_list)
    double_dict(found_list)
    print "length of links_list is:", len(links_list)
    print "non match = ", non_match, "matched = ", matched, "too much = ", too_match, "count = " ,count
    comments= get_comments()
    print "comments", len(comments)
    diff= list(set(comments).difference(links_list))
    file =open('file.txt', 'w')
    file2 =open('file2.txt', 'w')
    for k in diff:
       file.write(k+"\n")
    print float(len(links_list))/float(len(comments))
    diff1 = list(set(links_list).difference(comments))
    acuracy = 1 -  float(len(diff1) /float(len(links_list)))
    print acuracy
    #for j in diff1:
       # file2.write( j+"\n")
    #compare.write("lowest ratio:" + str(i) +"    " + "matched:" +str(float(matched)/float(len(comments)))+ "  "+ "acuracy " +  str(acuracy))