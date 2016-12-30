# -*- coding: utf-8 -*-
import re
#import data_utilities
import codecs
import chardet

#from sources import functions

#returns list with this format:
# [ [peticha], [intro], [ [maamar 1], [maamar 2],[maamar 3],[maamar 4] ] where the intro is broken into paragraphs and each maamar is broken into chapters and paragraphs. Note that the maamar intros/haaras are kept as chapters and handled in the posting script.
def get_parsed_text():
    
    final_text = []
    #first file contains intro and first maamar
    with open ("IkkarimHebrew-Volume1.txt", "r") as myfile:
        file_text= myfile.readlines()
    #element 0 is peticha
    peticha_paragraphs = re.split("  "+"[א-ת]{1,3}"+" ",file_text[0])
    peticha = []
    for p in peticha_paragraphs:
        for p2 in re.findall("פרק"+".*?\.",p) if re.findall("פרק"+".*?\.",p) else [p]:
            peticha.append(p2)
    final_text.append(peticha)

    text = parse_text_segment(file_text[1])
    #first chapter is intro, this get appended seperately. last paragraph is really subject of first maamar
    intro = remove_blanks_from_chapter_list( [text[0][:-1]] )
    final_text.append(intro[0])
    #the remaining elements comprise the first maamar.
    #each maamar has a heading and chapters, but these are differenciated in the posting method
    maamarim = []
    maamar_box = []
    #as mentioned earlier, the last element in the introduction is the heading of the first maamar. This is put in a list because some headers are more than one paragraph
    maamar_box.append([text[0][-1]])
    for chapter in text[1:]:
        maamar_box.append(chapter)
    maamar_box = remove_blanks_from_chapter_list(maamar_box)
    maamarim.append(maamar_box)
    maamar_box = []
    #append remaining maamarim:
    for x in range(2,4):
        with open ("IkkarimHebrew-Volume"+str(x)+".txt", "r") as myfile:
            file_text= myfile.readlines()
        for line in file_text:
            if not_blank(line):
                maamar_box.append(line)
        maamar_box = parse_text_segment_2(maamar_box)
        maamarim.append(maamar_box)
        maamar_box = []
    #the fourth maamar is split into two files, so they're parsed seperately
    for x in range(4,6):
        with open ("IkkarimHebrew-Volume"+str(x)+".txt", "r") as myfile:
            file_text= myfile.readlines()
        for line in file_text:
            if not_blank(line):
                maamar_box.append(line)
    maamar_box = parse_text_segment_2(maamar_box)
    maamarim.append(maamar_box)
    maamar_box = []

    final_text.append(maamarim)
    return final_text


def remove_blanks_from_chapter_list(list):
    """
    for chapter in list:
        for paragraph in chapter:
            if not_blank(paragraph) != True:
                chapter.remove(paragraph)
            if len(chapter) == 0:
                list.remove(chapter)
                """
    return list

def parse_text_segment(text):
    return_array = []
    chapters = re.split("  "+"פרק",text)
    for chapter in chapters:
        return_array.append(re.split("  "+"[א-ת]{1,3}"+" ",chapter)[1:])
    return return_array

#we need another parse method for maamar 2-4, since they are formatted differenently
def parse_text_segment_2(text):
    return_array = []
    chapter_box  = []
    for line in text:
        if re.match("א"+ " ",line) and len(chapter_box)!=0:
            #last element in chapter box is always the header for the next chapter
            return_array.append(chapter_box[:-1])
            chapter_box = []
        if "@NEWCHAPTER@" in line:
            return_array.append(chapter_box)
            chapter_box = []
        else: #we want to take out first "word", which is just a letter at the beggining of each paragraph
            line = take_out_first_word(line)
            chapter_box.append(line)
    #add final chapter
    return_array.append(chapter_box)
    #take out first "chapter", header put in by publisher
    return return_array[1:]

def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);

def take_out_first_word(s):
    return ' '.join(s.strip().split(' ')[1:])

text = get_parsed_text()

for p in text[0]:
    print "P:"+p
"""
for index, maamar in enumerate(text[1]):
    print "MAAMAR "+str(index)
    for index2, chapter in enumerate(maamar):
        print "CHAPTER "+str(index2)
        for index3, next in enumerate(chapter):
            print "NEXT "+str(index3)
            print next

print "this is the introduction:"
for paragraph in text[0]:
    print paragraph

print "this is the first maamar subject"
print text[1][0]

print "this is the first maamar contents"
for chapter in text[1][1]:
    for paragraph in chapter:
        print paragraph
"""

