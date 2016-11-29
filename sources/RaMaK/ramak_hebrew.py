# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
from XML_to_JaggedArray import XML_to_JaggedArray
import sys
import codecs
sys.path.append('../')
from functions import *
sys.path.append('../../../')
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray
import bleach


def dealWithEnd(subject, lines, root, subjects):
    subjects.append(subject)
    curr_letter_num = 0
    eng_letters = ["Alef", "Bet", "Gimel", "Daled", "Heh", "Vav", "Zayin", "Chet", "Tet", "Yod", "Kaf", "Lamed", "Mem", "Nun", "Samekh",
                    "Ayin", "Peh", "Tzadi", "Kof", "Resh", "Shin", "Tav"]
    heb_letters = {}

    for line in lines:
        line = line.replace("<p>", "")
        line = re.sub(u'(\n|\r)', u'', line)
        ot = re.compile(ur"^אות ([\u05d0-\u05ea]{1,2})")
        match = ot.search(line)
        if match:
            curr_letter_num += 1
        else:
            if curr_letter_num not in heb_letters:
                heb_letters[curr_letter_num] = []
            heb_letters[curr_letter_num].append(line)

    return root.array(), heb_letters, subjects


def parse():
    with codecs.open('hebrew_or_neerav.html', 'r', 'windows-1255') as infile:
        lines = infile.readlines()
    gate, chapter, whole_text = -1, -1, []
    root = JaggedArray([[]])
    found_beginning = False
    next_line_subject = False
    subjects = []
    main_pattern = re.compile(ur'^<b>חלק ([\u05d0-\u05ea]{1,2}) פרק ([\u05d0-\u05ea]{1,2})')

    for index, line in enumerate(lines):
        line = line.replace("(", "(<sub>")
        line = line.replace(")", "</sub>)")
        if next_line_subject == True:
            subjects.append(line)
            next_line_subject = False
            continue
        if line.find(u"חלק שביעי חלק הכינויים א") >= 0:
            return dealWithEnd(lines[index+1], lines[index+2:], root, subjects)
        main_match = main_pattern.search(line)
        if main_match:
            if found_beginning:
                root.set_element([gate, chapter], whole_text, pad=[])
                whole_text = []
            else:
                found_beginning = True
            new_gate, new_chapter = getGematria(main_match.group(1))-1, getGematria(main_match.group(2))-1
            if new_gate - gate > 1 or new_chapter - chapter > 1:
                print 'skip found at Gate {} Chapter {}'.format(new_gate+1, new_chapter+1)
            gate, chapter = new_gate, new_chapter
        elif found_beginning:
            if len(line.split(" ")) == 2 and line.find(u"חלק") >= 0:
                next_line_subject = True
                continue
            if len(line.split(" ")) == 2 and line.find(u"פרק") >= 0:
                continue
            line = bleach.clean(line, tags=[], strip=True)
            if line.isspace():
                continue
            line = re.sub(u'(\n|\r)', u'', line)
            whole_text.append(line)
        else:
            continue
    else:
        root.set_element([gate, chapter], whole_text)


def makeSchema():
    root = SchemaNode()
    root.key = "Or Neerav"


if __name__ == "__main__":
    first_part, second_part, subjects = parse()
    roman_arr = ["I", "II", "III", "IV", "V", "VI"]
    second_part = convertDictToArray(second_part)
    for i in range(6):
        part_text = {
                    "text": first_part[i],
                    "language": "he",
                    "versionSource": "http://www.ktav.com/index.php/moses-cordovero-s-introduction-to-kabbalah.html",
                    "versionTitle": "Moses Cordovero’s Introduction to Kabbalah, Annotated trans. of Or ne'erav, Ira Robinson, 1994."
                }
        post_text("Or Neerav, PART "+roman_arr[i], part_text)
        subject_text = {
                    "text": [subjects[i]],
                    "language": "he",
                    "versionSource": "http://www.ktav.com/index.php/moses-cordovero-s-introduction-to-kabbalah.html",
                    "versionTitle": "Moses Cordovero’s Introduction to Kabbalah, Annotated trans. of Or ne'erav, Ira Robinson, 1994."
                }
        post_text("Or Neerav, PART "+roman_arr[i]+", Subject", subject_text)



    partvii_text = {
            "text": [subjects[6]],
            "language": "he",
            "versionSource": "http://www.ktav.com/index.php/moses-cordovero-s-introduction-to-kabbalah.html",
            "versionTitle": "Moses Cordovero’s Introduction to Kabbalah, Annotated trans. of Or ne'erav, Ira Robinson, 1994."
        }

    post_text("Or Neerav, PART VII, Subject", partvii_text)

    letters_eng = ["Alef", "Bet", "Gimel", "Daled", "Heh", "Vav", "Zayin", "Chet", "Tet", "Yod", "Kaf", "Lamed", "Mem", "Nun", "Samekh",
                    "Ayin", "Peh", "Tzadi", "Kof", "Resh", "Shin", "Tav"]

    for index, section in enumerate(second_part):
        ref = "Or Neerav, PART VII, Letter {}".format(letters_eng[index])
        send_text = {
            "text": section,
            "language": "he",
            "versionSource": "http://www.ktav.com/index.php/moses-cordovero-s-introduction-to-kabbalah.html",
            "versionTitle": "Moses Cordovero’s Introduction to Kabbalah, Annotated trans. of Or ne'erav, Ira Robinson, 1994."
        }
        post_text(ref, send_text)
