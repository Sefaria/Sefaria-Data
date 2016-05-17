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

#pattern = re.compile('@\d\d\s?[\[\(].*?[\]\)]')
#pattern = re.compile('(@\d\d)+[\[\(].{1,4}[\]\)]')
pattern =  re.compile('(@?\d\d)+[\[\(][^&]{1,4}[\]\)]')
curr_siman = 0
curr_seif_katan = 0
text = {}
 

def replaceWithHTMLTags(line, helek, siman_num):
    line = line.decode('utf-8')
    line = line.replace('%(', '(%')
    line = line.replace('(#', '(%')
    line = line.replace("*(", "(*")
    line = line.replace('(*', '(%')
    commentaries = ["Drisha", "Prisha", "Darchei Moshe", "Hagahot", "Beit_Yosef", "Bach", "Mystery"]
    matches_array = [re.findall(u"\[[\u05D0-\u05EA]{1,4}\]", line), re.findall(u"\([\u05D0-\u05EA]{1,4}\)", line),
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



def create_indexes(eng_helekim, heb_helekim, eng_title, heb_title):
  #helek, siman, seif_katan
  commentary = SchemaNode()
  commentary.add_title(eng_title, 'en', primary=True)
  commentary.add_title(heb_title, 'he', primary=True)
  commentary.key = eng_title.replace(" ","")

  for count, helek in enumerate(eng_helekim):
      helek_node = JaggedArrayNode()

      helek_node.add_title(helek, 'en', primary=True)
      helek_node.add_title(heb_helekim[count], 'he', primary=True)
      helek_node.key = helek.replace(" ","")
      helek_node.depth = 3
      helek_node.addressTypes = ["Integer", "Integer", "Integer"]
      if helek == "Choshen Mishpat":
          helek_node.sectionNames = ["Siman", "Seif", "Seif Katan"]
      else:
          helek_node.sectionNames = ["Siman", "Seif Katan", "Paragraph"]
      commentary.append(helek_node)
  commentary.validate()
  index = {
    "title": eng_title,
    "categories": ["Halakhah", "Tur and Commentaries"],
    "schema": commentary.serialize()
    }
  post_index(index)

def smallFont(line):
  if line.find("@66") >= 0 and line.find("@77") >= 0 and line.find("@77") > line.find("@66"):
      line = line.replace("@66", "<small>")
      line = line.replace("@77", "</small>")
  return line

def checkCSV(helek, commentator, siman, num_comments, prev_line):
    csvf = open('comments_per_siman.csv', 'r')
    csvreader = csv.reader(csvf, delimiter=',')
    first_words = " ".join(prev_line.split(" ")[0:4])
    for row in csvreader:
        if helek == row[0] and commentator == row[1] and str(siman) == row[2]:
            if commentator == "Drisha" and helek == "Choshen Mishpat":
                continue
            if abs(num_comments-int(row[3])) > 0 and abs(num_comments-int(row[3])) <= 5:
                num_comments_mismatch_small.write(helek.replace(" ","_")+";"+commentator+";Siman:"+str(siman)+";"+commentator+"_Count;"+str(num_comments)+";Tur_Count:"+row[3]+';First_Words_Prev_Line:'+first_words+'\n')
            elif abs(num_comments-int(row[3])) > 5:
                num_comments_mismatch_big.write(helek.replace(" ","_")+";"+commentator+";Siman:"+str(siman)+";"+commentator+"_Count;"+str(num_comments)+";Tur_Count:"+row[3]+';First_Words_Prev_Line:'+first_words+'\n')
    csvf.close()

def dealWithTwoSimanim(text):
    if text[0] == ' ':
        text = text[1:]
    if text[len(text)-1] == ' ':
        text = text[:-1]
    if len(text.split(" "))>1:
        if len(text.split(" ")[0]) > 0 and len(text.split(" ")[1]) > 0:
            text = text.split(" ")[0]
    return text


def divideUpLines(text, commentator):
    tag = " "
    text_array = []
    if commentator == "Bach":
        tag = "@77"
    elif commentator == "Bi" or commentator == "Beit Yosef":
        tag = "@66"
    if text.find(tag)==0:
        text = text.replace(tag,"", 1)
    text_array = text.split(tag)
    for i in range(len(text_array)):
        text_array[i] = [removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], text_array[i])]
    return text_array

