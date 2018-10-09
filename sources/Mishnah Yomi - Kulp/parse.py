#encoding=utf-8
import requests
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from num2words import num2words
from word2number import w2n
import os
import re
from collections import Counter
from sources.functions import post_index, post_text, convertDictToArray, add_category
from bs4 import BeautifulSoup
import textract
import traceback
import sys

SERVER = "http://ste.sefaria.org"

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
    print new_name
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





def parse(lines, sefer, chapter, mishnah, HOW_MANY_REFER_TO_SECTIONS):
    def get_first_sentence(line):
        line = line.strip()
        end = line.find(". ")
        if end != -1:
            return line[0:end]+". "
        return line+" "


    def deal_with_sections(line, text, len_mishnah):
        line = line.replace(" -", ":", 1).replace("—", ": ", 1).replace("â", ": ", 1)
        section = re.search("^Section (\d+|[a-zA-Z]+) ", line)
        if not section:
            if len(text) > 0:
                text[-1] += "<br/>"+line
            else:
                text.append(line)
            return 0

        section_num_as_word = section.group(1).strip()

        if section_num_as_word.endswith(":"): # if there is a colon at the end, we want to replace the words "Section one: ", but if it's part of the sentence like "Section one is ...", then we want to keep it
            line = line.replace(section.group(0), "")
            section_num_as_word = section_num_as_word[0:-1]

        if section_num_as_word.find("-") in [1, 2]: #either 10-14 or 2-7 will be matched, this is a range
            section_num_as_word = section_num_as_word.split("-")[0]


        try:
            if type(section_num_as_word) is unicode:
                section_num_as_word = section_num_as_word.encode('utf-8')
            if len(section_num_as_word) > 1:
                section_num = w2n.word_to_num(section_num_as_word)
            elif section_num_as_word.isdigit():
                section_num = int(section_num_as_word)
            elif len(section_num_as_word) == 1: #just a letter
                section_num = ord(section_num_as_word) - 64
        except ValueError:
            assert type(section_num_as_word) is int, "Problem with {}".format(section_num_as_word)
            section_num = section_num_as_word
        if section_num - 1 < len_mishnah:
            first_sentence = get_first_sentence(mishnah_text[section_num - 1])
            line = "<b>{}</b>{}".format(first_sentence, line)
            text.append(line)
        else:
            text.append(line)
            return -1

    currently_parsing = ""
    mishnah_text = []
    commentary_text = []
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
        #line = line.strip().replace(unichr(151), u"").replace(unichr(146), u"")
        if "Part" in line and len(line.split()) < 10:
            print "{}\n{}\n\n".format(file, line)
            return (commentary_text + questions_text, mishnah_text)
        if "Questions for Further Thought" in line:
            currently_parsing = "QUESTIONS"
            questions_text.append("<b>"+line+"</b>")
        elif len(line.split()) < 7 and ("Mishna" in line or sefer == line):
            if "Mishnah {}".format(mishnah_as_word) != line and "Mishna" in line:
                word = line.split()[-1] #Mishnah Five -> Five
                try:
                    mishnah_inside_file = w2n.word_to_num(word)
                    complaint = "Mishnah word different than number: {} {}:{}".format(sefer, chapter, mishnah)
                    #print complaint
                except ValueError:
                    pass
            currently_parsing = "MISHNAH"
        elif "Introduction" == line:
            commentary_text.append("<b>"+line+"</b>")
            currently_parsing = line.upper()
        elif "Explanation" == line:
            currently_parsing = line.upper()
        else:
            if currently_parsing == "INTRODUCTION":
                commentary_text[-1] += "\n" + line
            elif currently_parsing == "EXPLANATION":
                result = deal_with_sections(line, explanation_sections_text, len(mishnah_text))
                if result == -1:  # there was just an error
                    print "{} - Problem with explanation sections corresponding to mishnayot\n".format(file)
                    result = deal_with_sections(line, explanation_sections_text, len(mishnah_text))
                    return (commentary_text + questions_text, mishnah_text)
            elif currently_parsing == "QUESTIONS":
                questions_sections_text.append(line)
            elif currently_parsing == "MISHNAH":
                mishnah_text.append(line)


    assert commentary_text != mishnah_text != []
    mishnah_text = restructure_mishnah_text(mishnah_text)
    if len(explanation_sections_text) > len(mishnah_text):
         print "Length of mishnah less than length of explanations {}".format(file)
    commentary_text += explanation_sections_text
    questions_text += questions_sections_text
    commentary_text = [el for el in commentary_text if el]
    questions_text = [el for el in questions_text if el]
    return (commentary_text+questions_text, mishnah_text)


def restructure_mishnah_text(old_mishnah_text):
    mishnah_text = []
    found_digit_or_char = False
    for line in old_mishnah_text:
        digit = re.search("^\d+\)", line)
        char = re.search("^[a-zA-Z]+\)", line)
        if digit or char:
            found_digit_or_char = True

    if not found_digit_or_char:
        return old_mishnah_text

    for line in old_mishnah_text:
        digit = re.search("^\d+\)", line)
        char = re.search("^[a-zA-Z]+\)", line)
        if digit:
            mishnah_text.append(line.replace(digit.group(0), "").strip())
        elif char:
            mishnah_text.append(line.replace(char.group(0), "").strip())
        elif len(mishnah_text) > 0:
            mishnah_text[-1] += " " + line.strip()
        else:
            mishnah_text.append(line.strip())
    return mishnah_text

