# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
import csv

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud

def howBig(dict):  #figure out how many slots are actually filled in a dict in which some are filled, and some aren't
    return len(extractFilled(dict))

def extractFilled(dict):
  new_dict = {}
  for slot in dict:
     if dict[slot] != [""]:
        new_dict[slot] = dict[slot]
  return new_dict

def addHeader(line, header, just_saw_00, will_see_00):
  if just_saw_00 == True:
      just_saw_00 = False
      line = "<b>"+header+"</b><br>"+line
  if will_see_00 == True:
      just_saw_00 = True
      will_see_00 = False
  return line, just_saw_00, will_see_00


def replaceWithHTMLTags(line):
    line = line.decode('utf-8')
    line = line.replace('%(', '(%')
    line = line.replace('(#', '(%')
    line = line.replace("*(", "(%")
    line = line.replace('(*', '(%')
    commentaries = ["Drisha", "Darchei Moshe", "Hagahot", "Beit_Yosef", "Bach", "Mystery"]
    matches_array = [re.findall(u"\[[\u05D0-\u05EA]{1,4}\]", line),
                        re.findall(u"\(%[\u05D0-\u05EA]{1,4}\)", line), re.findall(u"\s#[\u05D0-\u05EA]{1,4}", line),
                        re.findall(u"\{[\u05D0-\u05EA]{1,4}\}",line), re.findall(u"\|[\u05D0-\u05EA]{1,4}\|", line),
                        re.findall(u"<[\u05D0-\u05EA]{1,4}>",line)]
    for commentary_count, matches in enumerate(matches_array):
        how_many_shams = 0
        for order_count, match in enumerate(matches):
            if match == u"(שם)" or match == u"[שם]":
                how_many_shams += 1
                continue
            HTML_tag =  '<i data-commentator="'+commentaries[commentary_count]+'" data-order="'+str(order_count+1-how_many_shams)+'"></i>'
            line = line.replace(match, HTML_tag)
    return line

def lookForHeader(line, curr_header, just_saw_00, will_see_00):
  if line.find("@00") >= 0 and len(line.split(" ")) >= 2:
      skip = True
      start = line.find("@00")
      end = len(line)
      header = line[start:end]
      line = line.replace(header, "")
      header = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"], header)
      if len(line) > 1:
          will_see_00 = True
      else:
          just_saw_00 = True
  else:
      skip = False
      header = curr_header
  return line, header, just_saw_00, will_see_00, skip


