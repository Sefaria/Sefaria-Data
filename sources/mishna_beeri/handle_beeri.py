import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
# import time
import docx
from docx import Document
import itertools
import re


from collections import defaultdict



seder = "Moed"
masechtot = [
"Berakhot",
             "Peah",
             "Demai",
             "Kilayim",
             "Sheviit",
             "Terumot",
             "Maasrot",
             "Maaser Sheni",
             "Challah",
             "Orlah",
             "Bikkurim"]
masechtot = ["Shabbat",
 "Eruvin",
 "Pesachim",
 "Shekalim",
 "Yoma",
 "Sukkah",
 "Beitzah",
 "Rosh Hashanah",
 "Ta'anit",
 "Megillah",
 "Moed Katan",
 "Chagigah"
]
masechtot = ["Yevamot",
 "Ketubot",
 "Nedarim",
"Nazir",
 "Sotah",
 "Gittin",
"Kiddushin",
]
masechtot = [
"Bava Kamma",
 "Bava Metzia",
 "Bava Batra",
 "Sanhedrin",
 "Makkot",
 "Shevuot",
 "Eduyot",
 "Avodah Zarah",
# "Pirkei Avot",
"Horayot"
]
# masechtot = [
# "Zevachim",
#  "Menachot",
#  "Chullin",
#  "Bekhorot",
#  "Arakhin",
#  "Temurah",
#  "Keritot",
#  "Meilah",
#  "Tamid",
#  "Middot",
#  "Kinnim"
# ]
# masechtot = [
#  "Kelim",
#  "Oholot",
#  "Negaim",
#  "Parah",
#  "Tahorot",
#  "Mikvaot",
#  "Niddah",
#  "Makhshirin",
#  "Zavim",
#  "Tevul Yom",
#  "Yadayim",
#  "Oktzin"
# ]
all_masechtot = [
"Berakhot",
             "Peah",
             "Demai",
             "Kilayim",
             "Sheviit",
             "Terumot",
             "Maasrot",
             "Maaser Sheni",
             "Challah",
             "Orlah",
             "Bikkurim",
    "Shabbat",
    "Eruvin",
    "Pesachim",
    "Shekalim",
    "Yoma",
    "Sukkah",
    "Beitzah",
    "Rosh Hashanah",
    "Taanit",
    "Megillah",
    "Moed Katan",
    "Chagigah",
"Yevamot",
 "Ketubot",
 "Nedarim",
"Nazir",
 "Sotah",
 "Gittin",
"Kiddushin",
"Bava Kamma",
 "Bava Metzia",
 "Bava Batra",
 "Sanhedrin",
 "Makkot",
 "Shevuot",
 "Eduyot",
 "Avodah Zarah",
 "Avot",
"Horayot",
"Zevachim",
 "Menachot",
 "Chullin",
 "Bekhorot",
 "Arakhin",
 "Temurah",
 "Keritot",
 "Meilah",
 "Tamid",
 "Middot",
 "Kinnim",
 "Kelim",
 "Oholot",
 "Negaim",
 "Parah",
 "Tahorot",
 "Mikvaot",
 "Niddah",
 "Makhshirin",
 "Zavim",
 "Tevul Yom",
 "Yadayim",
 "Oktzin"
]
masechtot_he = [
    "ברכות",
             "פאה",
             "פאה",
             "דמאי",
             "כלאים",
             "שביעית",
             "תרומות",
             "מעשרות",
             "מעשר שני",
             "חלה",
             "ערלה",
             "ביכורים"]
# masechtot_he = ["שבת",
#              "עירובין",
#              "פסחים",
#              "שקלים",
#              "יומא",
#              "סוכה",
#              "ביצה",
#              "ראש השנה",
#              "תענית",
#              "מגילה",
#              "מועד קטן",
#                 "חגיגה"]
# masechtot_he = ["יבמות",
#              "כתובות",
#              "נדרים",
#              "נזיר",
#              "סוטה",
#              "גיטין",
#              "קידושין"]
# masechtot_he = [
# "בבא קמא",
#  "בבא מציעא",
#  "בבא בתרא",
#  "סנהדרין",
#  "מכות",
#  "שבועות",
#  "עדיות",
#  "עבודה זרה",
# # "אבות",
# "הוריות"
# ]
# masechtot_he = [
# "זבחים",
#  "מנחות",
#  "חולין",
#  "בכורות",
#  "ערכין",
#  "תמורה",
#  "כריתות",
#  "מעילה",
#  "תמיד",
#  "מידות",
#  "קינים"
# ]
# masechtot_he = [
#  "כלים",
#  "אהלות",
#  "נגעים",
#  "פרה",
#  "טהרות",
#  "מקואת",
#  "נדה",
#  "מכשירין",
#  "זבים",
#  "טבול יום",
#  "ידים",
#  "עוקצים"
# ]
gimatria_numerals = ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י", "יא", "יב", "יג", "יד", "טו", "טז","יו", "יה", "יז", "יח", "יט", "כ", "כא", "כב", "כג", "כד", "כה"]

