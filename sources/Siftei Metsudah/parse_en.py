# -*- coding: utf-8 -*-
import re
from sefaria.model import *
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *
from glob import glob

pasuk_errors = 0
tog_set = set()

subline_probs = []

def check_pasuk_order(line, perek, curr_pasuk, starters, curr_ref, base):
    poss_pasuk, line = line.split(".", 1)
    new_pasuk = int(poss_pasuk)
    if new_pasuk <= curr_pasuk:
        perek += 1
        prev_ref = curr_ref
        curr_ref = u"{} {}".format(base, perek)
        if prev_ref not in probs:
            starters.append((perek, new_pasuk, line))
        else:
            perek -= 1
            starters.append((u"*{}".format(perek), new_pasuk, line))
    curr_pasuk = new_pasuk
    return perek, curr_pasuk, curr_ref


def check_pasuk_order_and_parse_text(lines, book, base, lang='en', probs=[], start_markers=["@ps"], closers=[]):
    curr_pasuk = 0
    perek = 1
    starters = []
    prev_ref = curr_ref = None
    text = {}
    for count, line in enumerate(lines):
        orig_line = line
        if len(line) <= 1:
            continue

        has_pasuk = re.findall(u"^\d+\.", line)
        assert len(has_pasuk) in [0, 1]

        if has_pasuk:
            perek, curr_pasuk, curr_ref = check_pasuk_order(line, perek, curr_pasuk, starters, curr_ref, base)
            line = line.replace(has_pasuk[0] + " ", "").replace(has_pasuk[0], "")

        if perek not in text.keys():
            text[perek] = {}
        if curr_pasuk not in text[perek].keys():
            text[perek][curr_pasuk] = []

        closer_present = False
        for closer in closers:
            if closer in line:
                closer_present = True
        if closer_present:
            sublines = split_line_by_array(line, start_markers)
        else:
            sublines = [line]

        text = add_sublines_to_text(sublines, text, perek, curr_pasuk)
    return text, perek, starters

def add_sublines_to_text(sublines, text, perek, curr_pasuk):
    for j, subline in enumerate(sublines):
        for closing_marker in closers:
            if closing_marker in subline:
                subline = subline.replace(closing_marker, "</b>", 1)
                if not subline.startswith("<b>"):
                    subline = "<b>" + subline
        subline = process_tag(subline)
        if len(subline) > 3:
            if not "<b>" in subline:
                subline_probs.append(subline)
            text[perek][curr_pasuk].append(subline)
    return text


def split_line_by_array(line, array, index=0):
    '''
    Check if anything is left to split in the array
    If there isn't, then return the text
    If there is,
    Check if text needs to be split by array[index].
    If it does, return split
    If it doesn't, return text
    :param text:
    :param array:
    :return:
    '''

    if index >= len(array):
        return [line]

    splitter = array[index]

    if splitter in line:
        lines = line.split(splitter)
        split_lines = []
        for line in lines:
            temp = split_line_by_array(line, array, index+1)
            if type(temp) is not list:
                split_lines.append(line)
            else:
                for x in temp:
                    split_lines.append(x)
        return split_lines
    else:
        return split_line_by_array(line, array, index+1)


'''

'''

def process_tag(subline):
    tag_translations = [("@IT", "<i>", "@it", "</i>"),
                      ("@BO", "<b>", "@bo", "</b>"),
                      ("@m1", "<small>", "@m2", "</small>"),
                      ("@mr", "<small>", "@rm", "</small>"),
                        ("@M", "<small>", "@J", "</small>")]

    for row in tag_translations:
        while row[0] in subline and row[2] in subline:
            subline = subline.replace(row[0], row[1], 1).replace(row[2], row[3], 1)

    num_bolds = len(subline.split("<b>")) - 1
    num_bold_ends = len(subline.split("</b>")) - 1
    num_italics = len(subline.split("<i>")) - 1
    num_italics_ends = len(subline.split("</i>")) - 1

    if not subline.startswith("<b>") and "@bo" in subline:
        subline = "<b>" + subline.replace("@bo", "</b>", 1)

    for TOG_tag in re.findall("@.{2}", subline):
        subline = subline.replace(TOG_tag, "")
        tog_set.add(TOG_tag)

    try:
        assert num_bolds == num_bold_ends, "Bolding off {} vs {}".format(num_bold_ends, num_bolds)
    except AssertionError as e:
        print repr(e)

    try:
        assert num_italics == num_italics_ends, "Italics off {} vs {}".format(num_italics_ends, num_italics)
    except AssertionError as e:
        print repr(e)

    return subline



