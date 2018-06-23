# -*- coding: utf-8 -*-

import helperFunctions as Helper
import json
import re
import hebrew


def book_record():
    return {
        "title": 'Haamek Davar',
        "titleVariants": ["hanatziv on the tora", "Haamek Davar on the tora"],
        "heTitle": 'העמק דבר',
        "heTitleVariants" :['הנצ"יב על התורה', 'העמק דבר על התורה'],
        "sectionNames": ["", ""],
        "categories": ['Commentary'],
    }


def open_file():
    with open("source/haamek_davar.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


### in work
def list_tags(text):
    data = re.findall(r'@[0-9][0-9]', text)
    tags_list = dict((x, data.count(x)) for x in data)
    return tags_list


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
                comments = pasuk.split('@33')[1:]
                for comment in comments:
                    if comment.strip() != '':
                        key = re.split(ur'@00', comment)
                        if len(key) > 1:
                            comment = '<b>' + key[0] + '</b>' + key[1]
                        parsed_verse.append(comment)
    return parsed_text


def expand_list_assign(list, index, value):
    """since we are dealing with a sparse list, we need to grow the list size according to the index"""
    if index > len(list) - 1:
        list.extend([[]] * (index + 1 - len(list)))
    list[index] = value


""" Saves a text to JSON """

def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Haamek Davar on Genesis',
        "versionTitle": "Presburg : A. Schmid, 1842",
        "versionSource": "http://www.worldcat.org/title/perush-radak-al-ha-torah-sefer-bereshit/oclc/867743220",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Haamek_Davar_on_Genesis.json", 'w') as out:
        json.dump(text_whole, out)

def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Haamek_Davar_on_Genesis.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Haamek Davar on Genesis", file_text, False)


""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    text=open_file()
    #print run_parser(text)[0][0][0][0]
    parsed=run_parser(text)
    save_parsed_text(parsed)
    #print "posting "+name
    run_post_to_api()