def compute_gematria(word):
    # Define the numerical values of each letter
    gematria = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

    # Compute the Gematria of the word
    total = 0
    for letter in word:
        if letter in gematria:
            total += gematria[letter]

    return total

def read_docx(file_path):
    doc = docx.Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)


def parse_text(text):
    lines = text.split('\n')
    return lines


def print_dict_list_lengths(list_of_dicts):
    for dictionary in list_of_dicts:
        for key, value in dictionary.items():
            if isinstance(value, list):
                key = key.replace("@11", '')
                # print(f"Masechet and Chapter: {key}, Number of Mishnayot: {len(value)}")
                print(f"{key}, Number of Mishnayot: {len(value)}")
                # print(f"{len(value)}")
def extract_substring_until_after_perek(input_string):
    # Find the position of "פרק"
    index = input_string.find("פרק") + 4

    # If "פרק" is found, find the position of the next space after it
    if index != -1:
        space_index = input_string.find(" ", index)

        # Extract the substring from the beginning of the string until the space after "פרק"
        if space_index != -1:
            extracted_substring = input_string[:space_index + 1].strip()
        else:
            # Handle the case where no space is found after "פרק"
            extracted_substring = input_string
    else:
        # Handle the case where "פרק" is not found
        extracted_substring = input_string
    return(extracted_substring)


def contains_just_one_word(input_string):
    # Check if the string contains only whitespace characters
    if input_string.isspace():
        return False

    # Split the string into words using whitespace as the delimiter
    words = input_string.split()

    # Check if there is only one word in the list
    return len(words) == 1


def extract_first_hebrew_word(input_string):
    # Remove all non-Hebrew letters and spaces
    clean_string = re.sub(r'[^א-ת\s]', '', input_string)

    # Split the cleaned string into words
    words = clean_string.split()

    # Get the first Hebrew word (if any)
    if words:
        return words[0]
    else:
        return None


def beeri_to_structured():
    a = read_docx("beeri_corrected.docx")
    a = a.split('@00')[1:]
    shas = []
    for mas in a:
        # mas = mas.split("@11מסכת")
        mas = ['@11מסכת' + e for e in mas.split('@11מסכת') if e]
        # Create a defaultdict with a default factory of list
        mas_chapters = defaultdict(list)
        for mishna in mas:
            # input_string = mishna
            extracted_substring = extract_substring_until_after_perek(mishna)
            # Print the extracted substring
            if '@11מסכת ' in extracted_substring and ' פרק ' in extracted_substring:
                mas_chapters[extracted_substring].append(mishna)
            # print(extracted_substring)

        shas.append(mas_chapters)
    return shas

def format_mishna(mishna_string):
    if "רַשַּׁי" in mishna_string:
        a = 8
    # Split the string into lines, filter, and join back
    lines = mishna_string.splitlines()
    filtered_lines = [line for line in lines if not (line.startswith('@') or
                                                     line.startswith(' @') or line.startswith('(@') or  line.startswith(' (@') or
                                                     line.startswith('חסלת'))]
    for line in filtered_lines:
        if contains_just_one_word((line)):
            # Define the regular expression pattern
            # pattern = r'([\u0590-\u05fe])\n'
            if extract_first_hebrew_word(line) in gimatria_numerals:
                pattern = r'([\u0590-\u05FF]{1,2})'
                # Replace '\n' with '<br>' after a space and a letter
                filtered_lines[filtered_lines.index(line)] = re.sub(pattern, r'<small>\1</small>', line).replace('\n', ' ')

    mishna_string = '\n'.join(filtered_lines)
    if mishna_string.endswith("("):
        # Remove the ( and preceding white spaces
        mishna_string = mishna_string.rstrip(" (")

    # # Define the regular expression pattern
    # # pattern = r'([\u0590-\u05fe])\n'
    # pattern = r'([\u0590-\u05FF]+\s*\n)'
    # # Replace '\n' with '<br>' after a space and a letter
    # output_string = re.sub(pattern, r'<small>\1</small>', mishna_string).replace('\n', ' ')
    if mishna_string.startswith("<br>"):
        mishna_string = output_string[4:]
    return(mishna_string)

