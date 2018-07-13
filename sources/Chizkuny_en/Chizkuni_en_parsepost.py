# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import unicodedata
import codecs
from bs4 import BeautifulSoup

books_of_Torah = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
def get_parsed_text():
    with open("Chizkuni - Munk (1).html", 'r') as myfile:
        text = ''.join(myfile.readlines())
    soup = BeautifulSoup(text, 'html.parser')
    spans = soup.find_all('span')
    text_complete= ""
    for s in spans:
        if s.get('style')=="font-weight:bold;":
            text_complete += "BOLD:"
        try:
            text_complete += ''.join(s.contents)
        except TypeError:
            text_complete+= ''.join(s.findAll(text=True))
    book_heads = ["BOLD:Parshat Sh\u2019mot","BOLD:Parshat Vayikra","BOLD:Parshat Bamidbar","BOLD:Parshat Devarim"]
    #seperate the comments into seperate elements
    comment_split = re.findall(r'BOLD:.*?(?=BOLD:)' ,text_complete)
    #combine comments split incorrectly, and takes out blanks
    #iterate multiple times to get all comments (some are skipped, since the array is edited as as being iterated through)
    for x in range(5):
        combine_comments(comment_split)
    #remove parsha headers and extra "BOLD:" tags
    for index, comment in enumerate(comment_split):
        comment_split[index] = re.sub(r'BOLD:Parshat.*?BOLD:', 'BOLD:',comment)
    for index, comment in enumerate(comment_split):
        comment_split[index]= re.sub("BOLD:(?=[A-Za-z ,]+)","",re.sub("^BOLD:","",re.sub("BOLD:Parshat [^א-ת]*","",comment)))
    #combine comments with no index with the comments preceding them
    indexed_comments = []
    for comment in comment_split:
        try:
            get_comment_index(comment)
            indexed_comments.append(comment)
        except AttributeError:
            if len(comment.replace("@SKIP@","")) == len(comment):
                indexed_comments[-1]+=comment
            else:
                indexed_comments[-1]+="<br>"+comment.replace("@SKIP@","")
    book_box = []
    all_books = []
    for comment in indexed_comments:
        if get_comment_index(comment)[0]==1 and get_comment_index(comment)[1]==1 and len(book_box)!=0:
            all_books.append(book_box)
            book_box = []
        book_box.append(comment)
    all_books.append(book_box)
    for book in all_books:
        for comment in book:
            print "P!: "+comment
    final_text = []
    misplaced = []
    for index, book in enumerate(all_books):
        last_perek = 0
        last_pasuk = 0
        for comment in book:
            comment_index = get_comment_index(comment)
            if last_pasuk > comment_index[1] and last_perek == comment_index[0]:
                misplaced.append(comment)
            else:
                last_perek = comment_index[0]
                last_pasuk = comment_index[1]
    for index, book in enumerate(all_books):
        book_array = make_perek_array(books_of_Torah[index])
        for comment in book:
            comment_index = get_comment_index(comment)
            try:
                book_array[comment_index[0]-1][comment_index[1]-1] = comment.split("BOLD:")
                """
                if last_perek > comment_index[0]:
                    misplaced.append(comment)
                else:
                    last_perek = comment_index[0]
                    last_pasuk = comment_index[1]
                """
            except IndexError:
                #a few typos in the file, corrected here
                comment = re.sub("^\d+[.,]\d+","",comment)
                if comment_index[0] == 13 and comment_index[1]==24 and index==0:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[13][23] = comment.split("BOLD:")
                elif comment_index[0] == 47 and comment_index[1]==34 and index==0:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[46][30] = comment.split("BOLD:")
                elif comment_index[0] == 2 and comment_index[1]==28 and index==1:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[1][24] = comment.split("BOLD:")
                elif comment_index[0] == 9 and comment_index[1]==38 and index==1:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[8][34] = comment.split("BOLD:")
                elif comment_index[0] == 119 and comment_index[1]==14 and index==1:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[18][13] = comment.split("BOLD:")
                elif comment_index[0] == 33 and comment_index[1]==33 and index==1:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[31][32] = comment.split("BOLD:")
                elif comment_index[0] == 24 and index==1:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[33][comment_index[1]-1] = comment.split("BOLD:")
                elif comment_index[0] == 40 and comment_index[1]==39 and index==1:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[39][37] = comment.split("BOLD:")
                elif comment_index[0] == 25 and comment_index[1]==19 and index==3:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[25][0] = comment.split("BOLD:")
                elif comment_index[0] == 10 and comment_index[1]==13 and index==4:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    #comment_cut = comment.split("BOLD:")
                    book_array[29][12] = comment.split("BOLD:")
                elif comment_index[0] == 30 and comment_index[1]==30 and index==4:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[29][19] = comment.split("BOLD:")
                elif comment_index[0] == 21 and comment_index[1]==30 and index==4:
                    comment = re.sub("^\d+[.,]\d+","",comment)
                    book_array[30][29] = comment.split("BOLD:")
                else:
                    print "ERROR!"
                    print str(index) +" "+str(comment_index[0]-1)+" "+str(comment_index[1]-1)
                    print comment

        for m in misplaced:
            print "MISPLACED! "+m

        final_text.append(book_array)

    #check to make sure commentary location matches index its placed in
    for book_index, book in enumerate(final_text):
        for perek_index, perek in enumerate(book):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    location = re.match("^\d+[.,]\d+",comment)
                    if location:
                        if int(re.split("[.,]",location.group())[0])-1 != perek_index or int(re.split("[.,]",location.group())[1])-1!=pasuk_index:
                            try:
                                final_text[book_index][int(re.split("[.,]",location.group())[0])-1][int(re.split("[.,]",location.group())[1])-1].append(re.sub("^\d+[.,]\d+","",comment))
                                del final_text[book_index][perek_index][pasuk_index][comment_index]
                            except IndexError:
                                print "ERROR! "+str(book_index)+" "+comment
                        else:
                            final_text[book_index][perek_index][pasuk_index][comment_index]= re.sub("^\d+[.,]\d+","",comment)
    #fix final stubs and remove extra spaces
    for book_index, book in enumerate(final_text):
        for perek_index, perek in enumerate(book):
            for pasuk_index, pasuk in enumerate(perek):
                commentary_box = []
                for comment in pasuk:
                    commentary_box.append(re.sub("^\. ","",remove_extra_space(comment)))
                final_text[book_index][perek_index][pasuk_index] = fix_stubs(commentary_box)
    """
    for book_index, book in enumerate(final_text):
        for perek_index, perek in enumerate(book):
            for pasuk_index, pasuk in enumerate(perek):
                print str(book_index)+" "+str(perek_index)+" "+str(pasuk_index)
                for comment in pasuk:
                    print "C!: "+comment
    """
    return final_text

