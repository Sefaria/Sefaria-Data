# -*- coding: utf-8 -*-
import re
import csv
import codecs
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
    order_box = []
    title=""
    for index, paragraph in enumerate(text):
        #we don't append blanks or assorted non-text put in by publisher
        if not_blank(paragraph) and is_text_segment(paragraph):
            #for these dosuments, the sections titles and אתיות don't have nikudot, so we parse by finding non-nikudot paragraphs
            #EXCEPT some random paragraphs in YD, these are dealt with with the length qualifyer
            #as a general outline to our approach, we append paragaphs to ois's, then ois's to sections, then sections to topics
            if True!=wordHasNekudot(paragraph) and len(paragraph)<200 and no_ignore(paragraph):
                if len(ois_box)!=0:
                    section_box.append(ois_box)
                    ois_box = []
                #if the word אות is not in the paragraph, it's a section header. If it does have the word אות, it's the begging of an ois
                #EXCEPT second section of nederim in yoreh daya doesn't have the word אות , for that we check the length of the paragraph
                #since all these paragraphs are less than 18 chars, and no section titles are that short (challah is the shortest, and is still included. HOWEVER, IF SECTIONS ARE MISSING I'd LOOK INTO THIS QUALIFIER, JUST TO MAKE SURE
                if "‏אות" not in paragraph and len(paragraph)>17 or "@@BREAK" in paragraph:
                    if len(section_box)!=0:
                        topic_box.append(section_box)
                        section_box=[]
                    #to distinuish new topics from new sections, we keep a log of topics already parsed
                    title = extract_title(paragraph)
                    if not_blank(title) and not_marker(title):
                        if "הקדמת" not in title:
                            title = ("הלכות"+" "+title).replace("  "," ")
                        if title not in parsed_topics:
                            #print str(index)+" "+''.join(title)
                            if len(topic_box)!=0:
                                order_box.append(topic_box)
                                topic_box = []
                            parsed_topics.append(title)
            #we don't want to append names of sections, ois's, or topics, so we only append if our paragraph is none of these, hence "else"
            else:
                ois_box.append(unmark(paragraph))

#still have to store last entry in text, since hitting a title calls the append chain and there's no title after the last title.
    section_box.append(ois_box)
    topic_box.append(section_box)
    order_box.append(topic_box)
    if title not in parsed_topics:
        parsed_topics.append(title)
#some empty topic still crept in...
    for index, topic in enumerate(order_box):
        if len(topic)==0:
            order_box.pop(index)
            parsed_order_topics.pop(index)
    return [parsed_topics, order_box]
"""USEFUL PRINT METHOD TO CHECK RESULTS
    for index_0, topic in enumerate(topic_box):
    for index, box in enumerate(topic):
    for index2, text in enumerate(box):
    for index3, ois in enumerate(text):
    print str(index_0)+" "+str(index)+" "+str(index2)+" "+str(index3)
    print ois
    """
def get_parsed_text():
    OC_files = ["orah haim a m.txt","orah haim b m.txt","orah haim c m.txt"]
    YD_files = ["yore deha a m.txt", "yore deha b m.txt"]
    OH_files = ["even aezel m.txt"]
    CM_files = ["hoshen mishpat a m.txt","hoshen mishpat b m.txt"]
    order_files = [OC_files, YD_files, OH_files, CM_files]
    parsed_order_text = []
    parsed_order_topics = []
    final_text = []

    for indexo, order in enumerate(order_files):
        for file_name in order:
            file_parse_return = extract_text(file_name)
            for index, topic_title in enumerate(file_parse_return[0]):
                print str(indexo)+" "+str(index) + "         " + topic_title
                parsed_order_topics.append(topic_title)
            for topic in file_parse_return[1]:
                parsed_order_text.append(topic)
        final_text.append([parsed_order_topics,parsed_order_text])
        parsed_order_topics = []
        parsed_order_text = []
    #can't find bug, but Introduction for some reason is cut out.
    #final_text[0][0].insert(0,"הקדמת המחבר")
    #we want to code seperate method for intro, in order to preserve integrety of index as compared to Shulchan Aruch
    #so we pop both title and text here
    print "deleting intro..."
    final_text[0][0].pop(0)
    final_text[0][1].pop(0)
    return final_text

def get_parsed_intro():
    file_parse_return = extract_text("orah haim a m.txt")
    intro =  file_parse_return[1][0][0][0]
    for item in intro:
        if False == item:
            index.remove(item)
    return intro

