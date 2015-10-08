# -*- coding: utf8 -*-
__author__ = 'eliav'
import re
import sys
import os
from fuzzywuzzy import fuzz
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew
import json
masechet = str(sys.argv[1])
min_ratio = int(sys.argv[2])
step = int(sys.argv[3])
commentator = str(sys.argv[4])
if "_" in masechet:
    masechet = re.sub("_", " ", masechet)
else:
    masechet
masechet_he = Index().load({"title":masechet}).get_title("he")
masechet_he= re.sub(" ","_",masechet_he.strip())
rashi = TextChunk(Ref("{} on {}".format(commentator, masechet)), "he").text
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


def convert_daf_to_index(daf,amud):
   if amud=="a":
       index =(daf*2)-2
   elif amud =="b":
       index =(daf*2)-1
   return index


def shas_dafs_daf():
    build_rashi = []
    for daf_num,  daf in enumerate(shas):
        dafs =[]
        for line in daf:
            lines=[]
            dafs.append(lines)
        build_rashi.append(dafs)
    print len(build_rashi)
    print build_rashi
    return build_rashi


def index_to_daf():
    for daf_num,  daf in enumerate(shas):
        rashi_daf = rashi[daf_num]
        for rashi_line in rashi_daf:
            for rashi_dh in rashi_line:
                dh = re.split(ur"(?:-|–)",rashi_dh)[0]
                match(dh,shas[daf_num],daf_num,rashi_dh)


def read_rashi():
    for f in os.listdir(u'%s' % commentator):
        if masechet_he in f:
            pf = os.path.join(u'%s' % commentator, f)
            print pf
            split = re.split("_",f.strip())
            if "_" in masechet_he:
                daf_he =  split[2]
                amud_he = split[3][0]
            else:
                daf_he =  split[1]
                amud_he = split[2][0]
            daf =hebrew.heb_string_to_int(daf_he)
            if amud_he ==u'א':
                amud= "a"
            elif amud_he ==u'ב':
                amud="b"
            else:
                print "we have a problam"
            index = convert_daf_to_index(daf,amud)
            print index
            print daf
            print amud
            with open(pf, 'r') as filep:
                file_text = filep.read()
                list = re.split("\n",file_text)
                for liner in list:
                    if "-" in liner or "–" in liner:
                        #print line
                        pass
                    if commentator in "Rashi":
                        dh = re.split("(?:-|–)",liner)[0]
                    elif "Tosafot" in commentator :
                        dh = re.split(ur"\.",liner)[0]
                    match(dh.decode('utf-8'),shas[index],index,liner.decode('utf-8'))


def match(dh,shas,index,dibur, ratio=100):
    found_dict = {}
    list_of_found_links = []
    found_dict['index']= index
    found_dict['dh'] = dh
    found_dict['dibbur'] = dibur
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
        link = "Rashi on %s" % masechet +" " + dafamud +":"+ str(the_line+1) + " " + dh
        add_rashi(index,dibur,the_line)
        links_list.append(link)
        print "found!!",dafamud,":", the_line," ", dh
        matched+=1
        found_list.append(found_dict)
    if found == 0:
        if ratio > min_ratio:
            match(dh,shas, index,dibur, ratio-step)
        else:
            list_of_found_links.append(-1)
            found_dict['lines']=list_of_found_links
            found_dict["more_than_one"]="FALSE"
            print len(dh)
            non_match += 1
            found_list.append(found_dict)


def get_comments():
    comments =[]
    rf = Ref('{} on {}'.format(commentator, masechet))
    tc = rf.text(lang='he').text
    for i,chap in enumerate(tc):
        for j,line in enumerate(chap):
            for k, com in enumerate(line):
                if isinstance(com, basestring) and len(com.strip()) > 0:
                    dafamud=convert_inf_to_daf(i)
                    dh = re.split(ur"(?:-|–)",com)[0]
                    placement= u"{} on {} ".format(commentator, masechet) + dafamud + ":" + str(j+1) + " " + dh
                    comments.append(placement)
    return comments


def add_rashi(index, dh, line):
    rashis[index][line].append(dh)