def parse_text(commentators, files):
  choshen_mishpat = {}
  for commentator in commentators:
    curr_siman = 0
    file = files[commentator]
    seif_list = []
    curr_seif = 0
    choshen_mishpat[commentator] = {}
    num_seifim = 0
    append_to_next_line = ""
    just_saw_00 = False
    will_see_00 = False
    header = ""
    for line in file:
        actual_line = line
        line = replaceWithHTMLTags(line)
        line = line.replace("\n", "")
        if line == u"""@22סי' """:
            continue
        if len(line) == 0:
            continue

        line, header, just_saw_00, will_see_00, skip = lookForHeader(line, header, just_saw_00, will_see_00)
        if skip == True:
          skip = False
          continue

        if line.find("@22") >= 0 and len(line) > 13:
            line = line.replace(u"@22סי' ", "").replace(u"@22ס' ", "").replace(u"@22סי ", "")
            if line[0] == ' ':
                line = line[1:]
            first_space = line.find(' ')
            first_word = line[0:first_space]
            line = line.replace(first_word,"")
            first_word = first_word.replace(u"@22סי' ", "").replace(u"@22ס' ", "").replace(u"@22סי ", "")
            first_word = first_word.replace("@22", "").replace("@66", "").replace("@77", "")

            #if curr_siman > 0:
            #    checkCSV(helek, commentator, curr_siman, len(choshen_mishpat[commentator][curr_siman]), prev_line)
            if len(first_word) > 0:
                first_word = dealWithTwoSimanim(first_word)
                poss_siman = getGematria(first_word)
            else:
                poss_siman += 1
            if poss_siman == curr_siman - 2 and first_word.find(u'ה') >= 0:
                poss_siman += 3
            elif poss_siman <= curr_siman:
                print 'siman issue'
                pdb.set_trace()
                #siman_file.write(helek + "," + commentator + "," + str(poss_siman) + "," + str(
                #    curr_siman) + "," + actual_line + "\n")

            prev_siman = curr_siman
            curr_siman = poss_siman
            curr_seif = 0
            actual_seif = 0
            seif_list = []
            choshen_mishpat[commentator][curr_siman] = {}


            try:
                seif = re.findall(u"\([\u05D0-\u05EA]+\)", line)[0]
            except:
                pdb.set_trace()
            temp_arr = re.split('\d\d', seif)
            seif = temp_arr[len(temp_arr) - 1]
            poss_seif = getGematria(removeAllStrings(["[", "]", "(", ")"], seif))
            if poss_seif == curr_seif - 2 and seif.find(u'ה') >= 0:
                poss_seif += 3
            elif poss_seif < curr_seif:
                print 'seif prob'
                pdb.set_trace()
                seif_file.write(
                    helek + "," + commentator + "," + str(curr_siman) + "," + str(poss_seif) + "," + str(
                        curr_seif) + "," + actual_line + "\n")

            if howBig(choshen_mishpat[commentator][curr_siman]) > tur[curr_siman]:
                print 'too many seifim'
                #pdb.set_trace()



            if poss_seif - curr_seif > 1:
                amt = poss_seif - curr_seif - 1
                for i in range(amt):
                    print 'skipping in '+str(curr_siman)+' curr_seif = '+str(curr_seif)+' poss_seif = '+str(poss_seif)
                    choshen_mishpat[commentator][curr_siman][i+1+curr_seif] = [""]

            seif = re.findall(u"\([\u05D0-\u05EA]+\)", line)[0]
            add_after = ""
            if seif.find("@77") >= 0:
                add_after += "@77"
            if seif.find("@66") >= 0:
                add_after += "@66"
            if seif.find("@88") >= 0:
                add_after += "@88"
            line = line.replace(seif, "")
            line = add_after + line
            line = removeAllStrings(["@11", "@22", "@33", "@44", "@55", "@66", "@77", "@87", "@88", "@89", "@98"],
                                    line)

            line, just_saw_00, will_see_00 = addHeader(line, header, just_saw_00, will_see_00)
            choshen_mishpat[commentator][curr_siman][poss_seif] = [line]


            curr_seif = poss_seif
            curr_seif_line = actual_line
            if line.find("@") >= 0:
                print '@'
                pdb.set_trace()
            prev_seif = curr_seif

        elif len(re.findall(u"\([\u05D0-\u05EA]+\)", line)) > 0 and line.find(re.findall(u"\([\u05D0-\u05EA]+\)", line)[0]) < 10:
            seif = re.findall(u"\([\u05D0-\u05EA]+\)", line)[0]
            temp_arr = re.split('\d\d', seif)
            seif = temp_arr[len(temp_arr) - 1]
            poss_seif = getGematria(removeAllStrings(["[", "]", "(", ")"], seif))
            if poss_seif == curr_seif - 2 and seif.find(u'ה') >= 0:
                poss_seif += 3
            elif poss_seif < curr_seif:
                print 'seif prob'
                poss_seif = curr_seif + 1
            try:
              if howBig(choshen_mishpat[commentator][curr_siman]) > tur[curr_siman]:
                print 'too many seifim'
                #pdb.set_trace()
            except:
              pdb.set_trace()


            if poss_seif - curr_seif > 1:
                amt = poss_seif - curr_seif - 1
                for i in range(amt):
                    print 'skipping in '+str(curr_siman)+' curr_seif = '+str(curr_seif)+' poss_seif = '+str(poss_seif)
                    choshen_mishpat[commentator][curr_siman][i+1+curr_seif] = [""]




            seif = re.findall(u"\([\u05D0-\u05EA]+\)", line)[0]
            add_after = ""
            if seif.find("@77") >= 0:
                add_after += "@77"
            if seif.find("@66") >= 0:
                add_after += "@66"
            if seif.find("@88") >= 0:
                add_after += "@88"
            line = line.replace(seif, "")
            line = add_after + line
            line = removeAllStrings(["@11", "@22", "@33", "@44", "@55", "@66", "@77", "@87", "@88", "@89", "@98"],
                                    line)

            line, just_saw_00, will_see_00 = addHeader(line, header, just_saw_00, will_see_00)
            choshen_mishpat[commentator][curr_siman][poss_seif] = [line]

            curr_seif = poss_seif
            curr_seif_line = actual_line

            line = line.replace('@','')
            prev_seif = curr_seif



        elif line.find(u"@22סי'") >= 0 or (
                    line.find("@22") < 4 and line.find("@22") >= 0 and len(line.split(" ")) < 4):
            line = line.replace(u"@22סי' ", "").replace(u"@22ס' ", "").replace(u"@22סי ", "")
            line = line.replace("@22", "").replace("@66", "").replace("@77", "")

            #if curr_siman > 0:
            #    checkCSV(helek, commentator, curr_siman, len(choshen_mishpat[commentator][curr_siman]), prev_line)
            if len(line) > 0:
                line = dealWithTwoSimanim(line)
                poss_siman = getGematria(line)
            else:
                poss_siman += 1
            if poss_siman == curr_siman - 2 and line.find(u'ה') >= 0:
                poss_siman += 3
            elif poss_siman <= curr_siman:
                print 'siman issue'
                pdb.set_trace()
                siman_file.write(helek + "," + commentator + "," + str(poss_siman) + "," + str(
                    curr_siman) + "," + actual_line + "\n")

            prev_siman = curr_siman
            curr_siman = poss_siman

            curr_seif = 0
            actual_seif = 0
            seif_list = []
            choshen_mishpat[commentator][curr_siman] = {}
        else:  # just add it to current seif katan
            line = removeAllStrings(["@11", "@22", "@33", "@44", "@55", "@66", "@77", "@87", "@88", "@89", "@98"],
                                    line)
            try:
                choshen_mishpat[commentator][curr_siman][curr_seif][0] += line
            except:
                pdb.set_trace()
        prev_line = actual_line
  return choshen_mishpat

