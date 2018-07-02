# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sefaria.system.exceptions import *
import re
from sources.functions import *
from sefaria.model import *
from bs4 import BeautifulSoup
from BeautifulSoup import NavigableString, Tag
SERVER = "http://draft.sefaria.org"

def split_up_paragraphs_into_lines(file):
    lines = []
    for line in file:
        if "@TX" in line or "@xt" in line or "@P1" in line:
            split_up_paragraph = re.findall("(@[a-zA-Z0-9]{2}<[0-9A-Z\-]{1,5}>)", line)
            if split_up_paragraph:
                for count, each_tag in enumerate(split_up_paragraph):
                    pos = line.find(each_tag)
                    if "@xt" in line and count == 0: #this is a continuation of previous things so add it to previous
                        lines[-1] = "{}<br/>{}".format(lines[-1], line[0:pos])
                    else:
                        lines.append(line[0:pos])
                    line = line[pos:]
            lines.append(line)
        else:
            lines.append(line)
    return lines

def parse_file(filename, notes, title, heTitle):
    text = {}
    text['he'] = {}
    text['en'] = {}
    sections = {}
    sections['he'] = []
    sections['en'] = []
    expect_lang = 'he'
    prev_he_title = False
    note_counter = 0
    prev_note_counter = -1
    '''
    check if prev_note_counter is note_counter even though there was a @
    '''
    prev_note = ""
    current_outer_section = None
    current_section = None
    flat_to_multi = {} #in parsing text, we build a flat list of english section names and use this dict to
                        #determine where in the multidimensional depth 3 text each flat section name corresponds to

    heb_flat_to_eng = {} #there are no multid tags for hebrew, so we build a dictionary of hebrew to english to get the flat en section and then
                    #use flat_to_multi to get the multid section

    lines = split_up_paragraphs_into_lines(open(filename))
    root = SchemaNode()
    root.add_primary_titles(title, heTitle)
    curr_schema_node = None

    for line in lines:
        orig_line = line
        if not has_content(line):
            continue
        prev_note_counter = note_counter
        line, note_counter, prev_note = pre_parse(line, notes, note_counter, prev_note)

        line, lang, start_tag = parse(line)
        is_title_bool = is_title(start_tag, text, lang, prev_he_title)
        is_he_title = False
        if is_title_bool:
            is_he_title = lang == 'he'
            flat_title = set_flat_title(line, sections, text, lang)
            if len(sections[lang]) > 1 and text[lang][sections[lang][-2]] == [] and prev_en_title_tag == start_tag:
                combine(text, sections, lang)
            current_section, current_outer_section = add_to_map(flat_to_multi, current_outer_section, current_section, flat_title, start_tag, line)
            if lang == 'en':
                prev_en_title_tag = start_tag
                curr_he_title = sections['he'][-1]
                heb_flat_to_eng[curr_he_title] = flat_title
                curr_schema_node = create_node(start_tag, curr_he_title[0:-1], line, root, curr_schema_node)
        else:
            if prev_he_title: #if previous is a Hebrew title, this should be an English title, but if not, don't treat prev as title
                fix_prev_he_title(text, sections)

            if "in" in start_tag: #instructions need to be on separate lines
                curr_pos_en = len(text['en'][sections['en'][-1]])
                curr_pos_he = len(text['he'][sections['he'][-1]])
                if curr_pos_en + 1 == curr_pos_he:
                    text['en'][sections['en'][-1]].append("")
                    text['he'][sections['he'][-1]].append("")

            add_line_to_text(line, start_tag, text, sections, lang)



        expect_lang, found_expected_lang = is_expected_lang(lang, expect_lang, start_tag)
        if not found_expected_lang:
            text[expect_lang][sections[expect_lang][-1]].append("")

        prev_line = orig_line
        prev_he_title = is_he_title

    post_schema(root, title)
    print "FINAL COUNT {} out of {}".format(note_counter, len(notes))
    return verify_he_en_same_size(text, sections, flat_to_multi, heb_flat_to_eng)
'''

'''
def post_schema(root, title):
    root.validate()
    if root.children[-1].children == []:
        flip_schema_to_ja(root)
    index = {"title": title, "schema": root.serialize(), "categories": ["Liturgy"]}
    post_index(index, server=SERVER)

