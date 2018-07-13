# -*- coding: utf-8 -*-

import json
import re
import sys
sys.path.insert(1, '../genuzot')
from hebrew import *
import helperFunctions as Helper


# Helper function for extracting chapter numbers
def extract_chapter_numbers(text):
    chapter_numbers = re.findall(r"(?<=\[פרק\])\s?\[.*(?=\]\.?\s?\[פרק\])", text)

    chapter_numerals = []
    for number in chapter_numbers:
        number = number.replace("[", "").strip()
        chapter_numerals.append(decode_hebrew_numeral(number.decode('utf-8')))

    return chapter_numerals


# Helper function for extracting verse numbers
def extract_verse_numbers(text):
    verse_numbers = re.findall(r"(?<=\[פסוק\]).*(?=\[פסוק\])", text)
    verse_numerals = []
    for number in verse_numbers:
        number = re.sub(r"\.|\'|״|׳|\"", "", number).strip()
        # For range of verses, code currently only stores first verse
        if "-" in number:
            verse_range = number.split("-")
            begin = decode_hebrew_numeral(verse_range[0].decode('utf-8'))
            verse_numerals.append(begin)
        elif "־" in number:
            verse_range = number.split("־")
            begin = decode_hebrew_numeral(verse_range[0].decode('utf-8'))
            verse_numerals.append(begin)
        else:
            verse_numerals.append(decode_hebrew_numeral(number.decode('utf-8')))

    return verse_numerals


# Function for printing parsed text in a readable way
def print_parsed_text(parsed_text):
    for x in range(len(parsed_text)):
        if parsed_text[x] is not None:
            for y in range(len(parsed_text[x])):
                if parsed_text[x][y] is not None:
                    print "Chapter {} Verse {} \n".format(x+1, y+1) + parsed_text[x][y]


def parse_text_section(text, footnote_list, links, section=""):
    chap_nums = extract_chapter_numbers(text)
    parsed_text = [[] for x in range(chap_nums[-1])]
    footnotes_organized = [[] for x in range(chap_nums[-1])]
    chapters = re.split(r"\[פרק\].*\[פרק\]\s+", text)
    title_text = chapters.pop(0)
    footnote_offset = 0
    for i in range(len(chapters)):
        verse_nums = extract_verse_numbers(chapters[i])
        chap_text = []
        chapter_footnotes = []
        verses = re.split(r"\[פסוק\].*\[פסוק\]\s+", chapters[i])
        verses.remove("")
        for j in range(len(verses)):
            verse_footnotes = []
            verse = re.sub(r"\[ד\"ה\](.*?)\[ד\"ה\]", r"<b> \1 </b>", verses[j]).strip()
            # Find all footnotes, create links, and then remove footnote notation from text
            footnotes = re.findall(r"\((\*?..)(\d\d?)\)", verse)
            for footnote in footnotes:
                number = int(footnote[1])
                letter = footnote[0]
                if letter[0] == '*':
                    footnote_offset = 1
                    letter = letter[1:]
                letter_value = ord(letter[0]) + ord(letter[1]) - 358
                if letter_value == 1:
                    footnote_offset = 0
                verse_footnotes.append(footnote_list[number - 1][letter_value - 1 + footnote_offset])
            verse = re.sub(r"\(\*?..\d\d?\)", "", verse)
            chap_text.append(verse)
            chapter_footnotes.append(verse_footnotes)
            link_obj = {
                "type": "midrash",
                "refs": ["Mekhilta DeRabbi Shimon Bar Yochai %s %d:%d" % (section, chap_nums[i], verse_nums[j]),
                         "Exodus %d:%d" % (chap_nums[i], verse_nums[j])]
                }
            links.append(link_obj)
        parsed_text[chap_nums[i] - 1] = chap_text
        footnotes_organized[chap_nums[i] - 1] = chapter_footnotes

    return {"text": parsed_text, "notes": footnotes_organized}


def parse_footnotes(text):
    parsed_text = [["" for x in range(28)] for x in range(77)]

    # Add footnotes on footnotes back into text.
    notes_on_notes = re.findall(r"\n\(\*\)(.*\n?.*)\(\*\)", text)
    text = re.sub(r"\n\(\*\).*\n?.*\(\*\)", "", text)

    footnotes = re.split(r"(\*?[^\d\s]{2})(\d\d?)\)", text)
    note_counter = 0
    offset = 0  # In case of footnote with letter and asterix,
    # offset all remaining footnotes in that section to compensate for extra letter
    for i in range(1, len(footnotes), 3):
        letter = footnotes[i]
        if letter[0] == '*':
            offset = 1
            letter = letter[1:]
        letter_value = ord(letter[0]) + ord(letter[1]) - 358
        if letter_value == 1:  # Reset offset at every new numbered section
            offset = 0
        number = int(footnotes[i+1])
        footnote = footnotes[i+2].strip()
        parsed = re.subn(r"\(\*\)", "", footnote)
        parsed_footnote = parsed[0]
        was_replaced = parsed[1]
        if was_replaced != 0:
            parsed_footnote += notes_on_notes[note_counter]
            note_counter += 1
        parsed_text[number - 1][letter_value - 1 + offset] = parsed_footnote
    return parsed_text