def getAllSimanim(title, start_at = 1):
    ref = title+" "+str(start_at)
    tur = {}
    siman = 1
    tur_siman_info = open('tur_siman_info.csv', 'w')
    while ref is not None:
        if ref.find("Choshen")==-1:
            break
        print ref
        siman_text = get_text_plus(ref, "http://ste.sefaria.org/")
        while ref.find(str(siman)) == -1:
            print 'siman not found'
            print ref
            print siman
            siman += 1
        tur[siman] = siman_text['he']
        tur_siman_info.write(str(siman)+","+str(len(tur[siman]))+"\n")
        ref = siman_text['next']
        siman += 1
    tur_siman_info.close()
    return tur

def dealWithTwoSimanim(text):
    if text[0] == ' ':
        text = text[1:]
    if text[len(text) - 1] == ' ':
        text = text[:-1]
    if len(text.split(" ")) > 1:
        if len(text.split(" ")[0]) > 0 and len(text.split(" ")[1]) > 0:
            text = text.split(" ")[0]
    return text

def splitSeifKatan(array):
    new_array = []
    for i in range(len(array)):
        if array[i][0] == "":
            new_array.append([""])
        else:
            array_to_append = array[i][0].split(': ')
            array_to_append.pop(len(array_to_append)-1)
            for j in range(len(array_to_append)):
                array_to_append[j] = array_to_append[j] + ':'
            new_array.append(array_to_append)

    return new_array

def post_text_and_link(choshen_mishpat, commentators):
    links = []
    for commentator in commentators:
        print commentator
        choshen_mishpat[commentator] = convertDictToArray(choshen_mishpat[commentator])
        for siman_num, siman in enumerate(choshen_mishpat[commentator]):
            if len(choshen_mishpat[commentator][siman_num]) == 0:
                continue
            choshen_mishpat[commentator][siman_num] = convertDictToArray(choshen_mishpat[commentator][siman_num])
            choshen_mishpat[commentator][siman_num] = splitSeifKatan(choshen_mishpat[commentator][siman_num])

            for seif_num, seif in enumerate(choshen_mishpat[commentator][siman_num]):
                for seif_katan_num, seif_katan in enumerate(choshen_mishpat[commentator][siman_num][seif_num]):
                    if choshen_mishpat[commentator][siman_num][seif_num][seif_katan_num] != "":
                        tur_end = "Tur,_Choshen_Mishpat."+str(siman_num+1)+"."+str(seif_num+1)
                        commentator_end = commentator+",_Choshen_Mishpat."+str(siman_num+1)+"."+str(seif_num+1)+"."+str(seif_katan_num+1)

                        links.append({'refs': [tur_end, commentator_end], 'type': 'commentary', 'auto': 'True', 'generated_by': commentator+"choshenmishpat"})
        send_text = \
        {
                "text": choshen_mishpat[commentator],
                "versionTitle": "Tur Choshen Mishpat: Vilna, 1923",
                "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
                "language": "he"
        }
        post_text(commentator+",_Choshen_Mishpat", send_text)
        post_link(links)





def getTurFile(file):
    csvf = open(file, 'r')
    tur = {}
    csvreader = csv.reader(csvf, delimiter=',')
    for row in csvreader:
        tur[int(row[0])] = int(row[1])
    return tur


def loadFiles(commentators):
    files = {}
    for commentator in commentators:
        array = []
        for ext in ["1a", "1b", "2a", "2b"]:
            open_file = open("Choshen Mishpat/"+commentator+" choshen mishpat "+ext+".txt")
            for line in open_file:
                array.append(line)
        files[commentator] = array
    return files


if __name__ == "__main__":
    global helek, tur, pattern
    commentators = ["Beit Yosef"]
    #tur = getAllSimanim("Tur,_Choshen_Mishpat", 1)
    tur = getTurFile('tur_siman_info.csv')
    files = loadFiles(commentators)
    choshen_mishpat = parse_text(commentators, files)
    post_text_and_link(choshen_mishpat, commentators)
