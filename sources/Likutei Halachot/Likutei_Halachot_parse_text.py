# -*- coding: utf-8 -*-
import sys
import re
import csv
import codecs
import os
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
import functions
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
        paragraph = fix_parens(paragraph)
        paragraph = remove_nekudot_from_parenthetical_statements(paragraph)
        if "@SKIP@" not in paragraph:
            if "@TEXT@" in paragraph:
                for paragraph_split in colon_paragraph_break(invert_brackets(unmark(paragraph.strip()))):
                    if not_blank(paragraph_split.replace("(","").replace(")","")):
                        ois_box.append(paragraph_split+":" if paragraph_split[-1]!=":" else paragraph_split)
                """
                for paragraph_split in invert_brackets(unmark(paragraph.strip())).split(":"):
                    if not_blank(paragraph_split):
                        ois_box.append(paragraph_split+":")
                """
            #we don't append blanks or assorted non-text put in by publisher
            elif not_blank(paragraph) and is_text_segment(paragraph) and is_not_header(paragraph):
                #for these dosuments, the sections titles and אתיות don't have nikudot, so we parse by finding non-nikudot paragraphs
                #EXCEPT some random paragraphs in YD, these are dealt with with the length qualifyer
                #as a general outline to our approach, we append paragaphs to ois's, then ois's to sections, then sections to topics
                if "@SECTION@" in paragraph or (True!=wordHasNekudot(paragraph) and len(paragraph)<200 and no_ignore(paragraph)):
                    if "אות‏ ‏א" in paragraph:
                        continue
                    if len(ois_box)!=0:
                        section_box.append(ois_box)
                        ois_box = []
                    #if the word אות is not in the paragraph, it's a section header. If it does have the word אות, it's the begging of an ois
                    #EXCEPT second section of nederim in yoreh daya doesn't have the word אות , for that we check the length of the paragraph
                    #since all these paragraphs are less than 18 chars, and no section titles are that short (challah is the shortest, and is still included. HOWEVER, IF SECTIONS ARE MISSING I'd LOOK INTO THIS QUALIFIER, JUST TO MAKE SURE
                    if ("‏אות" not in paragraph and len(paragraph)>17 or "@@BREAK" in paragraph) or "NEWOIS" in paragraph or "@SECTION@" in paragraph:
                        if len(section_box)!=0:
                            topic_box.append(section_box)
                            section_box=[]
                        #to distinuish new topics from new sections, we keep a log of topics already parsed
                        if "NEWOIS" not in paragraph:
                            title = extract_title(paragraph) if "@SECTION@" not in paragraph else "אונאה"
                            if not_blank(title) and not_marker(title) and "שיך" not in title and "למה‏ ‏שכתו" not in title:
                                if "הקדמת" not in title:
                                    title = "הלכות"+" "+title.strip()
                                    title = remove_blanks(title)
                                print "TitleT: "+title
                                if title not in parsed_topics:
                                    #print str(index)+" "+''.join(title)
                                    if len(topic_box)!=0:
                                        order_box.append(topic_box)
                                        topic_box = []
                                    parsed_topics.append(title)
                #we don't want to append names of sections, ois's, or topics, so we only append if our paragraph is none of these, hence "else"
                else:
                    for paragraph_split in colon_paragraph_break(invert_brackets(unmark(paragraph.strip()))):
                        if not_blank(paragraph_split.replace("(","").replace(")","")):
                            ois_box.append(paragraph_split+":" if paragraph_split[-1]!=":" else paragraph_split)

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
                    #print str(index_0)+" "+str(index)+" "+str(index2)+" "+str(index3)
                    #print ois
                    if ois.count("(")!= ois.count(")"):

    return [parsed_topics, order_box]
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
    #we want to code seperate method for intro, in order to preserve integrety of index as compared to Shulchan Aruch
    #so we pop both title and text here
    print "deleting intro..."
    final_text[0][0].pop(0)
    final_text[0][1].pop(0)
    return final_text
def colon_paragraph_break(p):
    in_paren = False
    return_list = []
    last_insert = 0
    for index, char in enumerate(p):
        if char=="(":
            in_paren=True
        elif char==")":
            in_paren=False
        elif char ==":" and in_paren==False and len(p[last_insert:index+1])>1:
            return_list.append(p[last_insert:index+1])
            last_insert=index+1
    if len(p[last_insert:index+1])>1:
        return_list.append(p[last_insert:index+1])
    return return_list

def get_parsed_intro():
    file_parse_return = extract_text("orah haim a m.txt")
    intro =  file_parse_return[1][0][0][0]
    for item in intro:
        if False == item:
            index.remove(item)
    return intro
def remove_blanks(s):
    """
    word_list = s.split(" ")
    final_word_list = []
    for word in word_list:
        if not_blank(word) and word!=" " and True != re.match("s*",word) and word != '\xe2\x80\x8f':
            final_word_list.append(word)
    return ' '.join(final_word_list)
    """
    word_list = s.split(" ")
    final_word_list = []
    for word in word_list:
        if not_blank(word) and word!=" " and True != re.match("s*",word) and word != '\xe2\x80\x8f':
            final_word_list.append(word)
    return ' '.join(final_word_list)