def double_dict(found_list):
    file = open("multiple.txt",'w')
    for i, diction in enumerate(found_list):
        print found_list[i]
        if found_list[i]["more_than_one"]=="TRUE":
            if found_list[i]["index"]== found_list[i+1]["index"]:
                next_line = found_list[i+1]['lines']
                if len(found_list[i+1]['lines'])==1:
                        found_list[i]['lines'] = [j for j in found_list[i]['lines'] if j <= next_line[0]]
                        print "new found list" , found_list[i]['lines']
            if found_list[i]["index"]== found_list[i-1]["index"]:
                #for line in diction['lines']:
                    pre_line = found_list[i-1]['lines']
                    print "pre_lines", pre_line
                    if len(found_list[i-1]['lines'])==1:
                        lines = [j for j in found_list[i]['lines'] if j >= pre_line[0]]
                        if len(lines)!=0:
                            print "lines", lines
                            file.write(str(found_list[i]["index"]) +" "+ found_list[i]['dh'].encode('utf-8') + " " + "the difference between current dh and previus is: " + str(lines) + '\n')
                            #if len(lines) ==1:
                            the_line= min(lines, key=lambda x:x-pre_line[0])
                            found_list[i]['lines'] =[the_line]
                            link =  "{} on {}".format(commentator, masechet) +" " +convert_inf_to_daf(found_list[i]["index"]) +":"+ str(the_line+1) + " " + found_list[i]["dh"]
                            add_rashi(found_list[i]["index"],found_list[i]["dibbur"],the_line)
                            print link
                            found_list[i]["more_than_one"]="FALSE"
                            links_list.append(link)
                        else:
                            print "no answer " +  str(found_list[i]["index"])+   found_list[i]['dh'].encode('utf-8')
                    else:
                        if found_list[i]["index"]== found_list[i+1]["index"]:
                            print "line after ", found_list[i+1]["lines"], "line: ",found_list[i]["lines"]
            else:
                if len(found_list[i]["lines"])>0:
                    print str(found_list[i]["index"])+ " " +str(min(found_list[i]["lines"]))
                    link = "{} on {}".format(commentator, masechet) +" " +convert_inf_to_daf(found_list[i]["index"]) +":"+ str(min(found_list[i]["lines"])+1)
                    print "new link:", link
                    found_list[i]["more_than_one"]="FALSE"
                    links_list.append(link)


def book_record():
    return {
        "title": '%s' % commentator,
        "titleVariants": ["%s" % commentator],
        "heTitle": '%s' % Index().load({"title":commentator}).get_title("he"),
        "heTitleVariants" :['%s' % Index().load({"title":commentator}).get_title("he")],
        "sectionNames": ["", ""],
        "categories": ['Commentary'],
    }


def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": '%s' % commentator ,
        "versionTitle": "Wikisource " +commentator,
        "versionSource":  "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/{}_on_{}.json".format(commentator,masechet), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/{}_on_{}.json".format(commentator, masechet), 'r') as filep:
        file_text = filep.read()
    mas = re.sub("_"," ", masechet.strip())
    Helper.postText("{} on {}".format(commentator, masechet) , file_text, False)


def post_logs():
    log =open("../../Match Logs/Talmud/{}/log_{}_{}.txt".format(masechet,masechet,commentator),"w")
    for i, diction in enumerate(found_list):
         if len(found_list[i]["lines"])==0:
            log.write("did not find daf: "+ convert_inf_to_daf(found_list[i]["index"]) + " dh: " + found_list[i]["dh"].encode('utf-8') + "\n" + "text: \n" + found_list[i]["dibbur"].encode('utf-8') + "\n" )

if __name__ == '__main__':
    rashis = shas_dafs_daf()
    read_rashi()
   # index_to_daf()
    print "length of links_list is:", len(links_list)
    double_dict(found_list)
    print "placed", len(links_list), "of the %s's" % commentator
    comments= get_comments() #get real rashi's
    print "full number of %s's is:" % commentator, len(comments)
    print "found too much:", len([i for i in found_list if i['more_than_one']=='TRUE']), "did not match at all:", non_match
    diff1 = list(set(links_list).difference(comments))
    file =open('file.txt', 'w')
    for k in diff1:
     file.write(k.encode('utf-8')+"\n")
    print "placed: " + str(round(float(len(links_list))/float(len(comments)),2)*100) +"%"
    acuracy = 1 -  float(len(diff1) /float(len(links_list)))
    print "acuracy: "+ str(round(acuracy,2)*100) + "%"
    print links_list[0], comments[0]
    #with open("testing.txt", "a") as myfile:
     #   myfile.write("min ratio: "+ str(min_ratio)+ "," + "step: "+ str(step)+ "," + "placed: "+ str(round(float(len(links_list))/float(len(comments)),2)*100) +"%" + "," + "accuracy: " + str(round(acuracy,2)*100) + "%" )
    save_parsed_text(rashis)
    run_post_to_api()
    post_logs()