# Save all three texts
def save_texts(main, additions, main_footnotes, added_footnotes):
    main_text = {
        "title": "Mekhilta DeRabbi Shimon Bar Yochai",
        "versionTitle": "Mechilta de-Rabbi Simon b. Jochai, Dr. D. Hoffman, Frankfurt 1905",
        "versionSource": "https://openlibrary.org/books/OL23318277M/Mekhilta_de-Rabi_Shimon_ben_Yoai_al_sefer_Shemot",
        "language": "he",
        "text": main,
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Mekhilta DeRashbi.json", 'w') as out:
        json.dump(main_text, out)

    text_additions = {
        "title": "Mekhilta DeRabbi Shimon Bar Yochai Additions",
        "versionTitle": "Mechilta de-Rabbi Simon b. Jochai, Dr. D. Hoffman, Frankfurt 1905",
        "versionSource": "https://openlibrary.org/books/OL23318277M/Mekhilta_de-Rabi_Shimon_ben_Yoai_al_sefer_Shemot",
        "language": "he",
        "text": additions,
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Mekhilta DeRashbi Added.json", 'w') as out:
        json.dump(text_additions, out)

    main_footnotes_text = {
        "versionTitle": "Mechilta de-Rabbi Simon b. Jochai, Dr. D. Hoffman, Frankfurt 1905",
        "versionSource": "https://openlibrary.org/books/OL23318277M/Mekhilta_de-Rabi_Shimon_ben_Yoai_al_sefer_Shemot",
        "language": "he",
        "text": main_footnotes,
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Mekhilta DeRashbi Footnotes 1.json", 'w') as out:
        json.dump(main_footnotes_text, out)

    added_footnotes_text = {
        "versionTitle": "Mechilta de-Rabbi Simon b. Jochai, Dr. D. Hoffman, Frankfurt 1905",
        "versionSource": "https://openlibrary.org/books/OL23318277M/Mekhilta_de-Rabi_Shimon_ben_Yoai_al_sefer_Shemot",
        "language": "he",
        "text": added_footnotes,
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Mekhilta DeRashbi Footnotes 2.json", 'w') as out:
        json.dump(added_footnotes_text, out)


def save_links(links):
    Helper.mkdir_p("preprocess_json/links/")
    with open("preprocess_json/links/Mekhilta DeRashbi links.json", 'w') as out:
        json.dump(links, out)


def post_texts():

    with open("preprocess_json/Mekhilta DeRashbi.json", 'r') as filep:
        json_text = filep.read()
    Helper.postText("Mekhilta DeRabbi Shimon Bar Yochai", json_text, False)

    with open("preprocess_json/Mekhilta DeRashbi Added.json", 'r') as filep:
        json_text = filep.read()
    Helper.postText("Mekhilta DeRabbi Shimon Bar Yochai Additions", json_text, False)

    with open("preprocess_json/Mekhilta DeRashbi Footnotes 1.json", 'r') as filep:
        json_text = filep.read()
    Helper.postText("Footnotes on Mekhilta DeRabbi Shimon Bar Yochai", json_text, False)

    with open("preprocess_json/Mekhilta DeRashbi Footnotes 2.json", 'r') as filep:
        json_text = filep.read()
    Helper.postText("Footnotes on Mekhilta DeRabbi Shimon Bar Yochai Additions", json_text, False)


def post_links():
    with open("preprocess_json/links/Mekhilta DeRashbi links.json", 'r') as filep:
        links_arr = json.load(filep)
    Helper.postLink(links_arr)


def run_parser():
    links = []

    # Parse Footnotes
    with open("Source/Mekhilta d'Rashbi footnotes.txt", 'r') as filep:
        file_text = filep.read()
    footnotes = parse_footnotes(file_text)
    # Parse Main Text
    with open("Source/Mekhilta d'Rashbi text.txt", 'r') as filep:
        file_text = filep.read()
    parashot = re.findall(r"פרשת\s\S*\s?\S*\.", file_text)
    file_text = re.sub(r"פרשת\s\S*\s?\S*\.", "", file_text)
    sections = re.split(r"הוספה\.", file_text)
    main = parse_text_section(sections[0], footnotes, links)
    additions = parse_text_section(sections[1], footnotes, links, "Additions")
    save_texts(main["text"], additions["text"], main["notes"], additions["notes"])
    save_links(links)
    post_texts()
    post_links()

if __name__ == '__main__':
    run_parser()