def not_marker(s):
    return s == s.replace("BREAK","");

#this method spot-fixes glitches in the titles
def extract_title(s):
    ##remove markers
    #fix minor glitches:
    s= s.replace("ענין‏","").replace("  "," ")
    #two entries that had a slight difference and should be together, both called birkat hatorah
    s = s.replace("\xe2\x80\x8f \xe2\x80\x8f \xe2\x80\x8f\xd7\xa7\xd7\xa8\xd7\x99\xd7\x90\xd7\xaa\xe2\x80\x8f \xe2\x80\x8f\xd7\x94\xd7\xaa\xd7\x95\xd7\xa8\xd7\x94\xe2\x80\x8f","\xe2\x80\x8f \xe2\x80\x8f\xd7\xa7\xd7\xa8\xd7\x99\xd7\x90\xd7\xaa\xe2\x80\x8f \xe2\x80\x8f\xd7\x94\xd7\xaa\xd7\x95\xd7\xa8\xd7\x94\xe2\x80\x8f")
    # has two section: ברכת הריח וברכת הודאה and ברכת הודאה that should be together
    #s = s.replace("\\20\\u200F\\u05D1\\u05E8\\u05DB\\u05EA\\u200F\\20\\u200F\\u05D4\\u05E8\\u05D9\\u05D7\\u200F\\20\\u200F\\u05D5\\u05D1\\u05E8\\u05DB\\u05EA\\u200F\\20\\u200F\\u05D4\\u05D5\\u05D3\\u05D0\\u05D4","\\20\\u05D1\\u05E8\\u05DB\\u05EA\\20\\u05D4\\u05D5\\u05D3\\u05D0\\u05D4")‏
    #s = s.replace('\\u200F\\20\\u200F\\u05D1\\u05E8\\u05DB\\u05EA\\u200F\\20\\u200F\\u05D4\\u05E8\\u05D9\\u05D7\\u200F\\20\\u200F\\u05D5\\u05D1\\u05E8\\u05DB\\u05EA\\u200F\\20\\u200F\\u05D4\\u05D5\\u05D3\\u05D0\\u05D4\\u200F','%u200F%20%u200F%u05D1%u05E8%u05DB%u05EA%u200F%20%u200F%u05D4%u05D5%u05D3%u05D0%u05D4')
    #s = s.replace("%u200F%u05D1%u05E8%u05DB%u05EA%u200F%20%u200F%u05D4%u05E8%u05D9%u05D7%u200F%20%u200F%u05D5","")
    s.replace("U+200F","")
    s = s.replace("‏ ‏ברכת‏ ‏הריח‏ ‏ו","")
    if  "פרשיות" in s and "ארבע" in s:
        return ' '.join(s.strip().split(" "))
    if "הקדמת‏" in s and "המחבר" in s:
        return ' '.join(s.strip().split(" "))
    #in chosen mishpat, there are two topic titles דיינים‏ and דינים which seem to refer to same topic...we chose דינים just because
    #it's easier to fix that way (we can run a blanket replace on דינים since this is likely found in other contexts)
    if "דיינים" in s:
        s=s.replace("דיינים" ,"דינים")
    return ' '.join((s.strip()).split(" ")[:-1])

def is_text_segment(s):
    non_text = ["בס\"ד", "לקּוּטֵי‏ ‏הֲלָכוֹ‏ת","לִקּוּטֵי‏ ‏הֲלָכוֹת‏","‏ליקוטי‏ ‏הלכות‏", "מתוך אוצר ספרי ברסלב להורדה של אור הגנוז ברסלב", "orhaganuz"]
    for entry in non_text:
        if entry in s:
            return False
    return True;
#IGNORE tags are paragraphs without nikudot that are not section headers
def no_ignore(s):
    return s.replace("IGNORE","")==s
def unmark(s):
    return s.replace("IGNORE","")
def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
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

#uncomment to see results
for index, order in enumerate(get_parsed_text()):
    print "ORDER " + str(index)
    for index1, topic in enumerate(order[1]):
        print order[0][index1]
        for index2, section in enumerate(topic):
            for index3, ois in enumerate(section):
                for index4, paragraph in enumerate(ois):
                    print str(index1) +" "+str(index2)+" "+str(index3)+" "+str(index4)
                    print paragraph