def ingest_masechet_version(masechet_name ,map_text):
    # vs = VersionState(index=library.get_index("Introductions to the Babylonian Talmud"))
    # vs.delete()
    # print("deleted version state")
    print("ingesting Masechet " + masechet_name)
    index = library.get_index("Mishnah " + masechet_name)
    cur_version = VersionSet({'title': "Mishnah " + masechet_name,
                              "versionTitle" : "Mishnah based on the Kaufmann manuscript, edited by Dan Be'eri"})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Mishnah based on the Kaufmann manuscript, edited by Dan Be'eri",
                       "versionSource": "https://archive.org/details/MishnaCorrectedKaufman00WHOLE",
                       "title": "Mishnah " + masechet_name,
                       "language": "he",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })
    modify_bulk_text(superuser_id, version, map_text)

def post_version(masechet_name ,map_text):
    from sources.functions import create_payload_and_post_text
    create_payload_and_post_text("Mishnah" + masechet_name, map_text, 'he', "Mishnah based on the Kaufmann manuscript, edited by Dan Be'eri",
                                 "https://archive.org/details/MishnaCorrectedKaufman00WHOLE", server="https://beeri.cauldron.sefaria.org")

if __name__ == '__main__':
    print("hello world")
    shas = beeri_to_structured()
    # Convert to list of lists of lists
    beeri_list_of_lists_of_lists = [[[value] if isinstance(value, list) else value for value in d.values()] for d in
                              shas]
    beeri_masechtot_flat = []
    for beeri_masechet in beeri_list_of_lists_of_lists:
        beeri_masechet_flat = []
        for beeri_perek in beeri_masechet:
            for dummy in beeri_perek:
                for beerei_mishna in dummy:
                    beeri_masechet_flat.append(beerei_mishna)
        beeri_masechtot_flat.append(beeri_masechet_flat)
    del(shas)
    del(beeri_list_of_lists_of_lists)




    for masechet in all_masechtot:
        masechet_to_post = {}
        masecet_index = all_masechtot.index(masechet)
        # if masecet_index >= 1:
        #     break
        r = Ref("Mishnah " + masechet)
        ranged = r.as_ranged_segment_ref()
        num_of_chapters  = ranged.toSections[0]
        segments = r.all_segment_refs()
        for segment in segments:
            segment_index = segments.index(segment)
            masechet_to_post[segment.tref] = format_mishna(beeri_masechtot_flat[masecet_index][segment_index])
        ingest_masechet_version(masechet, masechet_to_post)











    # print_dict_list_lengths(shas)
    # num_of_mish_every_chap = {}
    # for masechet in all_masechtot:
    #     r = Ref("Mishna " + masechet)
    #     ranged = r.as_ranged_segment_ref()
    #     num_of_chapters  = ranged.toSections[0]
    #     segments = r.all_segment_refs()
    #
    #
    #     for perek in range (1, num_of_chapters + 1):
    #         tref = "Mishna " + masechet +  ' ' + str(perek)
    #         num_of_mish = len(Ref("Mishna " + masechet +  ' ' + str(perek)).all_segment_refs())
    #         num_of_mish_every_chap[tref] = num_of_mish
    #
    # # Specify the CSV file path
    # csv_file = "output.csv"
    #
    # # Open the CSV file for writing
    # with open(csv_file, 'w', newline='') as file:
    #     # Create a CSV writer object
    #     writer = csv.writer(file)
    #
    #     # Write the key-value pairs as rows with two columns each
    #     for key, value in num_of_mish_every_chap.items():
    #         writer.writerow([key, value])
    #
    # print(f"CSV file '{csv_file}' has been created.")





    print('hi')