def create_index(text, sefer):
    #add_category("Mishnah Yomit", ["Mishnah", "Commentary", "Mishnah Yomit"], server=SERVER)
    index = library.get_index("Mishnah " + sefer)
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
    default.add_structure(["Perek", "Mishnah", "Comment"])
    root.append(default)
    root.validate()
    index = {
        "title": en_title,
        "schema": root.serialize(),
        "categories": ["Mishnah", "Commentary", "Mishnah Yomit"],
        "dependence": "Commentary",
        "base_text_titles": [index.title],
        "collective_title": "Joshua Kulp",
    }
    #post_index(index, server=SERVER)


def check_all_mishnayot_present_and_post(text, sefer, file_path):
    def post_(text, path):
        send_text = {
            "language": "en",
            "text": text,
            "versionTitle": "Mishnah Yomit",
            "versionSource": "http://learn.conservativeyeshiva.org/mishnah/"
        }
        #post_text(path, send_text, server=SERVER)
    #first check that all chapters present
    sefer = convert_spellings(sefer)
    index = library.get_index("Mishnah " + sefer)
    en_title = "Mishnah Yomit on {}".format(index.title)
    translation = dict(text)
    for ch in text.keys():
        if ch == "Introduction":
            post_(text[ch], "{}, Introduction".format(en_title))
            text.pop(ch)
            translation.pop(ch)
            continue
        actual_mishnayot = [el.sections[1] for el in Ref("Mishnah {} {}".format(sefer, ch)).all_segment_refs()]
        our_mishnayot = text[ch].keys()
        if our_mishnayot != actual_mishnayot:
            actual_mishnayot = set(actual_mishnayot)
            our_mishnayot = set(our_mishnayot)
            missing = actual_mishnayot - our_mishnayot
            wrong = our_mishnayot - actual_mishnayot
            print file_path
            print "Sefer: {}, Chapter: {}".format(sefer, ch)
            print "Mishnayot to check: {}".format(list(missing.union(wrong)))
            print
        text[ch] = zip(*convertDictToArray(text[ch], empty=("", "")))
        translation[ch] = list(text[ch][1])
        text[ch] = list(text[ch][0])
        while "" in text[ch]:
            i = text[ch].index("")
            text[ch][i] = []
    text = convertDictToArray(text)
    translation = convertDictToArray(translation)
    post_(text, en_title)
    for ch, chapter in enumerate(translation):
        for m, mishnah in enumerate(chapter):
            translation[ch][m] = " ".join(mishnah)
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

if __name__ == "__main__":

    HOW_MANY_REFER_TO_SECTIONS = 0
    parsed_text = {}
    download_mode = True
    dont_start = True
    categories = [category for category in os.listdir("./orig_contents") if os.path.isdir(category)]
    for category in categories:
        print "CATEGORY:"
        print category
        sefarim = os.listdir("./orig_contents/{}".format(category))
        for sefer in sefarim:
            current_path = "./orig_contents/{}/{}".format(category, sefer)
            if not os.path.isdir(current_path):
                continue
            if sefer not in parsed_text.keys():
                parsed_text[sefer] = {}
            files = os.listdir(current_path)
            found_ref = Counter()
            for file_n, file in enumerate(files):
                file_path = current_path + "/" + file
                print file_path
                if "Copy" in file or "part" in file or "Part" in file \
                        or len(file.split("-")) > 2 or not ".doc" in file or not " " in file: #Ignore copies, and files with multiple parts or mishnayot
                    continue
                if file.startswith("Introduction"):
                    lines = textract.process(file_path).splitlines()
                    parsed_text[sefer]["Introduction"] = [line.replace("\n", "") for line in lines if line != "\n"]
                elif file.startswith(sefer):
                    #get_mishnah_on_multiple_lines(category, sefer, file)
                    file = file.replace("-", ":").replace(".docx", "").replace(".doc", "") #Berakhot 3-13.doc --> Mishnah Berakhot 3:13
                    file = convert_spellings(file)
                    ref_form = Ref("Mishnah " + file)
                    found_ref[ref_form.normal()] += 1
                    chapter, mishnah = ref_form.sections[0], ref_form.sections[1]
                    if chapter not in parsed_text[sefer].keys():
                        parsed_text[sefer][chapter] = {}
                    #lines = get_lines_from_web(file.rsplit("/")[-1], download_mode=download_mode)
                    lines = textract.process(file_path).splitlines()
                    lines = [line.replace("\xa0", "") for line in lines if line.replace(" ", "").replace("\xa0", "")]
                    parsed_text[sefer][chapter][mishnah] = parse(lines, sefer, chapter, mishnah, HOW_MANY_REFER_TO_SECTIONS)


            # most_common_value = found_ref.most_common(1)[0]
            # assert most_common_value[1] == 1, "{} has {}".format(most_common_value[0], most_common_value[1])
            # create_index(parsed_text[sefer], sefer)
            check_all_mishnayot_present_and_post(parsed_text[sefer], sefer, current_path)