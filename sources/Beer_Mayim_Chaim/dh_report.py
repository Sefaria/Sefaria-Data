# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'

from sources.functions import *
import os
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from BeautifulSoup import *
from data_utilities.util import set_ranges_between_refs
from data_utilities.util import WeightedLevenshtein


from data_utilities.dibur_hamatchil_matcher import *
import bleach


links = []

def match_report(text, perek_num, file):
    perek_ref = "{} {}".format(file[0:-4].title(), perek_num)
    for pasuk_num in text[perek_num].keys():
        comm_ref = TextChunk(Ref("Be'er Mayim Chaim on Torah, {}:{}".format(perek_ref, pasuk_num)), lang='he')
        if comm_ref.text == []:
            continue
        num_segments = len(comm_ref.text)
        if num_segments <= 10:
            comm_ref_range = Ref("Be'er Mayim Chaim on Torah, {}:{}:1-{}".format(perek_ref, pasuk_num, num_segments))
            pasuk_ref = Ref("{}:{}".format(perek_ref, pasuk_num))
            links.append({
                "refs": [comm_ref_range.normal(), pasuk_ref.normal()],
                "type": "Commentary",
                "auto": True,
                "generated_by": "beer"
            })


def create_schema():
    root = SchemaNode()
    root.add_primary_titles("Be'er Mayim Chaim on Torah", u"באר מים חיים על תורה")

    books = library.get_indexes_in_category("Torah", full_records=True)
    for book in books:
        en_name = book.get_title("en")
        he_name = book.get_title("he")
        node = JaggedArrayNode()
        node.toc_zoom = 2
        node.add_structure(["Chapter", "Paragraph", "Comment"])
        node.add_primary_titles(en_name, he_name)
        root.append(node)

    index = {
        "schema": root.serialize(),
        "dependence": "Commentary",
        "collective_title": "Be'er Mayim Chaim",
        "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
        "categories": ["Chasidut"],
        "title": u"Be'er Mayim Chaim on Torah"
        }
    post_index(index, server="http://proto.sefaria.org")
    assert 2 == 3

def beer_mayim_post(file, text):
    for perek_num in text.keys():
        text[perek_num] = convertDictToArray(text[perek_num])
    text = convertDictToArray(text)
    create_payload_and_post_text("Be'er Mayim Chaim on Torah, {}".format(file[0:-4].title()), text, "he",
        vtitle="Be'er Mayim Chaim, Jerusalem 1991.",
        vsource="http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001185750",
        server="http://proto.sefaria.org")

def tokenizer(str):
    return str.split(" ")

def make_ranges_from_csv(file):
    '''
    start range at first time encountering new pasuk
    '''
    reader = UnicodeReader(file)
    current_range = None
    current_pasuk = None
    ranges = []
    for row in reader:
        if not row[0].startswith("Be'er Mayim"):
            continue
        poss_current_pasuk = get_pasuk(row[0])
        curr_ref = row[0]
        if current_pasuk is None:
            current_pasuk = poss_current_pasuk
            current_range = Ref(current_pasuk)
        elif poss_current_pasuk != current_pasuk or (poss_current_pasuk == current_pasuk and row[2] == "1"):
            assert current_range
            current_range = current_range.to(Ref(last_ref))
            ranges.append([current_range.normal(), current_pasuk.replace("Be'er Mayim Chaim on Torah, ", "")])
            current_range = Ref(curr_ref)
            current_pasuk = poss_current_pasuk
        last_ref = row[0]
    make_links(ranges)

def make_links(ranges):
    for range_pair in ranges:
        links.append({
            "refs": range_pair,
            "type": "Commentary",
            "auto": True,
            "generated_by": "BCM ranges"
        })
    post_link(links, server="http://proto.sefaria.org")



def get_pasuk(ref_str):
    pos = ref_str.rfind(":")
    ref = Ref(ref_str[0:pos])
    assert len(ref.sections) == 2
    return ref.normal()


if __name__ == "__main__":
    '''
    iterate and count perek and pasuk
    '''

    create_schema()
    meta_data = []
    meta_data_file = open("Be'er Mayim Chaim on Torah - he - Be'er Mayim Chaim, Jerusalem 1991.csv")
    make_ranges_from_csv(meta_data_file)

    files = [file for file in os.listdir(".") if file.endswith(".txt")]

    for file in files:
        print file
        text = {}
        perek_num = 0
        pasuk_num = 0
        for line in open(file):
            line = line.decode('utf-8').replace("\r", "").replace("\n", "").replace("{1}", "").replace("{2}", "").replace("@", "").replace("<sup>4</sup>", "<sup>*</sup>")
            if "$$" in line and len(line.split(" ")) < 4:
                #if perek_num > 0:
                #    match_report(text, perek_num, file)
                perek_num = getGematria(line.split(" ")[0])
                if perek_num in text:
                    print "Problem in {}: Found perek {} twice".format(file, perek_num)
                text[perek_num] = {}
                pasuk_num = 0
            elif "%%" in line and len(line.split(" ")) < 4:
                pasuk_num = getGematria(line.split(" ")[0])
                if pasuk_num in text[perek_num]:
                    print "Problem in {}: In perek {}, found pasuk {} twice".format(file, perek_num, pasuk_num)
                text[perek_num][pasuk_num] = []
            elif "##" in line:
                continue
            elif perek_num > 0 and pasuk_num > 0:
                text[perek_num][pasuk_num].append(line)
        beer_mayim_post(file, text)

    post_link(links, server="http://proto.sefaria.org")

