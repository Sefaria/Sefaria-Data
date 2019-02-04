#encoding=utf-8
import requests
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError, BookNameError
from num2words import num2words
from word2number import w2n
import shutil
import os
import re
from collections import Counter
from sources.functions import post_index, post_text, convertDictToArray, add_category, get_index_api
from bs4 import BeautifulSoup
import textract
import traceback
import sys

SERVER = "http://ste.sandbox.sefaria.org"
section_referenced_not_in_mishnah = []
mishnah_wout_numbers_explanation_has = []
mishnah_wout_numbers_explanation_wout = []
mishnah_sections_more_than_explanation_sections = []
# def download_sheets(self):
#     indexes = library.get_indexes_in_category("Mishnah")
#     indexes = [library.get_index(i) for i in indexes]
#     for i in indexes:
#         title_for_url = " ".join(i.split()[1:]).lower()
#         chapters = i.all_section_refs()
#         for ch_num, chapter in enumerate(chapters):
#             mishnayot = chapter.all_segment_refs()
#             for mishnah_num, mishnah in enumerate(mishnayot):
#                 headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
#                 response = requests.get("http://learn.conservativeyeshiva.org/{}-chapter-{}-mishnah-{}.html".format(title_for_url, chapter, mishnah), headers=headers)
#                 print "sleeping"
#                 with open("{}.html".format(i), 'w') as f:
#                     f.write(response.content)
def get_response(new_name, headers):
    not_found = True
    while not_found:
        try:
            response = requests.get("http://learn.conservativeyeshiva.org/{}".format(new_name), headers=headers)
            not_found = False
        except requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError:
            print "trying again.."
        return response