def parse_text(helekim, files, commentator):
  store_this_line = ""
  bach_bi_lines = ""
  for count, helek in enumerate(helekim):
    if helek == "Choshen Mishpat":
        continue
    curr_siman = 0
    curr_seif_katan = 0
    f = open(files[count])
    text[helek] = {}
    seif_list = []
    actual_seif_katan = 0
    for line in f:
      actual_line = line
      line = line.replace("@44","").replace("@55","")
      line = line.replace("\n", "")
      #deal with case where seif katan marker is separated from comment and is on line before comment
      if len(store_this_line)>0:
        line = store_this_line+line
        store_this_line = ""
      if len(line)<15 and line.find("@22")==-1:
        store_this_line = line
        continue
      if len(line) < 4:
        continue
      if line[0] == ' ':
        line = line[1:]
      #deal with strange cases first
      if (line.find("@22סי'")>=0 or line.find("@22סי")>=0) and len(line.split(" "))>4: #ONLY DRISHA ON YOREH DEAH
          try:
            nothing, siman, line = line.split("@",2)
          except:
            pdb.set_trace()
          siman = siman.replace("22סי'","").replace("22סי","")
          siman = dealWithTwoSimanim(siman)
          poss_siman = getGematria(siman)
          if poss_siman == curr_siman - 2 and siman.find('ה')>=0:
                poss_siman += 3
          elif poss_siman <= curr_siman:
                print 'siman issue'
                siman_file.write(helek+","+commentator+","+str(poss_siman)+","+str(curr_siman)+","+actual_line+"\n")
          if curr_siman > 0:
                checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]), prev_line)
          curr_siman = poss_siman
          curr_seif_katan = 0
          actual_seif_katan = 0
          text[helek][curr_siman] = []
          seif_list = []
          line = "@"+line
      if (line.find("@66@22")>=0 or line.find("@77@22")>=0) and len(line.split(" "))>4:  #ONLY Beit Yosef and BACH ON YOREH DEAH
          beg, line = line.split(" ", 1)
          beg = beg.replace("@66@22","")
          beg = dealWithTwoSimanim(beg)
          poss_siman = getGematria(beg)
          if poss_siman == curr_siman - 2 and beg.find('ה')>=0:
                poss_siman += 3
          elif poss_siman <= curr_siman:
                print 'siman issue'
                siman_file.write(helek+","+commentator+","+str(poss_siman)+","+str(curr_siman)+","+actual_line+"\n")

          if len(bach_bi_lines)>0 and (commentator == "Bach" or commentator == "Beit Yosef"):
              text[helek][curr_siman] = divideUpLines(bach_bi_lines, commentator)
              bach_bi_lines = ""

          if curr_siman > 0:
                checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]), prev_line)
          bach_bi_lines = ""
          curr_siman = poss_siman
          curr_seif_katan = 1
          actual_seif_katan = 1
          text[helek][curr_siman] = []
          seif_list = []
          seif_list.append(curr_seif_katan)
          bach_bi_lines += line
          continue
      #now process three typical cases: Siman header, Comment with Seif Katan marker, Comment without Seif Katan marker
      if pattern.match(line):
        seif_katan = pattern.match(line).group(0)
        temp_arr = re.split('\d\d', seif_katan)
        seif_katan = temp_arr[len(temp_arr)-1]
        poss_seif_katan = getGematria(removeAllStrings(["[","]","(",")"], seif_katan))
        if poss_seif_katan == curr_seif_katan-2 and seif_katan.find('ה')>=0:
            poss_seif_katan += 3
        elif poss_seif_katan < curr_seif_katan:
            seif_file.write(helek+","+commentator+","+str(curr_siman)+","+str(poss_seif_katan)+","+str(curr_seif_katan)+","+actual_line+"\n")
        if poss_seif_katan in seif_list:
            seif_katan = pattern.match(line).group(0)
            marked_seif_katan = seif_katan[0:len(seif_katan)-1]+'*'+seif_katan[len(seif_katan)-1]
            line = line.replace(seif_katan, marked_seif_katan)
        else:
            seif_katan = pattern.match(line).group(0)
            line = line.replace(seif_katan, "")
            seif_list.append(poss_seif_katan)

        bach_bi_lines += line
        line = smallFont(line)
        line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], line)
        curr_seif_katan = poss_seif_katan
        actual_seif_katan += 1
        curr_seif_katan_line = actual_line
        if line.find("@")>=0:
            print '@'
        text[helek][curr_siman].append([line])
      elif line.find("@22סי'")>=0 or (line.find("@22")<4 and line.find("@22")>=0 and len(line.split(" ")) < 4):
            line = line.replace("@22סי' ", "").replace("@22ס' ","").replace("@22סי ","")
            line = line.replace("@22", "").replace("@66","").replace("@77","")
            if len(bach_bi_lines)>0 and (commentator == "Bach" or commentator == "Beit Yosef"):
                text[helek][curr_siman] = divideUpLines(bach_bi_lines, commentator)
                bach_bi_lines = ""

            if curr_siman > 0:
                checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]), prev_line)
            if len(line) > 0:
                line = dealWithTwoSimanim(line)
                poss_siman = getGematria(line)
            else:
                poss_siman += 1
            if poss_siman == curr_siman - 2 and line.find('ה')>=0:
                poss_siman += 3
            elif poss_siman <= curr_siman:
                print 'siman issue'
                siman_file.write(helek+","+commentator+","+str(poss_siman)+","+str(curr_siman)+","+actual_line+"\n")

            prev_siman = curr_siman
            bach_bi_lines=""
            curr_siman = poss_siman
            curr_seif_katan = 0
            actual_seif_katan = 0
            seif_list = []
            text[helek][curr_siman] = []
      else: #just add it to current seif katan
        if commentator == "Prisha" or commentator == "Drisha":
            line = smallFont(line)
            line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], line)
            if line.find("@")>=0:
                print line.find("@")
                pdb.set_trace()
            if len(text[helek][curr_siman]) == 0:
                text[helek][curr_siman].append([line])
            else:
                len_text = len(text[helek][curr_siman])
                text[helek][curr_siman][len_text-1][0] += "<br>"+line
        else:
            bach_bi_lines += line
      prev_line = actual_line
    if len(bach_bi_lines)>0 and (commentator == "Bach" or commentator == "Beit Yosef"):
        text[helek][curr_siman] = divideUpLines(bach_bi_lines, commentator)
        bach_bi_lines = ""