def convert_one_file(file, lang='he', comm='Siftei'):
    lines = []
    big_line = ""
    pattern_siftei_en = (u"@p1\[\d+\]@[a-z0-9]{2}", u"@p1\[(\d+)\]@[a-z0-9]{2}")
    pattern_rashi_en = (u"@p1\d+@[a-z0-9]{2}", u"@p1(\d+)@[a-z0-9]{2}")

    pattern_siftei_he = (u"@s[a-z0-9]{1}.{1,2}\s?.{0,2}\)@[a-z0-9]{2}", u"@s[a-z0-9]{1}\((.{1,2}\s?.{0,2})\)@[a-z0-9]{2}")
    pattern_rashi_he = (u"@P\(.{1,2}\s?.{0,2}\)", u"@P\((.{1,2})\s?.{0,2}\)")


    if lang == 'he':
        pattern = pattern_siftei_he if comm == "Siftei" else pattern_rashi_he
    else:
        pattern = pattern_siftei_en if comm == "Siftei" else pattern_rashi_en

    with open(file) as f:
        f = list(f)
        for count, line in enumerate(f):
            line = line.replace('\xef\xbb\xbf', '')
            line = line.decode('utf-8')
            for xml_tag in re.findall("<.*?>", line):
                line = line.replace(xml_tag, " ")
            while "  " in line:
                line = line.replace("  ", " ")
            assert len(line.split('\n')) == 2
            line = line[0:-1]
            if lang == 'he' and comm == "Rashi":
                for prob_citation in re.findall(u"@M.*?\),?@T", line): #need to get rid of the @T since the meaning of @T is overloaded
                    fixed_citation = prob_citation.replace("@T", "@J")
                    line = line.replace(prob_citation, fixed_citation)

            big_line += line

    matches = re.findall(pattern[0], big_line)
    just_pasukim = re.findall(pattern[1], big_line)
    for tuple in zip(matches, just_pasukim):
        match = tuple[0]
        num = tuple[1] if lang == 'en' else getGematria(tuple[1])
        if u"שם" not in match:
            big_line = big_line.replace(match, u"\n{}.".format(num))
    return [subline for subline in big_line.split(u"\n") if subline != u""]



def produce_perek_report(book, comments, torah, lang='en'):
    #check perakim length
    writer = UnicodeWriter(open("{}_{}_{}.csv".format(book, lang, torah), 'w'))
    writer.writerow(["Assumed to be correct references", "Siftei Chakhamim comment"])
    for perek, pasuk, comm in comments:
        ref = "{} {}:{}".format(torah, perek, pasuk)
        writer.writerow([ref, comm])


def convert_he(book, i, file_title):
    dir = "./" + book + "/" + numToHeb(i + 1)
    files = [file for file in os.listdir(dir) if file.endswith(".txt")]
    lines = []
    sort_func = lambda x: int(x.replace("{}.txt".format(file_title), ""))
    for file in sorted(files, key=sort_func):
        if file_title == "SH": #siftei
            lines += convert_one_file(dir + "/" + file, lang='he', comm="Siftei")
        else:
            lines += convert_one_file(dir + "/" + file, lang='he', comm="Rashi")
    return lines


def produce_section_report(our_text, **kwargs):
    comm = kwargs["comm"]
    torah_book = kwargs["torah_book"]
    orig_text = kwargs["comm_book"]
    lang = kwargs["lang"]
    ch_length = len(Ref(orig_text).text(lang).text)
    if len(our_text.keys()) != ch_length:
        return

    all_top_sections = [ref.normal() for ref in library.get_index(orig_text).all_top_section_refs()]
    all_sections = [ref.normal() for ref in library.get_index(orig_text).all_section_refs()]
    all_segments = [ref.normal() for ref in library.get_index(orig_text).all_segment_refs()]

    for perek in our_text.iterkeys():
        for pasuk, text_arr in our_text[perek].iteritems():
            pasuk_ref = "{} {}:{}".format(orig_text, perek, pasuk)
            if pasuk_ref not in all_sections:
                global pasuk_errors
                pasuk_errors += 1


