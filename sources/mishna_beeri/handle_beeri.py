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
def create_text_object(lines):
    text_dict ={}

    def ref_generator(masechet_index, perek, mishna, segment):
        return "Lechem Shamayim on Mishnah " + masechtot[masechet_index] + " " + str(perek) + " " + str(mishna) + ":" + str(segment)
    masechet_index = -1
    perek_index = 0
    mishna_index = 0
    segment_index = 0


    for line in lines:
        # print(line)
        if  "סליקא מסכת" in line:
            continue
        if ('@00' in line or '@88' in line) and "מסכת" in line:
            masechet_index+=1
            perek_index = 0
            mishna_index = 0
            segment_index = 0
            continue
        elif '@00' in line and "פרק" in line:
            # perek_index += 1
            perek_index = compute_gematria(extract_last_word(line))
            mishna_index = 0
            segment_index = 0
        elif '@22' in line:
            # mishna_index += 1
            mishna_index = compute_gematria(extract_last_word(line))
            segment_index = 0
        else:
            if line in {"", " ", "  "}:
                continue
            segment_index +=1
            ref_string = ref_generator(masechet_index, perek_index, mishna_index, segment_index)
            text_dict[ref_string] = line
    return text_dict


def parse_text(text):
    lines = text.split('\n')
    return lines


def print_dict_list_lengths(list_of_dicts):
    for dictionary in list_of_dicts:
        for key, value in dictionary.items():
            if isinstance(value, list):
                key = key.replace("@11", '')
                # print(f"Masechet and Chapter: {key}, Number of Mishnayot: {len(value)}")
                # print(f"{key}, Number of Mishnayot: {len(value)}")
                print(f"{len(value)}")
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




if __name__ == '__main__':
    print("hello world")
    a = read_docx("beeri.docx")
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
    print_dict_list_lengths(shas)
    num_of_mish_every_chap = {}
    for masechet in all_masechtot:
        r = Ref("Mishna " + masechet)
        ranged = r.as_ranged_segment_ref()
        num_of_chapters  = ranged.toSections[0]
        segments = r.all_segment_refs()


        for perek in range (1, num_of_chapters + 1):
            tref = "Mishna " + masechet +  ' ' + str(perek)
            num_of_mish = len(Ref("Mishna " + masechet +  ' ' + str(perek)).all_segment_refs())
            num_of_mish_every_chap[tref] = num_of_mish

    # Specify the CSV file path
    csv_file = "output.csv"

    # Open the CSV file for writing
    with open(csv_file, 'w', newline='') as file:
        # Create a CSV writer object
        writer = csv.writer(file)

        # Write the key-value pairs as rows with two columns each
        for key, value in num_of_mish_every_chap.items():
            writer.writerow([key, value])

    print(f"CSV file '{csv_file}' has been created.")





    print('hi')








