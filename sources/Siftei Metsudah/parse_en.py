# -*- coding: utf-8 -*-
import re
from sefaria.model import *
from sources.functions import *
from glob import glob


def check_pasuk_order(lines, book, lang='en',):
    curr_pasuk = 0
    perek = 1
    starters = []
    for line in lines:
        line = line.decode('utf-8')
        if book == "Siftei":
            has_pasuk = re.findall("^\[(\d+)\]", line) if lang == 'en' else re.findall(u"^\((.{1,3})\)", line)
        elif book == "Rashi":
            has_pasuk = re.findall("^\d+", line) if lang == 'en' else re.findall(u"^\((.{1,3})\)", line)
        assert len(has_pasuk) in [0, 1]
        for xml_tag in re.findall("<.*?>", line):
            line = line.replace(xml_tag, "")
        for TOG_tag in re.findall("@.{2}", line):
            line = line.replace(TOG_tag, "")

        if has_pasuk:
            new_pasuk = int(has_pasuk[0]) if lang == 'en' else getGematria(has_pasuk[0])
            if new_pasuk <= curr_pasuk:
                perek += 1
                starters.append((perek, new_pasuk, line))

            curr_pasuk = new_pasuk

    return perek, starters


def convert_one_file(file, marker="@p1"):
    lines = []
    big_line = ""
    with open(file) as f:
        f = list(f)
        for count, line in enumerate(f):
            assert len(line.split('\n')) == 2
            line = line[0:-1]
            big_line += line
    lines = big_line.split(marker)[1:]
    return lines


def produce_report(book, comments, torah, lang='en'):
    writer = UnicodeWriter(open("{}_{}_{}.csv".format(book, lang, torah), 'w'))
    writer.writerow(["Assumed to be correct references", "Siftei Chachamim comment"])
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
            lines += convert_one_file(dir+"/"+file, marker="@sc") if i != 1 else convert_one_file(dir+"/"+file, marker="@sp")
        else:
            lines += convert_one_file(dir + "/" + file, marker="@P")
    return lines



if __name__ == "__main__":
    '''
    Check if Pasuk information alone gives us all 50 chapters
    If it doesn’t work, check Hebrew and English versions that the pasuk go in same order and if they do then Use DH of Hebrew to figure out what Perek we are in
    '''
    results = []
    for book in [file for file in os.listdir(".") if os.path.isdir(file)]:
        eng_title = "SE" if book == "Siftei" else "RE"
        he_title = "SH" if book == "Siftei" else "RH"
        print book
        for lang in ['en', 'he']:
            print lang
            for i in range(5):
                if lang == 'en':
                    file = "{}/{}{}.txt".format(book, i + 1, eng_title)
                    lines = convert_one_file(file)
                else:
                    lines = convert_he(book, i, he_title)
                perek_total, comments = check_pasuk_order(lines, book, lang=lang)
                produce_report(book, comments, library.get_indexes_in_category("Torah")[i], lang=lang)
                print perek_total