def produce_he_to_en_report(comm_title, dict):
    en_text = dict['en']
    he_text = dict['he']
    comments = {}
    for torah_book in en_text.iterkeys():
        comments[torah_book] = {"en": 0, "he": 0}
        for lang in ["en", "he"]:
            for perek, perek_dict in dict[lang][torah_book].iteritems():
                for pasuk, text_arr in perek_dict.iteritems():
                    comments[torah_book][lang] += len(text_arr)
    return comments


def produce_he_to_he_report(comm, comments):
    if comm == "Siftei":
        comm = ["Siftei Chakhamim"]
    else:
        comm = ["Rashi on {}".format(book) for book in library.get_indexes_in_category("Torah")]

    all_segment_refs = []
    for book in comm:
        all_segment_refs += library.get_index(book).all_segment_refs()

    node_title_for_refs = [ref.index.title.replace("Rashi on ", "") for ref in all_segment_refs]
    for torah_book in library.get_indexes_in_category("Torah"):
        comments[torah_book]["existing"] = len([ref for ref in node_title_for_refs if ref == torah_book])

    print comments



def get_split_marker(comm, lang, torah_book):
    if comm == "Siftei" and lang == 'he':
        starters = ["@ps", "@PS"] if torah_book != "Exodus" else ["@sr", "@SR"]
        closers = ["@sp", "@SP"] if torah_book != "Exodus" else ["@rs", "@RS"]
    elif lang == 'en':
        starters = ["@p1", "@d1", "@P1", "@D1"]
        closers = ["@p3", "@P3", "@d2", "@D2"]
    elif comm == "Rashi" and lang == "he":
        starters = ["@K"]
        closers = ["@T"]
    return starters, closers


def make_links_siftei(text_dict):
    '''
    every DH
    :param text_dict:
    :return:
    '''
    def dh_extract_method(str):
        str = str.lower()
        if "<b>" in str:
            start = str.find("<b>")
            end = str.find("</b>")
            dh = str[start+3:end]
            return dh.replace("etc.", "")
        else:
            return " ".join(str.split(" ")[0:5])


    def base_tokenizer(str):
        str = str.lower().replace("<b>", "").replace("</b>", "")
        str = strip_nekud(str)
        str_arr = str.split(" ")
        return [str for str in str_arr if str]

    links = []
    for lang in text_dict.iterkeys():
        results = {}
        if lang == 'en':
            continue
        comm_vtitle = "Sifsei Chachomim Chumash, Metsudah Publications, 2009"

        for torah_book, text in text_dict[lang].iteritems():
            results[torah_book] = []
            for perek, perek_arr in text.iteritems():
                for pasuk, text_arr in enumerate(perek_arr):
                    pasuk += 1
                    base_ref = Ref("Rashi on {} {}:{}".format(torah_book, perek, pasuk))
                    comm_ref = "Siftei Chakhamim, {}".format(torah_book)
                    comm_ref = Ref("{} {}:{}".format(comm_ref, perek, pasuk))
                    base_text = TextChunk(base_ref, lang=lang, vtitle="On Your Way")
                    comm_text = TextChunk(comm_ref, lang=lang, vtitle=comm_vtitle)
                    if base_text.text == [] or comm_text.text == []:
                        continue
                    temp_results = match_ref(base_text, comm_text, base_tokenizer, dh_extract_method=dh_extract_method)
                    for rashi, siftei in zip(temp_results["matches"], temp_results["comment_refs"]):
                        link = {"refs": [rashi.normal(), siftei.normal()],
                                "type": "commentary", "auto": True, "generated_by": "siftei_metsudah"}
                        links.append(link)

        post_link(links)


def make_links_base_text_mapping(text_dict, dont_post=False):
    links = []
    for comm in text_dict.iterkeys():
        for lang in text_dict[comm].iterkeys():
            for torah_book, text in text_dict[comm][lang].iteritems():
                comm_ref = "Rashi on {}".format(torah_book) if comm == "Rashi" else "Siftei Chakhamim, {}".format(torah_book)
                ref_pairs = create_links_many_to_one(comm_ref, torah_book)
                for refs in ref_pairs:
                    link = {"refs": refs,
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "Metsudah_"+comm}
                    links.append(link)
    if not dont_post:
        post_link(links)


