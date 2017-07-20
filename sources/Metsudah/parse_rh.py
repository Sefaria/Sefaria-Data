# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sefaria.system.exceptions import *
import re
from sources.functions import *
from sefaria.model import *

SERVER = "http://ste.sefaria.org"

def parse_file(filename, notes):
    text = {}
    text['he'] = {}
    text['en'] = {}
    sections = {}
    sections['he'] = []
    sections['en'] = []
    expect_lang = 'he'
    prev_he_title = False
    note_counter = 0
    prev_note = ""
    special_tags = set(['@z2:he', '@p2:he', '@ex:en', '@pc:he', '@h1:he', '@cs:en', '@za:he', '@kt:he', '@sa:en', '@p1:he', '@e2:en', '@h2:he', '@ps:he', '@cz:he', '@ip:en', '@ct:en', '@in:en', '@sb:he', '@tx:en', '@zb:he'])
    with open(filename) as f:
        for line in f:
            orig_line = line
            if not has_content(line):
                continue
            line, note_counter, prev_note = pre_parse(line, notes, note_counter, prev_note)
            line, lang, start_tag = parse(line)
            is_title_bool = is_title(start_tag, text, lang, prev_he_title)
            is_he_title = False
            if is_title_bool:
                is_he_title = lang == 'he'
                line += "1"
                while line in sections[lang]:
                    line = line[0:-1] + str(int(line[-1]) + 1)
                text[lang][line] = []
                sections[lang].append(line)
                if len(sections[lang]) > 1 and text[lang][sections[lang][-2]] == []:
                    combine(text, sections, lang)
            elif prev_he_title: #if previous is a Hebrew title, this should be an English title, but if not, don't treat prev as title
                not_real_title = sections['he'][-1]
                text['he'].pop(not_real_title)
                sections['he'] = sections['he'][0:-1]
                he_current_section = sections['he'][-1]
                text['he'][he_current_section].append(not_real_title)
                add_line_to_text(line, start_tag, text, sections, lang)
            else:
                add_line_to_text(line, start_tag, text, sections, lang)
            expect_lang, found_expected_lang = is_expected_lang(lang, expect_lang, start_tag, special_tags)
            if not found_expected_lang:
                text[expect_lang][sections[expect_lang][-1]].append("")
            prev_line = orig_line
            prev_he_title = is_he_title

    print "FINAL COUNT {}".format(note_counter)
    return verify_he_en_same_size(text, sections)


def pre_parse(line, notes, note_counter, prev_note):
    if "@el<ENG>under compulsion@n1<*3>3@n2 and willingly." in line: #skipped 2 notes in Yom Kippur
        note_counter += 2
    line = force_tag_lower_case(line)
    line = strip_XML_tags(line)
    line = process_non_start_tags(line)
    line, note_counter, prev_note = insert_ftnote_into_line(line, notes, note_counter, prev_note)
    return line, note_counter, prev_note


def process_non_start_tags(line):
    tag_and_meaning = {"@11": "<b>", "@22": "</b>", "@sb": "<b>", "@sr": "</b>"}  #bold tags
    tag_and_meaning["@in"] = "@in<br/><i>"
    for tag, meaning in tag_and_meaning.items():
        line = line.replace(tag, meaning)

    if line.startswith("@in"): #instructions surrounded by
        line += "</i><br/>"

    return line


def add_line_to_text(line, start_tag, text, sections, lang):
    line = bold_if_necessary(line, start_tag)
    current_section = sections[lang][-1]
    text[lang][current_section].append(line)


def get_poss_notes(notes, note_counter):
    poss_notes = []
    len_notes = len(notes)
    if note_counter == len_notes:
        return poss_notes

    def_note = notes[note_counter]
    def_note_num = def_note.split(". ", 1)[0]
    poss_notes.append(def_note) #the note we expect to be referenced for sure needs to be considered
    for pos in range(-5, 5):    #after that, consider 5 before it and 5 after it
        if len_notes > note_counter + pos >= 0 and pos != 0:
            poss_note = notes[note_counter + pos]
            poss_note_num = poss_note.split(". ", 1)[0]
            if poss_note_num != def_note_num:
                poss_notes.append(poss_note)

    return poss_notes

def insert_ftnote_into_line(line, notes, note_counter, prev_note):
    prev_note_counter = note_counter
    curr_poss_notes = get_poss_notes(notes, note_counter)
    for each_poss_note in curr_poss_notes:
        this_one_is_curr = False
        if note_counter < len(notes):
            this_one_is_curr = notes[note_counter] == each_poss_note
        note_num, note_content = each_poss_note.split(". ", 1)
        found_notes = re.findall("@[n|N]1{}@[n|N]\d+".format(note_num), line)
        found_notes += re.findall("@[T|t][N|n]{}@[T|t][N|n]".format(note_num), line)
        if len(found_notes) == 0:
            continue
        else:
            old_note_text = found_notes[0]
            new_note_text = "<sup>{}</sup><i class='footnote'>{}</i>".format(note_num, note_content)
            line = line.replace(old_note_text, new_note_text)
            if this_one_is_curr:
                note_counter += 1
            prev_note = notes[note_counter-1]

    return line, note_counter, prev_note


