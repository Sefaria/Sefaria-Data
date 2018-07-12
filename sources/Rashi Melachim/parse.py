import django
django.setup()
import re
from sefaria.model import *
from sources.functions import is_english_word, any_english_in_str, any_hebrew_in_str, getGematria, convertDictToArray, post_text, post_index
from collections import Counter

def combine_en_and_he(lines):
    # organizes lines by segment with two versions: en & he
    # and also provides validation checking
    combined = []
    how_many_lines_moved = 0
    lines = [el.replace("\r\n", "") for el in lines if el != "\r\n"]
    for line_n, line in enumerate(lines):
        if (how_many_lines_moved + line_n) % 2 == 0:
            #english
            assert any_english_in_str(line)
            combined.append(line)
        else:
            #hebrew:
            #after removing tags, there should be no English
            line_wout_tags = remove_tags(line)
            if any_english_in_str(line_wout_tags):
                #this is English, so put it at the end of the previous line which we know is English
                combined[-1] += " "+line
                how_many_lines_moved += 1
                continue
            combined[-1] += "\n"+line
    return combined


def remove_tags(line):
    important_tags = {"@it": "<i>", "@ic": "</i>"}
    tags = re.findall("@[a-zA-Z0-9]{2}", line)
    for tag in set(tags):
        if tag not in important_tags:
            line = line.replace(tag, "")
        else:
            line = line.replace(tag, important_tags[tag])
    return line


def get_pasuk_chapter(en, he, curr_pasuk, curr_chapter):
    he = getGematria(he)
    assert int(en) == he
    new_pasuk = int(en)
    if new_pasuk < curr_pasuk:
        curr_chapter = curr_chapter + 1
    return new_pasuk, curr_chapter


def post_rashi(en_text, he_text, title, server):
    if "II" in title:
        title = "Rashi on II Kings"
    else:
        title = "Rashi on I Kings"
    for lang, text in [("en", en_text), ("he", he_text)]:
        for ch_num in text.keys():
            text[ch_num] = convertDictToArray(text[ch_num])
        text = convertDictToArray(text)
        send_text = {
            "text": text,
            "language": lang,
            "versionTitle": "Metsudah {} -- {}".format(title, lang),
            "versionSource": "http://www.sefaria.org"
        }
        post_text(title, send_text, server=server)

def get_ftnotes(note_file):
    with open(note_file) as f:
        lines = list(f)
        combined = " ".join(lines)
        ftnotes_dict = {}
        chapters = combined.split("@fn@fn")[1:]
        for ch_num, chapter in enumerate(chapters):
            ftnotes_dict[ch_num+1] = {}
            verses = chapter.split("@ms")
            for verse_n, verse in enumerate(verses):
                while not verse[0].isdigit():
                    verse = verse[1:]
                digit = re.compile("^(\d+)").match(verse)
                verse = verse.replace(digit.group(1), "", 1)
                ftnotes_dict[ch_num+1]["@nt"+digit.group(1)] = verse
            c = Counter(ftnotes_dict[ch_num+1].keys())
            assert c.most_common(1)[0][1] == 1
        return ftnotes_dict

def replace_ftnotes(curr_chapter, line, ftnotes_dict):
    if "@nt" not in line:
        return line
    line = line.replace("@c3", "")
    notes_in_line = re.findall("(@nt(\d+))", line)

    prev_ftnote = int(notes_in_line[0][1])
    for note in notes_in_line:
        note_text = note[0]
        digit = note[1]
        if int(digit) < prev_ftnote:
            pass
        prev_ftnote = int(digit)
        if note_text not in ftnotes_dict.keys():
            print "Chapter {} footnote {}".format(curr_chapter, note_text)
            return line
        prev = ftnotes_dict[note_text]
        ftnotes_dict[note_text] = ftnotes_dict[note_text].replace("\n", "")
        i_tag = "<sup>{}</sup><i class='footnote'>{}</i>".format(digit, ftnotes_dict[note_text])
        line = line.replace(note_text, i_tag)
    return line

def validate(en_match, he_match, en, he):
    if not en_match:
        if not ("@d1" in en or "@d2" in en):
            print "Hebrew but no English"
            print line
            print
            he = ""
        else:
            he = he_match.group(1)
    if not he_match:
        if not ("@d1" in he or "@d2" in he):
            print "English but no Hebrew"
            print line
            print
            en = ""
        else:
            en = en_match.group(1)
    return he, en