def get_mishnah_on_multiple_lines(category, sefer, file, page=1):
    replace_with = {"Chullin": "Hullin", "Challah": "Hallah", "Yevamot": "Yevamoth", "Ketubot": "Ketuboth",
                    "Makhshirin": "Makshirin", "Tahorot": "Toharot", "Oholot": "Ohalot", "Oktzin": "Oktzim",
                    "Zevachim": "Zevahim", "Menachot": "Menahot", "Kinnim": "Kinim", "Chagigah": "Hagigah",
                    "Beitzah": "Betzah", "Pesachim": "Pesahim", "Avot": "Avoth",
                    "Horayot": "Horayoth", "Eduyot": "Eduyoth", "Shevuot": "Shevuoth"}
    modified_sefer = sefer
    for our_sp, their_sp in replace_with.items():
        modified_sefer = modified_sefer.replace(our_sp, their_sp)
    headers = {
        'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    not_found = True
    url = "http://learn.conservativeyeshiva.org/topic/rabbinic-texts/mishnah/my-seder-{}/{}/".format(category.lower(), modified_sefer.lower())
    if page > 1:
        url += "page/{}".format(page)
    response = None
    while not_found:
        try:
            response = requests.get(url, headers=headers)
            not_found = False
        except requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError:
            print "trying again.."
    if response.status_code == 200:
        content = response.content
        soup = BeautifulSoup(content)
        a_tag_dict = {a_tag.text: a_tag.attrs.get("href", "") for a_tag in soup.find_all("a")}
        ch_mishnah = file.split(" ")[-1]
        chapter, mishnah = ch_mishnah.split("-")
        chapter = "Chapter " + chapter
        mishnah = "Mishnah " + mishnah.replace(".txt", "")
        new_name = "{}, {}, {}".format(sefer, chapter, mishnah)
        if new_name not in a_tag_dict.keys():
            print "Trying {}".format(page+1)
            return get_mishnah_on_multiple_lines(category, sefer, file, page+1)
        href = a_tag_dict[new_name]
        not_found = True
        response = None
        while not_found:
            try:
                response = requests.get(href, headers=headers)
                not_found = False
            except requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError:
                print "trying again.."
        soup = BeautifulSoup(response.content)
        text = soup.find_all("div", {"class": "post-content"})
        lines = text[0].text.splitlines()
        any_line_has_marker = any([True if line.startswith("a)") else False for line in lines])
        if any_line_has_marker:
            print "FOUND {}".format(file)




def get_lines_from_web(name, download_mode=True):
    replace_with = {"Chullin": "Hullin", "Challah": "Hallah", "Yevamot": "Yevamoth", "Ketubot": "Ketuboth",
                     "Makhshirin": "Makshirin", "Tahorot": "Toharot", "Oholot": "Ohalot", "Oktzin": "Oktzim",
                    "Zevachim": "Zevahim", "Menachot": "Menahot", "Kinnim": "Kinim", "Chagigah": "Hagigah",
                    "Beitzah": "Betzah", "Pesachim": "Pesahim", "Avot": "Avoth",
                    "Horayot": "Horayoth", "Eduyot": "Eduyoth", "Shevuot": "Shevuoth"}
    for word_to_replace, new_word in replace_with.items():
        name = name.replace(word_to_replace, new_word)
    book = " ".join(name.split()[0:-1])
    book = book.lower().replace(" ", "-")
    ch, mishnah = name.split()[-1].split("-")
    ch = num2words(int(ch))
    mishnah = num2words(int(mishnah[0:-4]))
    new_name = "{}-chapter-{}-mishnah-{}".format(book, ch, mishnah)
    if download_mode:
        headers = {
            'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        not_found = True
        response = get_response(new_name, headers)
        if response.status_code != 200:
            other_name = name.replace(".txt", "") + "-htm"
            other_name = other_name.replace(" ", "-")
            other_name = other_name[0].lower() + other_name[1:]
            response = get_response(other_name, headers)
            if response.status_code != 200:
                return False
        f = open(new_name, 'w')
        f.write(response.content)
        f.close()
        return response.content
    elif not download_mode:
        f = str(open(new_name))
        soup = BeautifulSoup(f)
        text = soup.find_all("div", {"class": "post-content"})
        return text[0].text.splitlines()



def get_section_num(mishnah_num):
    try:
        if type(mishnah_num) is unicode:
            mishnah_num = mishnah_num.encode('utf-8')
        if mishnah_num[0].isdigit() and not mishnah_num[-1].isdigit():  #3a
            mishnah_num = mishnah_num[0:-1]
        if len(mishnah_num) > 2:
            section_num = w2n.word_to_num(mishnah_num)
        elif mishnah_num.isdigit():
            section_num = int(mishnah_num)
        elif len(mishnah_num) == 1:  # just a letter
            section_num = ord(mishnah_num) - 64
    except ValueError:
        assert type(mishnah_num) is int, "Problem with {}".format(mishnah_num)
        section_num = mishnah_num
    return section_num

def parse(lines, sefer, chapter, mishnah, HOW_MANY_REFER_TO_SECTIONS):
    def get_first_sentence(line):
        line = line.strip()
        end = line.find(". ")
        if end != -1:
            return line[0:end]+". "
        return line+" "


    def deal_with_sections(line, text, len_mishnah):
        line = line.replace(unichr(8212), u": ")
        section = re.search(u"^\s*(In sections?|Sections?) (\S+)\s", line)

        if not section:
            if len(text) > 0:
                text[-1] += u" " + line
            else:
                text.append(line)
            return 0

        section_num_as_word = section.group(2).strip().replace(u",", u"")

        # if there is a colon at the end, we want to replace the words "Section one: ", but if it's part of the sentence like "Section one is ...", then we want to keep it
        if section.group(0).endswith(u": ") or section.group(0).endswith(u"- "):
            line = line.replace(section.group(0), "").strip()
            section_num_as_word = section_num_as_word[0:-1]


        mishnayot = []
        if section_num_as_word.find(u"-") in [1, 2]: #either 10-14 or 2-7 will be matched, this is a range
            start, end = section_num_as_word.split(u"-")
            start = get_section_num(start)
            end = get_section_num(end)
            mishnayot = range(start, end+1)
        else:
            mishnayot.append(get_section_num(section_num_as_word))

        dh = ""
        for section_num in mishnayot:
            if section_num - 1 < len_mishnah:
                dh += u"<b>{}</b> ".format(mishnah_text[section_num - 1])
            else:
                text.append(line)
                return -1

        text.append(u"{} {}".format(dh, line))




    currently_parsing = ""
    mishnah_text = []
    commentary_text = []
    orig_mishnah = []
    orig_explanation = []
    questions_text = []
    found_mishnah = found_explanation = False # must find both, whereas intro is unnecessary
    explanation_sections_text = [] #After parsing "Section One: ...", this array will contain the line in position 0 of the array
    questions_sections_text = []

    first_line = lines[0]
    # chapter_as_word = num2words(chapter).capitalize()
    mishnah_as_word = num2words(mishnah).capitalize()
    # if "Chapter {}".format(chapter_as_word) not in first_line or "Mishnah {}".format(mishnah_as_word) not in first_line:
    #     print "Problem in file {} in first line {}".format(file, first_line)
    #     return (commentary_text, mishnah_text)
    section_num = 0

    for line_n, line in enumerate(lines):
        line = line.replace("\xc3\xa2\xc2\x80\xc2\x99", "'")
        line = line.decode('utf-8')
        line = line.replace(u". . .",  u"\u2026").replace(u'—', u" ")
        line = line.strip()
        #line = line.strip().replace(unichr(151), u"").replace(unichr(146), u"")
        if "Part" in line and len(line.split()) < 10:
            return (commentary_text + questions_text, mishnah_text)
        if "Questions for Further Thought" in line:
            currently_parsing = "QUESTIONS"
            questions_text.append(u"<b>"+line+u"</b>")
        elif "Explanation" in line and len(line.split()) < 5:
            currently_parsing = "EXPLANATION"
            mishnah_text = restructure_mishnah_text(mishnah_text)
        elif len(line.split()) < 7 and ("Mishna" in line or sefer == line):
            if u"Mishnah {}".format(mishnah_as_word) != line and "Mishna" in line:
                word = line.split()[-1] #Mishnah Five -> Five
                try:
                    mishnah_inside_file = w2n.word_to_num(word)
                    complaint = u"Mishnah word different than number: {} {}:{}".format(sefer, chapter, mishnah)
                    #print complaint
                except ValueError:
                    pass
            if currently_parsing == "INTRODUCTION":
                currently_parsing = "MISHNAH"
        elif "Introduction" == line:
            commentary_text.append(u"<b>"+line+"</b>")
            currently_parsing = line.upper()
        else:
            if currently_parsing == "INTRODUCTION":
                orig_explanation.append(line)
                commentary_text[-1] += u"\n" + line
            elif currently_parsing == "EXPLANATION":
                orig_explanation.append(line)
                result = deal_with_sections(line, explanation_sections_text, len(mishnah_text))
                if result == -1:  # there was just an error
                    section_referenced_not_in_mishnah.append(file)
                    # result = deal_with_sections(line, explanation_sections_text, len(mishnah_text))
                    #return (commentary_text + questions_text, mishnah_text)
            elif currently_parsing == "QUESTIONS":
                questions_sections_text.append(line)
            elif currently_parsing == "MISHNAH":
                mishnah_text.append(line)
                orig_mishnah.append(line)

    if explanation_sections_text == []:
        mishnah_text = restructure_mishnah_text(mishnah_text)

    assert commentary_text != mishnah_text != []
    if len(mishnah_text) == 1 and len(explanation_sections_text) > 1:
        mishnah_wout_numbers_explanation_has.append(file)
    elif len(mishnah_text) == 1 and len(explanation_sections_text) == 1: #this means there was no numbering
        mishnah_wout_numbers_explanation_wout.append(file)
        explanation_sections_text[0] = u"<b>{}</b> {}".format(mishnah_text[0], explanation_sections_text[0])
    elif len(mishnah_text) > len(explanation_sections_text):
        mishnah_sections_more_than_explanation_sections.append(file)
        if len(orig_mishnah) == 0:
            print file
            print "BLANK FILE"
        else:
            orig_mishnah = restructure_mishnah_text(orig_mishnah)
            orig_mishnah = "<b>" + u" ".join(orig_mishnah) + "</b><br/>"
            orig_explanation = u"<br/>".join(orig_explanation)
            return ([orig_mishnah+orig_explanation], [orig_mishnah.replace("<b>", "").replace("<br/>", "").replace("</b>", "")])




    commentary_text += explanation_sections_text
    questions_text += questions_sections_text
    commentary_text = [el for el in commentary_text if el]
    questions_text = [el for el in questions_text if el]
    commentary_text = [el for el in commentary_text+questions_text]
    mishnah_text = [el.replace("<b>", "").replace("</b>", "").replace("<br/>", "") for el in mishnah_text]
    return (commentary_text+questions_text, mishnah_text)


def restructure_mishnah_text(old_mishnah_text):
    mishnah_text = []
    found_digit_or_char = False
    found_digit = False
    for line in old_mishnah_text:
        digit = re.search("^\d+\)", line)
        char = re.search("^[a-zA-Z]+\)", line)
        if digit:
            found_digit = True
        if digit or char:
            found_digit_or_char = True

    if not found_digit_or_char:
        return [" ".join(old_mishnah_text)]

    for line in old_mishnah_text:
        digit = re.search("^(\d+)\)", line)
        line = re.sub("^\([a-zA-Z]{1,3}\)", "", line).strip()
        line = re.sub("^[a-zA-Z]{1,3}\)", "", line).strip()
        if digit:
            pos = int(digit.group(1)) - 1
            if len(mishnah_text) > pos:
                mishnah_text[pos] += "<br/>"+line.replace(digit.group(0), "").strip()
            else:
                mishnah_text.append(line.replace(digit.group(0), "").strip())
        elif len(mishnah_text) > 0:
            mishnah_text[-1] += " " + line.strip()
        else:
            mishnah_text.append(line.strip())
    return mishnah_text

def create_index(text, sefer, post=False):
    sefer = convert_spellings(sefer)
    index = library.get_index("Mishnah " + sefer)
    seder = index.categories[-1]
    root = SchemaNode()
    en_title = "Mishnah Yomit on {}".format(index.title)
    he_title = u"משנה יומית על {}".format(index.get_title('he'))
    root.add_primary_titles(en_title, he_title)

    if "Introduction" in text.keys():
        intro = JaggedArrayNode()
        intro.add_shared_term("Introduction")
        intro.key = "intro"
        intro.add_structure(["Paragraph"])
        root.append(intro)

    default = JaggedArrayNode()
    default.key = "default"
    default.default = True
    default.add_structure(["Chapter", "Mishnah", "Comment"])
    root.append(default)
    root.validate()
    add_category(seder, ["Modern Works", "Mishnah Yomit", seder], server=SERVER)
    index = {
        "title": en_title,
        "schema": root.serialize(),
        "categories": ["Modern Works", "Mishnah Yomit", seder],
        "dependence": "Commentary",
        "base_text_titles": [index.title],
        "base_text_mapping": "many_to_one",
        "collective_title": "Mishnah Yomit",
    }
    if post:
        post_index(index, server=SERVER)


def check_all_mishnayot_present_and_post(text, sefer, file_path, post=False):
    versionTitle = "Mishnah Yomit"
    sefer = convert_spellings(sefer)
    def post_(text, path):
        send_text = {
            "language": "en",
            "text": text,
            "versionTitle": versionTitle,
            "versionSource": "http://learn.conservativeyeshiva.org/mishnah/"
        }
        try:
            if post:
                print SERVER
                post_text(path, send_text, server=SERVER)
        except UnicodeDecodeError:
            for ch_num, chapter in enumerate(text):
                for mishnah_num, mishnah in enumerate(chapter):
                    for comm_num, comment in enumerate(mishnah):
                        send_text = {
                            "language": "en",
                            "text": comment,
                            "versionTitle": versionTitle,
                            "versionSource": "http://learn.conservativeyeshiva.org/mishnah/"
                        }
                        try:
                            if post:
                                post_text("{} {}:{}:{}".format(path, ch_num+1, mishnah_num+1, comm_num+1), send_text, server=SERVER)
                        except UnicodeDecodeError:
                            print "Error posting {}".format("{} {}:{}:{}".format(path, ch_num+1, mishnah_num+1, comm_num+1))

    #first check that all chapters present
    sefer = convert_spellings(sefer)
    index = library.get_index("Mishnah " + sefer)
    en_title = "Mishnah Yomit on {}".format(index.title)
    translation = dict(text)
    for ch in text.keys():
        if ch == "Introduction":
            if post:
                post_(text[ch], "{}, Introduction".format(en_title))
            text.pop(ch)
            translation.pop(ch)
            continue
        actual_mishnayot = [el.sections[1] for el in Ref("Mishnah {} {}".format(sefer, ch)).all_segment_refs()]
        our_mishnayot = text[ch].keys()
        if len(actual_mishnayot) > len(our_mishnayot):
            actual_mishnayot = set(actual_mishnayot)
            our_mishnayot = set(our_mishnayot)
            missing = actual_mishnayot - our_mishnayot
            print "Sefer: {}, Chapter: {}".format(sefer, ch)
            print "Missing mishnayot: {}".format(list(missing))
            print
        text[ch] = zip(*convertDictToArray(text[ch], empty=("", "")))
        translation[ch] = list(text[ch][1])
        text[ch] = list(text[ch][0])
        while "" in text[ch]:
            i = text[ch].index("")
            text[ch][i] = []
    text = convertDictToArray(text)
    translation = convertDictToArray(translation)
    if post:
        post_(text, en_title)
    for ch, chapter in enumerate(translation):
        for m, mishnah in enumerate(chapter):
            translation[ch][m] = " ".join(mishnah)
    if post:
        post_(translation, index.title)


def convert_spellings(sefer):
    replace_with = {"Chullin": "Hullin", "Challah": "Hallah", "Yevamot": "Yevamoth", "Ketubot": "Ketuboth",
                    "Makhshirin": "Makshirin", "Tahorot": "Toharot", "Oholot": "Ohalot", "Oktzin": "Oktzim",
                    "Zevachim": "Zevahim", "Menachot": "Menahot", "Kinnim": "Kinim", "Chagigah": "Hagigah",
                    "Beitzah": "Betzah", "Pesachim": "Pesahim", "Avot": "Avoth",
                    "Horayot": "Horayoth", "Eduyot": "Eduyoth", "Shevuot": "Shevuoth", "Makkot": "Makkoth",
                    "Bava Metzia": "Bava Metziah"}
    for k, v in replace_with.items():
        if v in sefer:
            sefer = sefer.replace(v, k)
            break
    return sefer

def parse_intro(lines):
    new_lines = []
    temp = ""
    for line_n, line in enumerate(lines):
        line = line.replace("\r\n", "")
        if line == "":
            new_lines.append(temp)
            temp = ""
        elif temp:
            temp += " " + line
        else:
            temp = line
    return [el for el in new_lines if el]


def move_files_to_one_dir():
    walk = os.walk("./orig_contents")
    for each_walk in walk:
        dir = each_walk[0]
        if len(dir.split("/")) == 4: #this indicates we're at the directories we care about
            dir, other, files = each_walk
            for file in files:
                shutil.copy(dir+"/"+file, "./orig_contents/"+file)




if __name__ == "__main__":
    move_files_to_one_dir()
    HOW_MANY_REFER_TO_SECTIONS = 0
    parsed_text = {}
    download_mode = True
    dir = "txt files"
    files = os.listdir("./{}".format(dir))
    for file_n, file in enumerate(files):
        orig_file = file
        if len(file) < 4:
            continue
        sefer = " ".join(file.split()[0:-1])
        if sefer not in parsed_text.keys():
            parsed_text[sefer] = {}
        file = file.title().replace(".Txt", ".txt")
        if "Copy" in file or "part" in file or "Part" in file \
                or len(file.split("-")) > 2 or not ".txt" in file \
                or "Rescued Document" in file or not " " in file: #Ignore copies, and files with multiple parts or mishnayot
            continue
        with open("./{}/{}".format(dir, file)) as f:
            lines = list(f)
        if file.startswith("Introduction"):
            sefer = orig_file.replace("Introduction to ", "").replace("Intro to ", "").replace("Tractate ", "")[0:-4]
            if sefer not in parsed_text.keys():
                parsed_text[sefer] = {}
            parsed_text[sefer]["Introduction"] = parse_intro(lines)
        elif file.startswith(sefer):
            #get_mishnah_on_multiple_lines(category, sefer, file)
            file = file.replace("-", ":").replace(".txt", "") #Berakhot 3-13.doc --> Mishnah Berakhot 3:13
            file = convert_spellings(file)
            ref_form = Ref("Mishnah " + file)
            chapter, mishnah = ref_form.sections[0], ref_form.sections[1]
            if chapter not in parsed_text[sefer].keys():
                parsed_text[sefer][chapter] = {}
            #lines = get_lines_from_web(file.rsplit("/")[-1], download_mode=download_mode)
            lines = [line.replace("\xa0", "").replace("\r\n", "") for line in lines if line.replace("\r\n", "").replace(" ", "").replace("\xa0", "")]
            parsed_text[sefer][chapter][mishnah] = parse(lines, sefer, chapter, mishnah, HOW_MANY_REFER_TO_SECTIONS)


    # most_common_value = found_ref.most_common(1)[0]
    # assert most_common_value[1] == 1, "{} has {}".format(most_common_value[0], most_common_value[1])
    post = True
    dont_start = True
    didnt_post = [u'Mishnah Yomit on Pirkei Avot',
 u'Mishnah Yomit on Mishnah Makhshirin',
 u'Mishnah Yomit on Mishnah Demai',
 u'Mishnah Yomit on Mishnah Berakhot',
 u'Mishnah Yomit on Mishnah Rosh Hashanah',
 u'Mishnah Yomit on Mishnah Shekalim',
 u'Mishnah Yomit on Mishnah Parah',
 u'Mishnah Yomit on Mishnah Megillah',
 u'Mishnah Yomit on Mishnah Shevuot',
 u'Mishnah Yomit on Mishnah Bava Batra',
 u'Mishnah Yomit on Mishnah Bekhorot',
 u'Mishnah Yomit on Mishnah Negaim',
 u'Mishnah Yomit on Mishnah Beitzah',
 u'Mishnah Yomit on Mishnah Yevamot',
 u'Mishnah Yomit on Mishnah Nazir',
 u'Mishnah Yomit on Mishnah Kilayim',
 u'Mishnah Yomit on Mishnah Sotah',
 u'Mishnah Yomit on Mishnah Zevachim',
 u'Mishnah Yomit on Mishnah Yoma',
 u'Mishnah Yomit on Mishnah Meilah',
 u'Mishnah Yomit on Mishnah Bava Kamma',
 u'Mishnah Yomit on Mishnah Keritot',
 u'Mishnah Yomit on Mishnah Terumot',
 u'Mishnah Yomit on Mishnah Bava Metzia',
 u'Mishnah Yomit on Mishnah Sanhedrin',
 u'Mishnah Yomit on Mishnah Kelim',
 u'Mishnah Yomit on Mishnah Tamid',
 u'Mishnah Yomit on Mishnah Arakhin',
 u'Mishnah Yomit on Mishnah Niddah',
 u'Mishnah Yomit on Mishnah Gittin',
 u'Mishnah Yomit on Mishnah Middot',
 u'Mishnah Yomit on Mishnah Pesachim']
    start_at = ""
    for sefer in parsed_text.keys():
        if start_at in sefer:
            dont_start = False
        if dont_start:
            continue
        if parsed_text[sefer]:
            try:
                create_index(parsed_text[sefer], sefer, post=post)
                check_all_mishnayot_present_and_post(parsed_text[sefer], sefer, file, post=post)
            except BookNameError as e:
                print e

    print "Section referenced not in mishnah: {} {}".format(len(section_referenced_not_in_mishnah), section_referenced_not_in_mishnah)
    print "Mishnah without numbers when explanation does have numbers: {} {}".format(len(mishnah_wout_numbers_explanation_has), mishnah_wout_numbers_explanation_has)
    print "Mishnah without numbers when explanation does NOT have numbers: {} {}".format(len(mishnah_wout_numbers_explanation_wout), mishnah_wout_numbers_explanation_wout)
    print "Found more mishnah sections than explanation sections: {} {}".format(len(mishnah_sections_more_than_explanation_sections), mishnah_sections_more_than_explanation_sections)