def post(text_dict, dont_post=False):
    for comm in text_dict.iterkeys():
        versionTitle = "Sifsei Chachomim" if comm == "Siftei" else "Rashi"
        for lang in text_dict[comm].iterkeys():
            for torah_book, text in text_dict[comm][lang].iteritems():
                ref = "Rashi on {}".format(torah_book) if comm == "Rashi" else "Siftei Chakhamim, {}".format(torah_book)
                for perek, perek_dict in text.iteritems():
                    text[perek] = convertDictToArray(text[perek])
                text = convertDictToArray(text)
                send_text = {
                    "text": text,
                    "language": lang,
                    "versionTitle": "{} Chumash, Metsudah Publications, 2009".format(versionTitle),
                    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002691623"
                }
                if not dont_post:
                    post_text(ref, send_text, server="http://localhost:8000")

def segment_or_hachaim():
    for book in library.get_indexes_in_category("Or HaChaim", include_dependant=True):
        for section_ref in library.get_index(book).all_section_refs():
            section_tc = TextChunk(section_ref, lang='he', vtitle='On Your Way')
            new_section_arr = []
            for i, line in enumerate(section_tc.text):
                brs = re.findall(u"(:(<b>)?<br>)", line)
                while brs != []:
                    line_to_append, line = line.split(brs[0][0], 1)
                    if "<b>" in brs[0][0]:
                        line = "<b>" + line
                    new_section_arr.append(line_to_append+":")
                    brs = re.findall(u"(:(<b>)?<br>)", line)
                assert len(line) > 0
                new_section_arr.append(line)

            if len(new_section_arr) > 0:
                assert len(line) > 0
                section_tc.text = new_section_arr
                section_tc.save(force_save=True)

        VersionState(book).refresh()

if __name__ == "__main__":
    '''
    Check if Pasuk information alone gives us all 50 chapters
    If it doesn’t work, check Hebrew and English versions that the pasuk go in same order and if they do then Use DH of Hebrew to figure out what Perek we are in
    '''
    results = {"Rashi": {"en": [], "he": []}, "Siftei": {"en": [], "he": []}}
    text_dict = {"Rashi": {"en": {}, "he": {}}, "Siftei": {"en": {}, "he": {}}}

    probs = ["Numbers 19", "Deuteronomy 32"]
    for comm in [file for file in os.listdir(".") if os.path.isdir(file)]:
        eng_title = "SE" if comm == "Siftei" else "RE"
        he_title = "SH" if comm == "Siftei" else "RH"
        for lang in ['en', 'he']:
            if not (comm == "Siftei"):
                continue

            for i in range(5):
                if lang == 'en':
                    file = "{}/{}{}.txt".format(comm, i + 1, eng_title)
                    lines = convert_one_file(file, lang='en', comm=comm)
                else:
                    lines = convert_he(comm, i, he_title)

                torah_book = library.get_indexes_in_category("Torah")[i]
                text_dict[comm][lang][torah_book] = {}
                if comm == "Rashi":
                    comm_book = "Rashi on {}".format(torah_book)
                    num_chapters = len(library.get_index(comm_book).all_top_section_refs())
                    orig_text = Ref(comm_book).text('he').text
                else:
                    comm_book = "Siftei Chakhamim, {}".format(torah_book)
                    all_top_sections = library.get_index(comm_book).all_top_section_refs()
                    all_top_sections = [sec for sec in all_top_sections if torah_book in sec.normal()]
                    num_chapters = len(all_top_sections)

                starters, closers = get_split_marker(comm, lang, torah_book)
                results = check_pasuk_order_and_parse_text(lines, comm, torah_book, lang=lang, probs=probs, start_markers=starters, closers=closers)
                text_dict[comm][lang][torah_book], perek_total, comments = results
                produce_perek_report(comm, comments, torah_book, lang=lang)
                #info = {"comm": comm, "torah_book": torah_book, "comm_book": comm_book, "lang": lang}
                #produce_section_report(our_text, **info)
                #results[comm][lang].append("{} {} of {}".format(torah_book, perek_total, num_chapters))


    #comments = produce_he_to_en_report("Rashi", text_dict["Rashi"])
    #produce_he_to_he_report("Rashi", comments)
    dont_post = False
    #post(text_dict, dont_post=dont_post)
    make_links_base_text_mapping(text_dict, dont_post=dont_post)
    make_links_siftei(text_dict["Siftei"])


    # print results["Rashi"]["en"]
    # print results["Siftei"]["en"]
    #
    # print results["Rashi"]["he"]
    print tog_set
