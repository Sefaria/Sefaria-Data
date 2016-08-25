# -*- coding: utf-8 -*-
import re
from fuzzywuzzy import fuzz
import csv
#from get_section_titles import get_he_section_title_array
#from get_section_titles import standardize_title


def extract_text(file_input):
    with open (file_input, "r") as myfile:
        text=myfile.readlines()
    
    parsed_topics = []

    paragraph_box = []
    ois_box = []
    section_box = []
    topic_box=[]
    
    for index, line in enumerate(text):
        #we don't append blanks or assorted non-text put in by publisher
        if not_blank(line) and is_text_segment(line):
            #for these dosuments, the sections titles and אתיות don't have nikudot, so we parse by finding non-nikudot lines
            #EXCEPT some random paragraphs in YD, these are dealt with with the length qualifyer
            #as a general outline to our approach, we append paragaphs to ois's, then ois's to sections, then sections to topics
            if True!=wordHasNekudot(line) and len(line)<200:
                ois_box.append(paragraph_box)
                #if the word אות is not in the line, it's a section header. If it does have the word אות, it's the begging of an ois
                #EXCEPT second section of nederim in yoreh daya doesn't have the word אות , for that we check the length of the line
                #since all these lines are less than 18 chars, and no section titles are that short (challah is the shortest, and is still included. HOWEVER, IF SECTIONS ARE MISSING I'd LOOK INTO THIS QUALIFIER, JUST TO MAKE SURE
                if "‏אות" not in line and len(line)>17:
                    section_box.append(ois_box)
                    ois_box=[]
                    #to distinuish new topics from new sections, we keep a log of topics already parsed
                    title = extract_title(line)
                    if title not in parsed_topics:
                        for word in title:
                            print "index is"+str(index)+" title is"+ word
                        print line
                        print
                        topic_box.append(section_box)
                        section_box = []
                        parsed_topics.append(title)
                paragraph_box = []
        #we sdon't want to append names of sections, ois's, or topics, so we only append if our line is none of these, hence "else"
            else:
                paragraph_box.append(line)
"""
    for index_0, topic in enumerate(topic_box):
        for index, box in enumerate(topic):
            for index2, text in enumerate(box):
                for index3, ois in enumerate(text):
                    print str(index_0)+" "+str(index)+" "+str(index2)+" "+str(index3)
                    print ois
"""
def extract_title(s):
    #fix minor glitch:
    if  "פרשיות" in s and "ארבע" in s:
        return s.strip().split(" ")
    if "הקדמת‏" in s and "המחבר" in s:
        return s.strip().split(" ")
#in chosen mishpat, there are two topic titles דיינים‏ and דינים which seem to refer to same topic...we chose דינים just because
#it's easier to fix that way (we can run a blanket replace on דינים since this is likely found in other contexts)
    if "דיינים" in s:
        s.replace("דיינים" ,"דינים")
    return (s.strip()).split(" ")[:-1]
#this method spot-fixes glitches in the titles

def is_text_segment(s):
    non_text = ["בס\"ד", "‏ליקוטי‏ ‏הלכות‏", "מתוך אוצר ספרי ברסלב להורדה של אור הגנוז ברסלב", "orhaganuz"]
    for entry in non_text:
        if entry in s:
            return False
    return True;

def not_blank(s):
    return (len(s.replace(" ","").replace("\n","").replace("\r","").replace("\t",""))!=0);
#taken from functions file
def wordHasNekudot(word):
    data = word.decode('utf-8')
    data = data.replace(u"\u05B0", "")
    data = data.replace(u"\u05B1", "")
    data = data.replace(u"\u05B2", "")
    data = data.replace(u"\u05B3", "")
    data = data.replace(u"\u05B4", "")
    data = data.replace(u"\u05B5", "")
    data = data.replace(u"\u05B6", "")
    data = data.replace(u"\u05B7", "")
    data = data.replace(u"\u05B8", "")
    data = data.replace(u"\u05B9", "")
    data = data.replace(u"\u05BB", "")
    data = data.replace(u"\u05BC", "")
    data = data.replace(u"\u05BD", "")
    data = data.replace(u"\u05BF", "")
    data = data.replace(u"\u05C1", "")
    data = data.replace(u"\u05C2", "")
    data = data.replace(u"\u05C3", "")
    data = data.replace(u"\u05C4", "")
    return data != word.decode('utf-8')


OC_files = ["orah haim a m.txt","orah haim b m.txt","orah haim c m.txt"]
YD_files = ["yore deha a m.txt", "yore deha b m.txt"]
OH_files = ["even aezel m.txt"]
CM_files = ["hoshen mishpat a m.txt","hoshen mishpat b m.txt"]

for file_str in CM_files:
    extract_text(file_str)


    