def combine_comments(comment_split):
    for index, comment in enumerate(comment_split):
        if not re.match("BOLD:([א-ת ]+|\d+[\.,]\d)", comment):
            if not_blank(re.sub("BOLD:","",comment)):
                comment_split[index-1] += comment
            comment_split.remove(comment)
        if len(remove_extra_space(comment).split(" "))<5:
            if not_blank(re.sub("BOLD:","",comment)):
                comment_split[index+1] = comment + comment_split[index+1]
            try:
                comment_split.remove(comment)
            except ValueError:
                pass
    return comment_split
def fix_stubs(pasuk):
    return_comments = []
    for comment in pasuk:
        #fix some spot errors
        comment = re.sub("[\*\-]","",re.sub("^-\d+","",comment))
        if re.match(u"^[\u0590-\u05ff \ufb1d-\ufb4f'\\?!\.\\\",]+",comment):
            return_comments.append(comment)
        else:
            try:
                return_comments[-1]+=comment
            except:
                return_comments.append(comment)
    return return_comments

def get_comment_index(comment):
    #check for skip flag:
    if "@SKIP@" in comment:
        raise AttributeError()
    string_index= re.split("[,.]",re.match("^\d+[,.]\d+",comment).group())
    return [int(string_index[0]),int(string_index[1])]
    
def remove_html(s):
    #take out html script
    s = re.sub("<.*?>","",s)
    return s;

def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array

def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);

def remove_extra_space(s):
    s = s.replace(u'\xa0', u' ')
    while "  " in s:
        s = s.replace("  "," ")
    return s

get_parsed_text()

for index, book in enumerate(get_parsed_text()[1:3]):
    index+=1
    version = {
        'versionTitle': 'Chizkuni, translated and annotated by Eliyahu Munk',
        'versionSource': 'http://www.urimpublications.com/Merchant2/merchant.mv?Screen=PROD&Store_Code=UP&Product_Code=Chizkuni&Category_Code=bd',
        'language': 'en',
        'text': book
    }
    post_text_weak_connection('Chizkuni, '+books_of_Torah[index], version)

