# -*- coding: utf-8 -*-

from sefaria.model import *
import os
import re
from sources.functions import *
global errors
errors = 0
from num2words import *

def check_in_order(line, value, type):
    poss_value = getGematria(line)
    if poss_value < value:
        print "out of order {}: {} comes after {}".format(type, poss_value, value)
        global errors
        errors += 1
    #if poss_value - value > 20:
    #    print "TOO LARGE DIFF ERROR: {} - {}".format(poss_value, value)
    return poss_value


def is_structure_marker(line):
    line = line.replace(u"פרק ", "").replace("(", "").replace(")", "")
    line = line.strip()
    right_num_of_words = len(line.split(" ")) <= 3
    right_num_of_chars = 4 <= len(line.replace(" ", "")) < 8
    return right_num_of_chars and right_num_of_words


def parse(file, type="body"):
    perek = 0
    pasuk = 0
    text_dict = {}
    with open(file) as f:
        lines = [line.replace("\n", "") for line in f if line.replace("\n", "").replace(" ", "")]
        for line_count, line in enumerate(lines):
            line = line.decode('utf-8')
            is_struct_marker = is_structure_marker(line)
            if line.startswith("@00") and is_struct_marker:
                line = line.replace(u"פרק", "")
                perek = check_in_order(line, perek, type="perek")
                #print "PEREK {}".format(perek)
                pasuk = 0
                if perek in text_dict.keys():
                    print "PEREK ERROR {}".format(perek)
                text_dict[perek] = {}
            elif line.startswith("@22") and is_struct_marker:
                pasuk = check_in_order(line, pasuk, type="pasuk in perek {}".format(perek))
                if pasuk in text_dict[perek].keys() and type == "footnotes":
                    pasuk += 0.1
                    text_dict[perek][pasuk] = []
                elif pasuk not in text_dict[perek].keys():
                    text_dict[perek][pasuk] = []
            elif line.startswith("@11"):
                line = line.replace("@11", "")
                text_dict[perek][pasuk].append(line)

    return text_dict


def extract_ftnote_text(ftnote_marker, ftnote_num, ftnotes):
    ftnote_comments = ftnotes[ftnote_num]
    ftnote_comment = u"<br/>".join(ftnote_comments)
    ftnote_marker = ftnote_marker.replace("*", "").replace(")", "").replace("@55", "")
    i_tag = u"<sup>{}</sup><i class='footnote'>{}</i>".format(ftnote_marker, ftnote_comment)
    return i_tag, ftnote_num


def insert_footnotes_into_base_text(base_text, footnotes):
    for perek, perek_text in base_text.items():
        ftnotes_in_perek = footnotes[perek]
        prev_ftnote_nums_in_perek = []
        for pasuk, pasuk_text in perek_text.items():
            for line_count, line in enumerate(pasuk_text):
                ftnote_marker_with_tags = re.findall(u"@\d\d[^\(]{1,3}\*?\)", line)
                for ftnote_marker in ftnote_marker_with_tags:
                    ftnote_num = getGematria(ftnote_marker)
                    prev_instances = [prev_num for prev_num in prev_ftnote_nums_in_perek if prev_num == ftnote_num]
                    for prev_instance in prev_instances:
                        ftnote_num += 0.1
                    if ftnote_num not in ftnotes_in_perek.keys():
                        print u"{} in perek {} pasuk {} in main file only".format(ftnote_marker, perek, pasuk)
                        global errors
                        errors += 1
                    else:
                        i_tag, ftnote_num = extract_ftnote_text(ftnote_marker, ftnote_num, ftnotes_in_perek)
                        prev_ftnote_nums_in_perek.append(int(ftnote_num))
                        base_text[perek][pasuk][line_count] = line.replace(ftnote_marker, i_tag)

    return base_text


def compare_dict_to_dict(base_text, comm_text):
    '''Iterate through all footnotes in footnote file looking for each one in main text footnotes.
     First, collect all footnotes in main text'''
    for perek in comm_text.keys():
        assert perek in base_text.keys()
        ftnote_count_in_main_file = 0
        ftnote_markers_in_main_file = []
        ftnotes_in_footnote_file = comm_text[perek].keys()
        for pasuk_num, pasuk_text in base_text[perek].items():
            for line_count, line in enumerate(pasuk_text):
                ftnote_markers_in_pasuk = re.findall(u"@\d\d[^\(]{1,3}\*?\)", line)
                for ftnote_marker in ftnote_markers_in_pasuk:
                    ftnote_num = getGematria(ftnote_marker)
                    #if ftnote_num not in ftnotes_in_footnote_file:line.startswith("@00")
                    #    print "{} NOT in footnotes file, but in main file in perek {}, pasuk {}".format()

                ftnote_markers_in_main_file += [getGematria(num) for num in ftnote_markers_in_pasuk]

        ftnote_count_in_main_file += len(ftnote_markers_in_main_file) #number of footnotes in main text in perek X, now we need to know how many footnotes are in the footnote file

        ftnote_count_in_footnote_file = len(ftnotes_in_footnote_file)
        if ftnote_count_in_footnote_file - ftnote_count_in_main_file > 0:
            for ftnote_num, ftnote_text in comm_text[perek].items():
                if int(ftnote_num) not in ftnote_markers_in_main_file:
                    global errors
                    errors += 1
                    print u"{} in perek {} in footnotes file only".format(ftnote_num, perek)


        if abs(ftnote_count_in_footnote_file - ftnote_count_in_main_file) > 0:
            print "IN PEREK {}".format(perek)
            print "Difference: {}".format(ftnote_count_in_footnote_file - ftnote_count_in_main_file)
            #print "Count in footnote file: {}".format(ftnote_count_in_footnote_file)
            #print "Count in main file: {}\n".format(ftnote_count_in_main_file)

def pre_parse(dir):
    files = os.listdir(dir)
    base = [file for file in files if "מרובע" in file]
    comm = [file for file in files if "הערות" in file]
    base_file = "{}/{}".format(dir, base[0])
    print base_file
    base_text = parse(base_file, "body")
    if comm != []:
        comm_file = "{}/{}".format(dir, comm[0])
        print comm_file
        comm_text = parse(comm_file, "footnotes")
        compare_dict_to_dict(base_text, comm_text)
        base_text = insert_footnotes_into_base_text(base_text, comm_text)
    return base_text


if __name__ == "__main__":
    SERVER = "http://localhost:8000"
    #add_term("Torah Temimah", u"תורה תמימה", "commentary_works", server=SERVER)
    torah_books = library.get_indexes_in_category("Torah")
    dirs = [dir for dir in os.listdir(".") if os.path.isdir(dir)]
    #create_complex_index_torah_commentary("Torah Temimah", u"תורה תמימה", server=SERVER)

    for dir in dirs:
        if dir not in torah_books:
            categories = ["Tanakh", "Commentary", "Torah Temimah", library.get_index(dir).categories[-1]]
            index = create_simple_index_many_to_one("Torah Temimah", u"תורה תמימה", dir, categories, server=SERVER)
        text_dict = pre_parse(dir)
    print "ERRORS {}".format(errors)