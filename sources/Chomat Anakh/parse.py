# -*- coding: utf-8 -*-

import re
from sefaria.model import *
from sources.functions import *
from sefaria.system.exceptions import *
from data_utilities.link_disambiguator import *
from data_utilities.dibur_hamatchil_matcher import *

SERVER = "http://draft.sefaria.org"
versionTitle = "Chomat Anakh, Jerusalem 1965"
versionSource = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001139222"
not_found = {}
verse_find_results = {}
sham_verses_indicated_set = set()

def parse(lines, verses_indicated=True):
    prev_ch = 1
    prev_v = 1
    text = {}
    sham_verses_indicated = False
    for count, line in enumerate(lines):
        orig_line = line
        ch_v_finds = re.findall(u"@\d+\[.*?,.*?\]@?\d?", line)
        sham = re.findall(u"@\d+\[שם.*?\]", line)
        assert len(ch_v_finds) in [0, 1]
        if len(sham) is 1:
            if "," in sham[0]:
                poss_verse = sham[0].split(",")[1]
                if "-" in poss_verse:
                    poss_verse = poss_verse.split("-")[0]
                poss_verse_num = getGematria(poss_verse)
                if poss_verse_num > 0:
                    sham_verses_indicated = True
                    v = poss_verse_num
                    text[ch][v] = []
            line = line.replace(sham[0], "")
        elif len(ch_v_finds) is 1:
            line = line.replace(ch_v_finds[0], "")
            if verses_indicated:
                ch, v = parse_ch_v(ch_v_finds[0])
                if ch not in text:
                    text[ch] = {}
                if v not in text[ch]:
                    text[ch][v] = []
            else:
                ch = getGematria(ch_v_finds[0])
                if ch not in text:
                    text[ch] = []

        line = removeAllTags(line)
        if len(line) > 0:
            line_arr = line.split(".", 1)
            assert len(line_arr) in [1, 2]
            if len(line_arr) == 2:
                dh = line_arr[0]
                comment = line_arr[1]
                dh = u"<b>{}</b>.".format(dh)
                line = dh + comment
            if verses_indicated:
                text[ch][v].append(line)
            else:
                text[ch].append(line)

    return text, sham_verses_indicated

def parse_ch_v(ch_v):
    ch_v = ch_v.replace(", ", ",")
    ch_v_first_at = ch_v.find("@")
    ch_v_last_at = ch_v.rfind("@")
    if ch_v_last_at > ch_v_first_at:
        ch_v = ch_v[ch_v_first_at:ch_v_last_at]
    else:
        ch_v = ch_v[ch_v_first_at:]
    ch_v = ch_v.split("-")[0]  # if there is a range, take the beginning of the range
    ch, v = ch_v.split(",")[0], ch_v.split(",")[1]
    ch = getGematria(ch)
    v = getGematria(v)
    return ch, v


def get_en_book(he_book):
    try:
        title = library.get_index(he_book).title
    except BookNameError:
        title_wout_first_word = " ".join(he_book.split(" ")[1:])
        title = library.get_index(title_wout_first_word).title
    return title


def pre_parse(file, verses_indicated=True):
    text = {}
    lines = []
    en_book = ""
    sham_bool = False
    for line in file:
        orig_line = line
        line = line.replace("\n", "").decode('utf-8')
        line = line.strip()
        is_header = line.split(" ")
        start_book_of_torah = line.startswith("@2") and u"פרשת" not in line and not line.startswith("@22")
        start_book_of_nach = line.startswith("@22") or line.startswith("@00") or line.startswith("@9")
        if start_book_of_torah and "[" not in line and "]" not in line:
            line = line.replace("@2", "")
            if len(lines) > 0:
                text[(en_book, he_book)], sham_bool = parse(lines, verses_indicated)
            if sham_bool:
                sham_verses_indicated_set.add(en_book)
                sham_bool = False
            en_book = "Torah, {}".format(get_en_book(line))
            he_book = line
            text[(en_book, he_book)] = {}
            lines = []

        elif start_book_of_nach and "[" not in line and "]" not in line:
            line = line.replace("@22", "").replace("@00", "").replace("@9", "")
            if len(lines) > 0:
                text[(en_book, he_book)], sham_bool = parse(lines, verses_indicated)
            if sham_bool:
                sham_verses_indicated_set.add(en_book)
                sham_bool = False
            en_book = get_en_book(line)
            he_book = line
            text[(en_book, he_book)] = {}
            lines = []

        elif u"פרשת" not in line or len(line.split(" ")) > 3:
            ch_v_marker = re.findall(u"@\d+\[.*?\]@\d+", line)
            lines.append(line)

    if len(lines) > 0:
        text[(en_book, he_book)] = parse(lines, verses_indicated)
    return text


def create_schema_nach(en, he, cat):
    root = JaggedArrayNode()
    comm_en = "Chomat Anakh on {}".format(en)
    comm_he = u"חומת אנך על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter", "Verse", "Paragraph"])
    root.toc_zoom = 2
    root.validate()
    index = {
        "dependence": "Commentary",
        "base_text_titles": [en],
        "base_text_mapping": "many_to_one",
        "title": comm_en,
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary", "Chomat Anakh", cat]
    }
    post_index(index, server=SERVER)

