# -*- coding: utf-8 -*-
import re
#import data_utilities
import codecs
def fix_quotation_marks(string_list):
    return list(map((lambda x: x.replace("\xe2\x80\x9c","").replace("\xe2\x80\x9d","")),string_list))
def get_parsed_text():
    #returns array with the following structure
    # [ [Pesicha] , [Introduction], [ [Book 1], [Book 2], [Book 3], Book 4] ]
    final_text = []
    #first file contains intros and first maamar
    with open ("Ikkarim English-Volume 1.txt", "r") as myfile:
        file_text= fix_quotation_marks(myfile.readlines())
    intro_split = ''.join(file_text).split("INTRODUCTION")
    #seperate editors intro, start with 1 because 0 if publisher reference information
    joined_text = ''.join(intro_split[1:])
    split_text = re.split(r"(BOOK OF PRINCIPLES|BOOK ONE)", joined_text)

    #append editors intro
    final_text.append(remove_blank_paragraphs(split_text[0].split('\n')))

    #append forward
    final_text.append(remove_blank_paragraphs(''.join(intro_split[1].split("BY RABBI JOSEPH ALBO")[1]).split("\n")))

    split_text = ' '.join(split_text).split("BOOK ONE")
    #append introduction
    final_text.append(remove_blank_paragraphs(''.join(intro_split[2].split("BOOK ONE")[0]).split('\n')))

#final_text.append(remove_blank_paragraphs(split_text[1].split('\n')[1:]))
    maamarim = []
    #append book one
    maamarim.append(parse_book(split_text[2]))

    #book four is done seperately, since it spans two files.
    for x in range(2,4):
        with open ("Ikkarim English-Volume "+str(x)+".txt", "r") as myfile:
            file_text= remove_heading(''.join(myfile.readlines()))
        maamarim.append(parse_book( file_text))

    #book 4
    with open ("Ikkarim English-Volume 4.txt", "r") as myfile:
        file_text= remove_heading(''.join(myfile.readlines()))
    with open ("Ikkarim English-Volume 5.txt", "r") as myfile:
        file_text= file_text + remove_heading(''.join(myfile.readlines()).split("FINISH")[0])
    maamarim.append(parse_book( remove_heading(file_text)))
    final_text.append(maamarim)
    return final_text

def parse_book(book_string):
#returns [ [Intro], [ [Chapter 1], [Chapter 2]... ] ]
    return_list = []
    chapter_split = re.split("CHAPTER [0-9]{1,3}", book_string)
    if len( chapter_split[0].split("OBSERVATION"))>1:
        for item in chapter_split[0].split("OBSERVATION"):
            return_list.append(remove_blank_paragraphs(item.split('\n')))
    else:
        return_list.append(remove_blank_paragraphs( chapter_split[0].split('\n') ))
    chapters = []
    for chapter in chapter_split[1:]:
        chapters.append(remove_blank_paragraphs( chapter.split('\n') ))
    return_list.append(chapters)

    return return_list

def remove_blank_paragraphs(list):
    return_list = []
    for paragraph in list:
        if not_blank(paragraph):
            return_list.append(paragraph)
    return return_list

def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);

def remove_heading(s):
    return re.split("(BOOK (TWO|THREE|FOUR))|(General Index 565)",s)[-1]


text = get_parsed_text()
for index, p in enumerate( text[3][3][1]):
    print "CHAPTER: "+str(index)
    for index2, q in enumerate( p):
        print "PARAGRAPH: "+str(index2)
        print q
"""
for index, chapter in enumerate(text[0:2]):
    print "SECTION!",index
    for index3, paragraph in enumerate(chapter):
        print "PARAGRAPH",index3, paragraph
print text[2][0][0]

for index, chapter in enumerate(text[2][1]):
    print "CHAPTER "+str(index)
    for index1, paragraph in enumerate(chapter):
        print "P"+str(index1),paragraph

print "INTRO"
for index, p in enumerate(text[5][0]):
    print "PARAGRAPH" + str(index),p

print "OBSERVATION"
for index, p in enumerate(text[3][1]):
    print "PARAGRAPH" + str(index),p

print "CHAPTERS"
for index, chapter in enumerate(text[5][1]):
    print "!CHAPTER "+str(index)
    for index2, p in enumerate(chapter):
        print index2, p
"""