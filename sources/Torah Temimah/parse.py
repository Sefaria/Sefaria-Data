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
                if "@33" in line and "@11" in line:
                    line = line.replace("@11", "<b>").replace("@33", "</b>")
                tags_to_change = re.findall("@\d\d[\[\(].*?[\]\)]@\d\d", line)
                for tag_to_change in tags_to_change:
                    if "@66" in tag_to_change and "@77" in tag_to_change:
                        changed_tag = tag_to_change.replace("@66", "").replace("@77", "")
                    elif "@44" in tag_to_change and "@55" in tag_to_change:
                        changed_tag = tag_to_change.replace("@44", "").replace("@55", "")
                    else:
                        raise ValueError

                    line = line.replace(tag_to_change, changed_tag)
                text_dict[perek][pasuk].append(line)

    return text_dict


def extract_ftnote_text(ftnote_marker, ftnote_num, ftnotes):
    ftnote_comments = ftnotes[ftnote_num]
    ftnote_comment = u"<br/>".join(ftnote_comments)
    ftnote_comment = ftnote_comment.replace("@11", "")
    ftnote_marker = ftnote_marker.replace("*", "").replace(")", "").replace("@55", "").replace("@77", "")
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
                        base_text[perek][pasuk][line_count] = base_text[perek][pasuk][line_count].replace(ftnote_marker, i_tag)

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
    base_text = parse(base_file, "body")
    if comm != []:
        comm_file = "{}/{}".format(dir, comm[0])
        comm_text = parse(comm_file, "footnotes")
        compare_dict_to_dict(base_text, comm_text)
        base_text = insert_footnotes_into_base_text(base_text, comm_text)
    return base_text


def make_and_post_links():
    torah_books = library.get_indexes_in_category("Torah")
    torah_temimah_on_torah_books = ["Torah Temimah on Torah, {}".format(book) for book in torah_books]
    refs = []
    generic_link = {"generated_by": "", "type": "Commentary", "auto": True, "refs": []}
    links = []

    for base, comm in zip(torah_books, torah_temimah_on_torah_books):
        refs = create_links_many_to_one(comm, base)
        for ref_pair in refs:
            generic_link["refs"] = ref_pair
            links.append(dict(generic_link))

    post_link(links, server="http://draft.sefaria.org")


def make_and_post_intro(send_text):
    perek = 0
    intro = {}
    with open("Genesis/intro.txt") as file:
        for line in file:
            line = line.replace("\n", "")
            if line.startswith("@00פרק"):
                perek += 1
                assert perek not in intro
                intro[perek] = []
            elif line.startswith("@00"):
                line = removeAllTags(line)
                line = "<b>" + line + "</b>"
                intro[perek].append(line)
            elif line.startswith("@11"):
                line = removeAllTags(line)
                intro[perek].append(line)
    intro = convertDictToArray(intro)
    send_text["text"] = intro
    #post_text("Torah Temimah on Torah, Introduction", send_text, server="http://draft.sefaria.org")



if __name__ == "__main__":

    cs = CategorySet({"sharedTitle": "Torah Temimah"})
    cs[0].can_delete()
    cs[1].can_delete()
    pass
    c = Category().load({"path": ["Tanakh", "Commentary", "Torah Temimah", "Torah"]})
    cs[0].delete()
    cs[1].delete()

    
    SERVER = "http://localhost:8000"
    posting_index_now = False
    posting_text = False
    torah_books = library.get_indexes_in_category("Torah")
    dirs = [dir for dir in os.listdir(".") if os.path.isdir(dir)]
    if posting_index_now:
        add_term("Torah Temimah", u"תורה תמימה", "commentary_works", server=SERVER)
        create_complex_index_torah_commentary("Torah Temimah", u"תורה תמימה", intro_structure=["Chapter", "Paragraph"], server=SERVER)

    for dir in dirs:
        if posting_index_now:
            if dir not in torah_books:
                categories = ["Tanakh", "Commentary", "Torah Temimah", library.get_index(dir).categories[-1]]
                index = create_simple_index_commentary("Torah Temimah", u"תורה תמימה", dir, categories, server=SERVER)

        text_dict = pre_parse(dir)
        for key in text_dict.keys():
            text_dict[key] = convertDictToArray(text_dict[key])
        text = convertDictToArray(text_dict)

        send_text = {
            "text": text,
            "language": "he",
            "versionTitle": "Torah Temimah, Vilna, 1904",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001750892"
        }
        #if posting_text:
        #    if dir not in torah_books:
        #        post_text("Torah Temimah on {}".format(dir), send_text, server=SERVER)
        #    else:
        #        post_text("Torah Temimah on Torah, {}".format(dir), send_text, server=SERVER)

    if posting_text:
        #make_and_post_intro(send_text)
        make_and_post_links()

    print "ERRORS {}".format(errors)