def post_commentary(commentator):
    commentator = commentator.replace("Bi", "Beit Yosef")
    links = []
    for helek in text:
    	if helek == "Orach Chaim":
    		continue
        text_array = convertDictToArray(text[helek])
        send_text = {
            "text": text_array,
            "language": "he",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
            "versionTitle": helek+", Vilna, 1923"
        }
        post_text(commentator+",_"+helek, send_text)
        for siman_num, siman in enumerate(text_array):
            for seif_katan_num, seif_katan in enumerate(text_array[siman_num]):
                tur_end = "Tur,_"+str(helek)+"."+str(siman_num+1)+".1"
                commentator_end = commentator+",_"+helek+"."+str(siman_num+1)+"."+str(seif_katan_num+1)+".1"
                links.append({'refs': [tur_end, commentator_end], 'type': 'commentary', 'auto': 'True', 'generated_by': commentator+"choshenmishpat"})
    post_link(links)


if __name__ == "__main__":
  import csv
  global siman_file
  global seif_file    
  siman_file = open('siman_probs.csv', 'a')
  seif_file = open('seif_probs.csv', 'a')
  num_comments_mismatch_small = open('num_comments_mismatch_small_diff.csv', 'a')
  num_comments_mismatch_big = open('num_comments_mismatch_big_diff.csv', 'a')
  eng_helekim = ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]
  heb_helekim = [u"אורח חיים", u"יורה דעה", u"אבן העזר", u"חושן משפט"]
  if sys.argv[1] == 'Drisha':
    files_helekim = ["Orach_Chaim/drisha orach chaim helek a.txt", "yoreh deah/drisha yoreh deah.txt",
   "Even HaEzer/drisha even haezer.txt"]
    #create_indexes(eng_helekim, heb_helekim, "Drisha", u"דרישה")
    parse_text(eng_helekim, files_helekim, "Drisha")
    post_commentary("Drisha")
  elif sys.argv[1] == 'Prisha':
    files_helekim = ["Orach_Chaim/prisha orach chaim.txt", "yoreh deah/prisha yoreh deah.txt",
   "Even HaEzer/prisha even haezer.txt"]
    create_indexes(eng_helekim, heb_helekim, "Prisha", u"פרישה")
    parse_text(eng_helekim, files_helekim, "Prisha")
    post_commentary("Prisha")
  elif sys.argv[1] == 'BeitYosef':
    print SEFARIA_SERVER
    files_helekim = ["Orach_Chaim/Beit Yosef orach chaim helek a.txt", "yoreh deah/Beit Yosef yoreh deah.txt", "Even HaEzer/Bi Even HaEzer.txt"]
    #create_indexes(eng_helekim, heb_helekim, "Beit Yosef", u'בית יוסף')
    parse_text(eng_helekim, files_helekim, "Beit Yosef")
    post_commentary("Beit Yosef")
  elif sys.argv[1].find("Bach")>=0:
    files_helekim = ["Orach_Chaim/bach orach chaim helek a.txt", "yoreh deah/bach yoreh deah.txt", "Even HaEzer/bach even haezer.txt"]
    create_indexes(eng_helekim, heb_helekim, "Bach", u'ב"ח')
    parse_text(eng_helekim, files_helekim, "Bach")
    pdb.set_trace()
    post_commentary("Bach")
  elif sys.argv[1].find("DarcheiMoshe")>=0:
    files_helekim = ["Orach_Chaim/darchei moshe orach chaim.txt", "yoreh deah/darchei moshe yoreh deah.txt", "Even HaEzer/darchei moshe even haezer.txt"]
    #create_indexes(eng_helekim, heb_helekim, "Darchei Moshe", u"דרכי משה")
    parse_text(eng_helekim, files_helekim, "Darchei Moshe")
    #post_commentary("Darchei Moshe")
  num_comments_mismatch_small.close()
  num_comments_mismatch_big.close()
  siman_file.close()
  seif_file.close()
  