def combine(text, sections, lang):
    text[lang].pop(sections[lang][-2])
    text[lang].pop(sections[lang][-1])
    text[lang][sections[lang][-2]+sections[lang][-1]] = []
    sections[lang][-2] = sections[lang][-2] + sections[lang][-1]
    sections[lang] = sections[lang][0:-1]


def verify_he_en_same_size(text, sections):
    num_lines = {"en": 0, "he": 0}
    num_sections = {"en": {}, "he": {}}
    assert len(sections['en']) == len(sections['he']), "{}!={}".format(len(sections['en']), len(sections['he']))
    assert len(text['he']) == len(text['en']), "{}!={}".format(len(text['he']), len(text['en']))
    zip_en_he = zip(sections['en'], sections['he'])
    for en_sec, he_sec in zip_en_he:
        #print en_sec
        #print he_sec
        len_text_en = len(text['en'][en_sec])
        len_text_he = len(text['he'][he_sec])
        '''
        if len_text_en == 0:
            print "english 0"
            print en_sec
        if len_text_he == 0:
            print "hebrew 0"
            print en_sec
        diff = len_text_en - len_text_he
        if diff != 0:
            print en_sec
            print "DIFFERENCE: {}".format(diff)
            print text['en'][en_sec]
        '''
    return text, zip_en_he

def force_tag_lower_case(line):
    return line[0:3].lower() + line[3:]

def is_expected_lang(curr_lang, expect_lang, start_tag, special_tags):
    '''
    :return: tuple that tells us what language to expect for the next line and True if the language we expected
    for this line was correct
    '''
    if expect_lang == curr_lang:
        if expect_lang == 'en':
            return 'he', True
        else:
            return 'en', True

    #assert start_tag+":"+curr_lang in special_tags

    return expect_lang, False



def reverse(func, *args):
    args = list(args)
    orig = args[0][1:3]
    reverse = orig[::-1].lower()
    args[0] = args[0].replace(orig, reverse)
    args = tuple(args)
    return func(*args, times=1)


def parse(line, times=0):
    lang = None
    en_chars = ["@e", "@c", "@i", "@sa", "@tx", "@z2"]
    he_chars = ["@h", "@k", "@p", "@za", "@zb", "@y", "@l"]
    line = line[0:3].lower() + line[3:]

    for en_char in en_chars:
        if line.startswith(en_char):
            lang = 'en'
    for he_char in he_chars:
        if line.startswith(he_char):
            lang = 'he'

    if lang is None:
        if times == 0:
            return reverse(parse, line)
        else:
            raise InputError, "line not readable"

    line, start_tag = strip_at_tags(line)
    return line, lang, start_tag

def has_content(line):
    content = not line.startswith("@RU") and not line.startswith("@ru")
    content = content and len(line.replace("\r", "").replace("\n", "").replace(" ", "")) > 0
    return content


def bold_if_necessary(line, start_tag):
    necessary = is_bold(start_tag)
    if necessary:
        return "<b>" + line + "</b>"
    else:
        return line

def is_bold(start_tag, times=0):
    bold = start_tag.startswith("@ct") or start_tag.startswith("@kt") or "b" in start_tag
    if not bold and times == 0:
        return reverse(is_bold, start_tag)

    return bold

def is_title(start_tag, text, lang, prev_he_title, times=0):
    if lang == 'en' and len(text['en']) - len(text['he']) == 0 and not prev_he_title:
        return False
    #the above prevents making something a title when there's english but no hebrew

    is_title_bool = start_tag.startswith("@ct") or start_tag.startswith("@kt")
    if not is_title_bool and times == 0:
        return reverse(is_title, start_tag, text, lang, prev_he_title)

    return is_title_bool

def strip_XML_tags(line, except_this_tag=None):
    #remove <...> and @[a-z]
    tags = re.findall(u"<.*?>", line)
    for tag in tags:
        if except_this_tag != tag:
            line = line.replace(tag, "")
    return line.replace("\r", "").replace("\n", "")

def strip_at_tags(line, return_start_tag=True):
    tags = re.findall(u"@[a-zA-Z0-9]{2}", line)
    tags_surround_word = re.findall(u"@[a-zA-Z0-9]{2}[\u05d0-\u05ea:]+@[a-zA-Z0-9]{2}", strip_XML_tags(line.decode('utf-8'))) #example: @azHELLO@az
    tags_surrounding_word_str = " ".join(tags_surround_word)
    start_tag = None
    assert len(tags) > 0

    for tag in tags:
        if line.find(tag) == 0:
            start_tag = tag
        if tag not in tags_surrounding_word_str:
            line = line.replace(tag, "")

    for tag_surround_word in tags_surround_word:
        tag_surround_word = tag_surround_word.encode('utf-8')
        if not tag_surround_word.startswith("@hh"):
            cutoff_pos = tag_surround_word.rfind("@")
            new_tag = "<small>{}</small> ".format(tag_surround_word[3:cutoff_pos])
            line = line.replace(tag_surround_word, new_tag)

    if return_start_tag:
        return line, start_tag
    else:
        return line


