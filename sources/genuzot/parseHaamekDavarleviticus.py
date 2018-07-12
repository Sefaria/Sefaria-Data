__author__ = 'eliav'
# -*- coding: utf-8 -*-
import helperFunctions as Helper
import hebrew
import re
import json


def open_file():
    with open("source/haamek_davar_Leviticus.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text

def run_parser(text):
    parsed_text=[]
    cur_chapter = 1
    cur_verse = 1
    text=re.sub(ur'@20.{6}','',text)
    chapters = re.split(ur'@10([^@]*)', text)
    for chapter_num, chapter in zip(chapters[1::2], chapters[2::2]):
        if chapter_num.strip() != '':
            chapter_num = re.sub("[\(,\)]", "", chapter_num)
            cur_chapter = hebrew.heb_string_to_int(chapter_num.strip())
            parsed_chapter = []
            expand_list_assign(parsed_text, cur_chapter - 1, parsed_chapter)
            psukim = re.split(ur'@11([^@]*)', chapter)
            for pasuk_num, pasuk in zip(psukim[1::2], psukim[2::2]):
                 if pasuk.strip() != '':
                    parsed_verse = []
                    pasuk_num = re.sub("[\(,\)]", "", pasuk_num)
                    cur_verse = hebrew.heb_string_to_int(pasuk_num.strip())
                    expand_list_assign(parsed_chapter, cur_verse - 1, parsed_verse)
                    DH = pasuk.split(ur'@12')[1:]
                    for dibur_hamatchil in DH:
                        comments = dibur_hamatchil.split('@33')[1:]
                        comment1=""
                        for comment in comments:
                            if comment.strip() != '':
                                key = re.split(ur'@00', comment)
                                if len(key) > 1:
                                    comment = '<b>' + key[0] + '</b>' + key[1]
                                    comment1 = comment1 + comment
                        parsed_verse.append(comment1)
    return parsed_text





def expand_list_assign(list, index, value):
    """since we are dealing with a sparse list, we need to grow the list size according to the index"""
    if index > len(list) - 1:
        list.extend([[]] * (index + 1 - len(list)))
    list[index] = value

def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": "Haamek Davar on Leviticus",
        "versionTitle": "Vilna : 1879",
        "versionSource": "http://babel.hathitrust.org/cgi/pt?id=uc1.31158011185906",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Haamek_Davar_on_Leviticus.json", 'w') as out:
        json.dump(text_whole, out)

def run_post_to_api():
    with open("preprocess_json/Haamek_Davar_on_Leviticus.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Haamek Davar on Leviticus", file_text, False)

if __name__ == '__main__':
    text=open_file()
    parsed=run_parser(text)
    save_parsed_text(parsed)
    run_post_to_api()
    #print parsed[0][0][0]
    #print parsed[0][1][0]
    #print parsed[0][0][1]
    #print len(parsed)