def create_node(start_tag, he_title, en_title, root, curr_schema_node):
    if "1" in start_tag:
        node = JaggedArrayNode()
        node.add_primary_titles(en_title, he_title)
        node.add_structure(["Paragraph"])
        curr_schema_node.append(node)
        return curr_schema_node
    else:
        assert "t" in start_tag
        if curr_schema_node and curr_schema_node.children == []:
            flip_schema_to_ja(root)

        node = SchemaNode()
        node.add_primary_titles(en_title, he_title)
        root.append(node)
        return node


def flip_schema_to_ja(root):
    node_to_change = root.children[-1]
    new_node = JaggedArrayNode()
    en, he = node_to_change.primary_title("en"), node_to_change.primary_title("he")
    new_node.add_primary_titles(en, he)
    new_node.add_structure(["Paragraph"])
    root.children = root.children[0:-1]
    root.append(new_node)

def add_to_map(flat_to_multi, current_outer_section, current_section, flat_title, start_tag, original_title):
    if start_tag == "@c2":
        assert current_outer_section, "No outer section"
        assert current_section, "No section"
        flat_to_multi[flat_title] = "{}, {}, {}".format(current_outer_section, current_section, original_title)
    elif start_tag == "@c1":
        assert current_outer_section, "No outer section"
        current_section = original_title
        flat_to_multi[flat_title] = "{}, {}".format(current_outer_section, current_section)
    elif start_tag == "@ct":
        current_outer_section = original_title
        current_section = None
        flat_to_multi[flat_title] = current_outer_section

    return current_section, current_outer_section


def set_flat_title(line, sections, text, lang):
    line += "1"
    while line in sections[lang]:
        line = line[0:-1] + str(int(line[-1]) + 1)
    text[lang][line] = []
    sections[lang].append(line)
    return line



def fix_prev_he_title(text, sections):
    not_real_title = sections['he'][-1]
    text['he'].pop(not_real_title)
    sections['he'] = sections['he'][0:-1]
    he_current_section = sections['he'][-1]
    text['he'][he_current_section].append(not_real_title)


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


def verify_he_en_same_size(text, sections, flat_to_multi, heb_flat_to_eng):
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
    return text, zip_en_he, flat_to_multi, heb_flat_to_eng

def force_tag_lower_case(line):
    return line[0:3].lower() + line[3:]

def is_expected_lang(curr_lang, expect_lang, start_tag):
    '''
    :return: tuple that tells us what language to expect for the next line and True if the language we expected
    for this line was correct
    '''
    if expect_lang == curr_lang:
        if expect_lang == 'en':
            return 'he', True
        else:
            return 'en', True

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
    bold = start_tag.startswith("@c") or start_tag.startswith("@kt") or "b" in start_tag
    if not bold and times == 0:
        return reverse(is_bold, start_tag)

    return bold

def is_title(start_tag, text, lang, prev_he_title, times=0):
    if lang == 'en' and len(text['en']) - len(text['he']) == 0 and not prev_he_title:
        return False
    #the above prevents making something a title when there's english but no hebrew

    is_title_bool = start_tag.startswith("@ct") or start_tag.startswith("@kt") or start_tag.startswith("@c2") or start_tag.startswith("@c1") or start_tag.startswith("@k1")
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

    line = line.replace("@hh", "").replace("@ee", "").replace("±", "—").replace("׀", "–")
    if return_start_tag:
        return line, start_tag
    else:
        return line

def post_en_he(text, zipped_list, title, vtitle, vsource, flat_to_multi):
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
        en = flat_to_multi[en]
        en = en.replace("\xe2\x80\x99", "'")
        print en
        if send_text_en['text'] != []:
            post_text("{}, {}".format(title, en), send_text_en, server=SERVER)
        if send_text_he['text'] != []:
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

'''
Idea is to use flat_to_multi and heb_to_eng
We use beautiful soup to get order of nodes
Then each one we divide up by comma and use heb_to_eng to reconstruct it
'''

def get_heb_nonflat_to_en(name, heb_nonflat_to_en):
    if name not in heb_nonflat_to_en:
        print name
        return "not found"
    else:
        return heb_nonflat_to_en[name]