def not_marker(s):
    return s == s.replace("BREAK","");

def is_not_header(s):
    if "הִלְכוֹת" in s or "הֲלָכָה" in s:
        if len(s)<110 and "נִכְלֶלֶ" not in s:
            return False
    return True
#this method spot-fixes glitches in the titles
def extract_title(s):
    ##remove markers
    #fix minor glitches:
    s= s.replace("ענין‏","").replace("  "," ").replace("@SECTION@","")
    #two entries that had a slight difference and should be together, both called birkat hatorah
    s = s.replace("\xe2\x80\x8f \xe2\x80\x8f \xe2\x80\x8f\xd7\xa7\xd7\xa8\xd7\x99\xd7\x90\xd7\xaa\xe2\x80\x8f \xe2\x80\x8f\xd7\x94\xd7\xaa\xd7\x95\xd7\xa8\xd7\x94\xe2\x80\x8f","\xe2\x80\x8f \xe2\x80\x8f\xd7\xa7\xd7\xa8\xd7\x99\xd7\x90\xd7\xaa\xe2\x80\x8f \xe2\x80\x8f\xd7\x94\xd7\xaa\xd7\x95\xd7\xa8\xd7\x94\xe2\x80\x8f")
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
    return s.replace("IGNORE","").replace("@TEXT@","")
def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def fix_parens(s):
    s = s.replace("( ","(")
    s = s.replace("((","(")
    s = s.replace("- ","-")
    s = s.replace(" -","-")
    return s
def invert_brackets(s):
    s = s.replace("[","@!@")
    s = s.replace("]","[")
    s = s.replace("@!@","]")
    return s
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

def remove_nekudot(word):
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
    return data.encode('utf-8')

def remove_nekudot_from_parenthetical_statements(s):
    words = s.split(' ')
    if len(words)>3:
        return s
    return_words = []
    words_with_nikkud = []
    words_without_nikkud = []
    in_paren_count = 0
    in_paren = False
    for word in words:
        if in_paren or "(" in word:
            in_paren = True
            if word!="(":
                in_paren_count+=1
            words_with_nikkud.append(word)
            words_without_nikkud.append(remove_nekudot(word))
            if ")" in word:
                in_paren = False
                if in_paren_count<=4:
                    #print "this is a quote "+' '.join(words_without_nikkud)
                    #print repr(' '.join(words_without_nikkud))
                    for paren_word in words_without_nikkud:
                        return_words.append(paren_word)
                else:
                    for paren_word in words_with_nikkud:
                        return_words.append(paren_word)
                in_paren_count=0
                words_with_nikkud=[]
                words_without_nikkud=[]
        else:
            return_words.append(word)
    return ' '.join(return_words)
def main():
    pass

if __name__ == "__main__":
    for oindex, order in enumerate(get_parsed_text()):
        for sindex, section in enumerate(order[1]):
            for cindex, chapter in enumerate(section):
                for iindex, ois in enumerate(chapter):
                    for pindex, paragraph in enumerate(ois):
                        print "ORDER "+str(oindex)+" SECION "+order[0][sindex]+" CHAPTER "+str(cindex)+" OIS "+str(iindex)+" PARAGRAPH "+str(pindex)
                        print paragraph

    #uncomment to see results
    """
    bad_paren = []

    for index, order in enumerate(get_parsed_text()):
        print "ORDER " + str(index)
        for index1, topic in enumerate(order[1]):
            print order[0][index1]
            for index2, section in enumerate(topic):
                for index3, ois in enumerate(section):
                    for index4, paragraph in enumerate(ois):
                        print str(index1) +" "+str(index2)+" "+str(index3)+" "+str(index4)
                        print paragraph
                        if paragraph.count("(")!=paragraph.count(")"):
                            bad_paren.append(str(index_0)+" "+str(index)+" "+str(index2)+" "+str(index3)+"\n"+ois)

    """
    orders = [ ["Orach Chaim","אורח חיים"],["Yoreh Deah","יורה דעה"],["Even HaEzer","אבן העזר"],["Choshen Mishpat","חושן משפט"]]
    html_str=""
    text = get_parsed_text()
    for x in range(4):
        for topic_index, topic in enumerate(text[x][1]):
            for chapter_index, chapter in enumerate(topic):
                for ois_index, ois in enumerate(chapter):
                    for paragraph_index, paragraph in enumerate(ois):
                        if paragraph.count("(")!=paragraph.count(")"):
                            html_str+=orders[x][1]+" "+text[x][0][topic_index]+" "+str(chapter_index+1)+" "+str(ois_index+1)+" "+str(paragraph_index+1)+"<br>"+paragraph.replace("(","<b><span style='font-size:35'>(</b></span>").replace(")","<b><span style='font-size:35'>)</b></span>")+"<hr>"
    Html_file= open("missing_parens.html","w")
    Html_file.write(html_str)
    Html_file.close()
    main()