def create_schema(parsed_text, title, he_title):
    root = SchemaNode()
    root.add_primary_titles(title, he_title)

    en_names = parsed_text['en'].keys()
    he_names = parsed_text['he'].keys()


    assert len(he_names) == len(en_names)
    for name_pair in zip(en_names, he_names):
        node = JaggedArrayNode()
        term = Term().load({"name": name_pair[0].replace("\xe2\x80\x99", "'")})
        if term:
            node.add_shared_term(term)
        else:
            node.add_primary_titles(name_pair[0].replace("\xe2\x80\x99", "'"), name_pair[1])
        node.add_structure(["Paragraph"])
        node.validate()
        root.append(node)

    root.validate()
    index = {
        "schema": root.serialize(),
        "title": title,
        "categories": ["Liturgy"],
    }
    post_index(index, server=SERVER)


def post_en_he(text, zipped_list, title, vtitle, vsource):
    for en, he in zipped_list:
        send_text_en = {
            "versionTitle": vtitle,
            "versionSource": vsource,
            "text": text['en'][en],
            "language": 'en'
        }
        send_text_he = {
            "versionTitle": vtitle,
            "versionSource": vsource,
            "text": text['he'][he],
            "language": 'he'
        }
        en = en.replace("\xe2\x80\x99", "'")
        post_text("{}, {}".format(title, en), send_text_en, server=SERVER)
        post_text("{}, {}".format(title, en), send_text_he, server=SERVER)

def pre_parse_notes(filename):
    lines = []
    with open(filename) as f:
        for line in f:
            line = line.replace("\n", "").replace("\r", "")
            if line.find("b1") != line.rfind("b1"):
                for new_line in line.split("@b1")[1:]:
                    lines.append(new_line)
            else:
                lines.append(line)
    return lines


def get_notes(filename):
    notes = []
    lines = pre_parse_notes(filename)
    for line in lines:
        line = line.replace("\xef\xbb\xbf", "")
        num_tag_list = re.findall("(<\*(\d+)>)", line)
        assert len(num_tag_list) in [0,1]
        if len(num_tag_list) == 0:
            notes[-1] += line
            continue
        line = strip_at_tags(line, return_start_tag=False)
        line = strip_XML_tags(line)
        num_in_tag = get_number_ftnote(line, num_tag_list)
        line = line.replace(num_in_tag, "", 1)
        line = "{}. {}".format(num_in_tag, line)
        notes.append(line)

    return notes

def get_number_ftnote(line, num_tag_list):
    num_in_text_p = re.compile("\d+")
    num_in_tag = num_tag_list[0][1]
    num_in_text_match = num_in_text_p.match(line)
    num_in_text = num_in_text_match.group(0)
    assert num_in_tag in num_in_text
    return num_in_tag



def check_old_schema_vs_new_schema(parsed_text):
    new_schema_dict = {}
    old_node_list = parsed_text['he'].keys()
    new_node_list = []
    with open("newschema.txt") as f:
        for line in f:
            line = line.replace("\n", "")
            if line in new_schema_dict:
                new_schema_dict[line] += 1
            else:
                new_schema_dict[line] = 1

    for node_name, num_times in new_schema_dict.items():
        for x in range(1, num_times+1):
            temp = node_name + str(x)
            new_node_list.append(temp)

    for new_node in new_node_list:
        if new_node not in old_node_list:
            print "Old schema does not have {}".format(new_node)

    for old_node in old_node_list:
        if old_node not in new_node_list:
            print "New schema does not have {}".format(old_node)



if __name__ == "__main__":
    rosh_hashana_dict = {}
    rosh_hashana_dict["notes_file"] = "Rosh Hashanah Ashkenaz/Plain Text/Notes.txt"
    rosh_hashana_dict["content_file"] = "Rosh Hashanah Ashkenaz/Plain Text/Rosh Hashanah.txt"
    rosh_hashana_dict["title"] = "Metsudah Rosh Hashanah Machzor"
    rosh_hashana_dict["schema"] = "Rosh Hashanah_schema.txt"
    rosh_hashana_dict["heTitle"] = u"מצודה ראש השנה מחזור"
    rosh_hashana_dict["versionTitle"] = "The Metsudah Machzor; Metsudah Publications, New York"
    rosh_hashana_dict["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH000996925"

    yom_kippur_dict = dict(rosh_hashana_dict)
    for key, value in yom_kippur_dict.items():
        yom_kippur_dict[key] = value.replace("Rosh Hashanah", "Yom Kippur")

    yom_kippur_dict["heTitle"] = u"מצודה יום כפור מחזור"

    for sefer in [rosh_hashana_dict, yom_kippur_dict]:
        notes = get_notes(sefer["notes_file"])
        parsed_text, zip_en_he_names = parse_file(sefer["content_file"], notes)
        check_old_schema_vs_new_schema(parsed_text)
        create_schema(parsed_text, sefer["title"], sefer["heTitle"])
        post_en_he(parsed_text, zip_en_he_names, sefer["title"], sefer["versionTitle"], sefer["versionSource"])