def construct_full_paths(workflowy, heb_nonflat_to_en):
    soup = BeautifulSoup(open(workflowy)).contents[0].contents[0].contents[0].contents
    soup = [el for el in soup if el != "\n"][1:]
    nodes = []
    for el in soup:
        el_name = el.attrs['text'].encode('utf-8')
        title = get_heb_nonflat_to_en(el_name, heb_nonflat_to_en)
        nodes.append("{}".format(title))
        el = [sub_el for sub_el in el if sub_el != "\n"]
        if len(el) > 0:
            for sub_el in el:
                sub_el_name = sub_el.attrs['text'].encode('utf-8')
                subtitle = get_heb_nonflat_to_en(sub_el_name, heb_nonflat_to_en)
                nodes.append("{}, {}".format(title, subtitle))
                sub_el = [x for x in sub_el if x != '\n']
                if len(sub_el) > 0:
                    for sub_sub_el in sub_el:
                        sub_sub_el_name = sub_sub_el.attrs['text'].encode('utf-8')
                        sub_subtitle = get_heb_nonflat_to_en(sub_sub_el_name, heb_nonflat_to_en)
                        nodes.append("{}, {}, {}".format(title, subtitle, sub_subtitle))


    for node in nodes:
        print node
    return nodes


def create_schema(heb_nonflat_to_eng, workflowy, en_title, he_title):
    count = 0
    found_first_line = False
    en_file = open("english_{}".format(workflowy), 'w')
    with open(workflowy) as file:
        for line in file:
            he_path = re.findall("""<outline text="(.*?)"\s?/?>""", line)
            if he_path:
                if not found_first_line:
                    found_first_line = True
                    en_file.write('<outline text="{} / {}">\n'.format(he_title.encode('utf-8'), en_title))
                old_path = he_path[0]
                new_path = old_path + " / " + heb_nonflat_to_eng[old_path.replace("&quot;", '"')]
                line = line.replace(old_path, new_path)
                count += 1
            elif "outline" not in line and found_first_line: #if it's not outline tag and found first line of outline tag, then we are at the end
                en_file.write("</outline>\n")
                found_first_line = False #this way "</outline>" is only added once

            en_file.write(line.replace("\xe2\x80\x99", "'"))

    en_file.close()


if __name__ == "__main__":
    rosh_hashana_dict = {}
    rosh_hashana_dict["notes_file"] = "Rosh Hashanah Ashkenaz/Plain Text/Notes.txt"
    rosh_hashana_dict["content_file"] = "Rosh Hashanah Ashkenaz/Plain Text/Rosh Hashanah.txt"
    rosh_hashana_dict["title"] = "Machzor Rosh Hashanah Ashkenaz Interlinear"
    rosh_hashana_dict["schema"] = "Rosh Hashanah_schema.txt"
    rosh_hashana_dict["workflowy"] = "Rosh Hashanah_workflowy.xml"
    rosh_hashana_dict["heTitle"] = u"מצודה ראש השנה מחזור"
    rosh_hashana_dict["versionTitle"] = "The Metsudah Machzor; Metsudah Publications, New York"
    rosh_hashana_dict["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH000996925"

    yom_kippur_dict = dict(rosh_hashana_dict)
    for key, value in yom_kippur_dict.items():
        yom_kippur_dict[key] = value.replace("Rosh Hashanah", "Yom Kippur")

    yom_kippur_dict["heTitle"] = u"מחזור ליום כיפור - אשכנז"

    for sefer in [yom_kippur_dict]:
        notes = get_notes(sefer["notes_file"])
        parsed_text, zip_en_he_names, flat_to_multi, heb_flat_to_eng = parse_file(sefer["content_file"], notes, sefer["title"], sefer["heTitle"])
        heb_nonflat_to_eng = {}
        for k,v in heb_flat_to_eng.items():
            k = k[0:-1]
            heb_nonflat_to_eng[k] = v[0:-1]
        #full_paths = construct_full_paths(sefer["workflowy"], heb_nonflat_to_eng)
        #create_schema(heb_nonflat_to_eng, sefer["workflowy"], sefer["title"], sefer["heTitle"])
        post_en_he(parsed_text, zip_en_he_names, sefer["title"], sefer["versionTitle"], sefer["versionSource"], flat_to_multi)