def create_schema_torah():
    root = SchemaNode()
    comm_en = "Chomat Anakh on Torah"
    comm_he = u"חומת אנך על תורה"
    root.add_primary_titles(comm_en, comm_he)
    indexes = library.get_indexes_in_category("Torah")
    for book in indexes:
        node = JaggedArrayNode()
        node.toc_zoom = 2
        book = library.get_index(book)
        he_title = book.get_title('he')
        en_title = book.get_title('en')
        links = make_commentary_links("{}, {}".format(comm_en, en_title), en_title)
        links = [{"refs": link, "generated_by": "ChomatAnakh", "type": "Commentary", "auto": True} for link in links]
        #post_link(links, server=SERVER)
        node.add_primary_titles(en_title, he_title)
        node.add_structure(["Chapter", "Verse", "Paragraph"])
        root.append(node)

    root.validate()
    index = {
        "dependence": "Commentary",
        "base_text_titles": indexes,
        "title": comm_en,
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary", "Chomat Anakh"]
    }
    post_index(index, server=SERVER)



def convertChaptersToChaptersVerse(text_dict, en, he):
    def base_tokenizer(str):
        str = str.replace(u"־"," ").replace("-", " ")
        str_list = str.split(" ")
        str_list = [str for str in str_list if len(str) > 0]
        return str_list

    def dh_extract_method(str):
        str = str.replace("<b>", "").replace("</b>", "")
        if "." in str:
            return str.split(".", 1)[0]
        else:
            return ""

    def rashi_filter(str):
        if len(str) == 0:
            return False
        return True

    def find_verse(pos, base_text):
        num_words = 0
        for count, line in enumerate(base_text):
            line = line.replace(u"־"," ").replace("-", " ")
            num_words += len(line.split(" "))
            if pos+1 <= num_words:
                return count+1

    not_found[en] = {}
    for ch_key, comm_text in text_dict[(en, he)].items():
        base_text_chunk = TextChunk(Ref("{} {}".format(en, ch_key)), lang='he', vtitle="Tanach with Text Only")
        base_text = base_tokenizer(" ".join(base_text_chunk.text))
        results = match_text(base_text, comm_text, dh_extract_method=dh_extract_method)['matches']

        text_dict[(en, he)][ch_key] = {}
        for count, result in enumerate(results):
            if result != (-1, -1):
                start = result[0]
                verse = find_verse(start, base_text_chunk.text)
                if verse not in text_dict[(en, he)][ch_key]:
                    text_dict[(en, he)][ch_key][verse] = []
                text_dict[(en, he)][ch_key][verse] += [comm_text[count]]
            else:
                if ch_key not in not_found[en]:
                    not_found[en][ch_key] = []
                not_found[en][ch_key].append(comm_text[count])
    return text_dict[(en, he)]


def create_fake_schema(en, he):
    root = JaggedArrayNode()
    comm_en = "Chomat Anakh on {}".format(en)
    comm_he = u"חומת אנך על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter", "Paragraph"])
    index = {
        "title": comm_en,
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary"]
    }
    post_index(index, server="http://localhost:8000")



def find_verses(text_dict, en, he):
    if en not in verse_find_results.keys():
        verse_find_results[en] = {}
    ld = Link_Disambiguator()
    for ch in text_dict[(en, he)].keys():
        if ch not in verse_find_results[en].keys():
            verse_find_results[en][ch] = []
        chomat_refs = Ref("Chomat Anakh on {} {}".format(en, ch)).all_segment_refs()
        tanakh_refs = Ref("{} {}".format(en, ch)).all_segment_refs()
        tanakh_tc = TextChunk(Ref("{} {}".format(en, ch)), lang='he')
        chomat_tc = TextChunk(Ref("Chomat Anakh on {} {}".format(en, ch)), lang='he')
        chomat_tc_list = [TextChunk(ref, lang='he') for ref in chomat_refs]
        tanakh_tc_list = [TextChunk(ref, lang='he') for ref in tanakh_refs]
        for chomat_tc in chomat_tc_list:
            verse_find_results[en][ch].append(ld.disambiguate_segment(chomat_tc, [tanakh_tc]))
            pass


def post_books(text_dict, verses_indicated=True):
    #create_schema_torah()
    for en, he in text_dict.keys():
        if not en.startswith("Torah,"):
            cat = library.get_index(en).categories[-1]
            if cat == "Commentary":
                cat = "Prophets"
            print "./run scripts/move_draft_text.py 'Chomat Anakh on {}' -d 'https://www.sefaria.org' -v 'all' -k 'kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg'".format(
                    en)

                #create_schema_nach(en, he, cat)
        '''
        if not verses_indicated:
            text = text_dict[(en, he)]
            text = convertDictToArray(text)
            text = convertChaptersToChaptersVerse(text_dict, en, he)
        else:
            text = text_dict[(en, he)]

        for ch_key in text.keys():
            text[ch_key] = convertDictToArray(text[ch_key], empty=[])
        text = convertDictToArray(text)

        send_text = {
                "text": text,
                "versionTitle": versionTitle,
                "versionSource": versionSource,
                "language": "he"
            }
        #post_text("Chomat Anakh on {}".format(en), send_text, server=SERVER)
        '''

def record_not_found():
    csv_writer = UnicodeWriter(open("chomat anakh not found.csv", 'w'))
    for book in not_found.keys():
        for chapter, text_arr in not_found[book].items():
            ref = "{} {}".format(book, chapter)
            for line in text_arr:
                csv_writer.writerow([ref, line])



if __name__ == "__main__":
    text1 = pre_parse(open("chomat anakh1.txt"))
    text3 = pre_parse(open("chomat anakh3.txt"))
    post_books(text3)
    text2 = pre_parse(open("chomat anakh2.txt"), verses_indicated=False)
    post_books(text2, verses_indicated=False)
    #record_not_found()
    post_books(text1)
    print sham_verses_indicated_set