def create_new_pasuk(text, curr_chapter, curr_pasuk, en_continuous_segment, he_continuous_segment):
    start_dh_pattern = re.compile(".*?\[(.{1,4})\](.*)")
    en_match = start_dh_pattern.match(en_wout_tags)
    he_match = start_dh_pattern.match(he_wout_tags)
    # if not en_match or not he_match:
    #     print line
    #     continue

    # first put continuous_segments in text dictionary and then start new continuous_segments based on this pasuk
    if en_continuous_segment:
        text[curr_chapter][curr_pasuk].append(en_continuous_segment)
        he_text[curr_chapter][curr_pasuk].append(he_continuous_segment)

    curr_pasuk, curr_chapter = get_pasuk_chapter(en_match.group(1), he_match.group(1), curr_pasuk, curr_chapter)
    if curr_chapter not in text.keys():
        text[curr_chapter] = {}
        he_text[curr_chapter] = {}
    if curr_pasuk not in text[curr_chapter].keys():
        text[curr_chapter][curr_pasuk] = []
        he_text[curr_chapter][curr_pasuk] = []
    if curr_chapter == curr_pasuk == -1:
        print line
        print

    en_continuous_segment = en_dh = en_match.group(2)
    he_continuous_segment = he_dh = he_match.group(2)
    en_continuous_segment = bold(en_continuous_segment)
    he_continuous_segment = bold(he_continuous_segment)
    return en_continuous_segment, he_continuous_segment, curr_chapter, curr_pasuk


if __name__ == "__main__":
    base = "Rashi Mel I"
    bases = [base+".txt", base+"I.txt"]
    notes = [base+" notes.txt", base+"I notes.txt"]
    en_dh = he_dh = ""
    bold = lambda x: "<b>" + x + "</b>"
    unbold = lambda x: x.replace("<b>", "").replace("</b>", "")
    en_continuous_segment = he_continuous_segment = ""
    for base_file, note_file in zip(bases, notes):
        print base_file
        ftnotes = get_ftnotes(note_file)
        text = {1: {1: []}}
        he_text = {1: {1: []}}
        curr_pasuk = curr_chapter = 1
        dh_pattern = re.compile(".*?(@[D|d]1.*?@d2)")  # only applies to second third fourth DHs in pasuk
        same_en_dh_next_line = re.compile(".*?@ld(.*)(?:@d2)?") #re.compile(".*?(@ld.*?@d2)")
        same_he_dh_next_line = re.compile(".*?(@dl.*?@d2)")
        with open(base_file) as f:
            lines = list(f)
            en_he_lines = combine_en_and_he(lines)
            for line_n, line in enumerate(en_he_lines):
                ftnotes_to_replace = ftnotes[curr_chapter]
                line = replace_ftnotes(curr_chapter, line, ftnotes_to_replace)
                en, he = line.split("\n")
                line_wout_tags = remove_tags(line)
                en_wout_tags, he_wout_tags = line_wout_tags.split("\n")
                if "@1P" in line: #this is the beginning of a pasuk, look for DH and start continuous segment AND save previous continuous segment in text
                    en_continuous_segment, he_continuous_segment, curr_chapter, curr_pasuk = create_new_pasuk(text, curr_chapter, curr_pasuk, en_continuous_segment, he_continuous_segment)
                else:
                    he_match = dh_pattern.match(he)
                    same_he_match = same_he_dh_next_line.match(he)
                    if not he_match and not same_he_match: #not a DH
                        en_continuous_segment += " " + en_wout_tags
                        he_continuous_segment += " " + he_wout_tags
                    if same_he_match: #same DH from previous line such as "The cat drank\n the milk"

                        same_en_match = same_en_dh_next_line.match(en)
                        same_he, same_en = validate(same_en_match, same_he_match, en, he)
                        same_he = remove_tags(same_he)
                        same_en = remove_tags(same_en)
                        en_continuous_segment = bold(unbold(en_continuous_segment) + " " + same_en)
                        he_continuous_segment = bold(unbold(he_continuous_segment) + " " + same_he)
                    elif he_match: #this case is where new DH in the same pasuk
                        en_match = dh_pattern.match(en)
                        new_he, new_en = validate(en_match, he_match, en, he)
                        if en_continuous_segment:
                            text[curr_chapter][curr_pasuk].append(en_continuous_segment)
                            he_text[curr_chapter][curr_pasuk].append(he_continuous_segment)
                        en_continuous_segment = bold(remove_tags(new_en))
                        he_continuous_segment = bold(remove_tags(new_he))


            post_rashi(text, he_text, base_file, "http://draft.sefaria.org")
