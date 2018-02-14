# -*- coding: utf-8 -*-
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
from sefaria.helper.text import replace_roman_numerals_including_lowercase
import re

def align(file):
    json_data = json.load(open(file))
    text = json_data['text'][""]
    how_many_period = 0
    how_many_italics = 0
    how_many_footnote = 0
    set1 = set()
    set2 = set()
    set3 = set()
    count = 0
    new_text = []

    for chapter in text:
        new_text.append([])
        for verse in chapter:
            current_perek = len(new_text) - 1
            new_text[current_perek].append([])
            for comment in verse:
                comment = comment.replace(u"\u201c", u"").replace(u"\u201d", u"")
                current_verse = len(new_text[current_perek]) - 1
                #segments = re.findall(u"""<span>[\u0590-\u05FF|\s]+</span>\s+<i>.*?</i>""", comment)
                period_span = re.findall(u"""\.\s+(<span>[\u0590-\u05FF|\s]+</span>\s+<i>.*?</i>)""", comment)
                footnote_span = re.findall(u"""<sup>\d+</sup><i class="footnote">.*?</i>\s+(<span>[\u0590-\u05FF|\s]+</span>.{5}.*?\.)""", comment)
                period_italics = re.findall(u"""\.\s+(<i>.*?</i>)""", comment)
                footnote_italics = re.findall(u"""<sup>\d+</sup><i class="footnote">.*?</i>\s+(<i>.*?</i>)""", comment)
                footnote_span = [el for el in footnote_span if not (el.find("<i>") >= 0) ^ (el.find("</i>") >= 0)]
                how_many_footnote += len(footnote_span)
                how_many_period += len(period_span)
                how_many_italics += len(period_italics)
                segments = period_span + footnote_span + period_italics
                positions = []
                for each in segments:
                    print current_perek
                    print current_verse
                    print each
                    each_pos = comment.find(each)
                    assert each_pos != -1
                    if each_pos > 0:
                        positions.append(each_pos)

                positions = sorted(positions)
                start = 0
                positions.append(len(comment))
                for count, pos in enumerate(positions):
                    if count == len(positions) - 1:
                        if comment[start:pos][-1] == ' ':
                            comment = comment[:pos-1]
                        alphabet = re.compile(u"[a-zA-Z]{1}")
                        last_char = comment[-1]
                        second_last_char = comment[-2]
                        if alphabet.match(last_char):
                            comment += "."
                            pos += 1
                    actual_comment = replace_roman_numerals_including_lowercase(comment[start:pos])
                    new_text[current_perek][current_verse].append(actual_comment)
                    start = pos

    send_text = {
        "text": new_text,
        "versionTitle": json_data["versionTitle"],
        "language": "en",
        "versionSource": json_data["versionSource"]

    }
    post_text("Ibn Ezra on Isaiah", send_text, server="http://proto.sefaria.org")

    return new_text

def get_num_segments(ch1):
    count = 0
    print "ORIGINAL COUNT {}".format(len(ch1))
    for verse in ch1:
        count += len(verse)
    print "NEW COUNT {}".format(count)

def make_links():
    print LinkSet(Ref("Ibn Ezra on Isaiah")).count()
    print "before"
    all_segments = library.get_index("Ibn Ezra on Isaiah").all_segment_refs()
    for segment in all_segments:
        comm_ref = segment.normal()
        isaiah_ref = comm_ref.rsplit(":", 1)[0].replace("Ibn Ezra on Isaiah ", "Isaiah ")
        new_link = Link({"type": "Commentary", "auto": True, "generated_by": "ibnezra_isaiah_structural_linking", "refs":
                    [
                        comm_ref,
                        isaiah_ref
                    ]
              })
        try:
            new_link.save()
        except:
            print comm_ref

    print LinkSet(Ref("Ibn Ezra on Isaiah")).count()
    print "after"




if __name__ == "__main__":
    make_links()
    new_text = align("ibnezra.json")
    #for perek in new_text:
    #    print get_num_segments(perek)
    '''
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = sys.argv[1]
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Commentary of Ibn Ezra on Isaiah; trans. by M. Friedlander, 1873"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001338443"
    file_name = "IbnEzra_Isiah.xml"
    title = "Ibn Ezra on Isaiah"

    mapping = {}
    array_of_names = ["Prelude"]
    for i in range(66):
        array_of_names.append(i+1)
    array_of_names += ["Addenda", "Translators Foreword"]
    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, array_of_names)
    parser.set_funcs()
    parser.run()
    '''