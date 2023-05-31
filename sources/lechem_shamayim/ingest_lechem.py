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
import time
import docx
from docx import Document
import re

# seder = "Tahorot"
masechtot = ["Berakhot",
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
masechtot = [
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
 "Kinnim"
]
masechtot = [
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
masechtot_he = ["ברכות",
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
masechtot_he = ["שבת",
             "עירובין",
             "פסחים",
             "שקלים",
             "יומא",
             "סוכה",
             "ביצה",
             "ראש השנה",
             "תענית",
             "מגילה",
             "מועד קטן",
                "חגיגה"]
masechtot_he = ["יבמות",
             "כתובות",
             "נדרים",
             "נזיר",
             "סוטה",
             "גיטין",
             "קידושין"]
masechtot_he = [
"בבא קמא",
 "בבא מציעא",
 "בבא בתרא",
 "סנהדרין",
 "מכות",
 "שבועות",
 "עדיות",
 "עבודה זרה",
# "אבות",
"הוריות"
]
masechtot_he = [
"זבחים",
 "מנחות",
 "חולין",
 "בכורות",
 "ערכין",
 "תמורה",
 "כריתות",
 "מעילה",
 "תמיד",
 "מידות",
 "קינים"
]
masechtot_he = [
 "כלים",
 "אהלות",
 "נגעים",
 "פרה",
 "טהרות",
 "מקואת",
 "נדה",
 "מכשירין",
 "זבים",
 "טבול יום",
 "ידים",
 "עוקצים"
]

def compute_gematria(word):
    # Define the numerical values of each letter
    gematria = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

    # Compute the Gematria of the word
    total = 0
    for letter in word:
        if letter in gematria:
            total += gematria[letter]

    return total
def extract_last_word(string):
    # Split the string into words using the whitespace as the delimiter
    words = string.split()

    # If there are no words, return an empty string
    if len(words) == 0:
        return ""

    # Otherwise, return the last word
    return words[-1]
def create_fake_schema(en, he):
    root = JaggedArrayNode()
    comm_en = "Chomat Anakh on {}".format(en)
    comm_he = u"חומת אנך על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter", "Paragraph"])
    index = {
        "title": comm_en,
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary"]
    }
    post_index(index, server="http://localhost:8000")

def add_new_categories():
    # create_category(['Jewish Thought', 'Guide for the Perplexed'], 'Guide for the Perplexed', "מורה נבוכים")
    # create_category(['Jewish Thought', 'Guide for the Perplexed', "Commentary"], 'Commentary', "מפרשים")
    # create_category(['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim', 'Seder ' + 'Zeraim'], 'Seder ' + 'Zeraim')
    create_category(['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim', 'Seder ' + 'Moed'], 'Seder ' + 'Moed')
    create_category(['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim', 'Seder ' + 'Nashim'], 'Seder ' + 'Nashim')
    create_category(['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim', 'Seder ' + 'Kodashim'], 'Seder ' + 'Kodashim')
    create_category(['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim', 'Seder ' + 'Tahorot'], 'Seder ' + 'Tahorot')

def create_text_object(lines):
    text_dict ={}

    def ref_generator(masechet_index, perek, mishna, segment):
        return "Lechem Shamayim on Mishnah " + masechtot[masechet_index] + " " + str(perek) + " " + str(mishna) + ":" + str(segment)
    masechet_index = -1
    perek_index = 0
    mishna_index = 0
    segment_index = 0


    for line in lines:
        print(line)
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
    data = {}
    # for line in lines:
    #     if line.startswith('@'):
    #         try:
    #             key, value = re.split("@\d+", line)[1:]
    #             data[key] = value
    #         except ValueError:
    #             print(f"Unable to split line: {line}")
    return lines
def filter_dictionary_by_string(dictionary, string):
    filtered_dict = {}

    for key, value in dictionary.items():
        if string in key:
            filtered_dict[key] = value

    return filtered_dict
def ingest_version(map_text):
    # vs = VersionState(index=library.get_index("Introductions to the Babylonian Talmud"))
    # vs.delete()
    # print("deleted version state")
    # def filter_dictionary_by_string(dictionary, string):
    #     filtered_dict = {}
    #
    #     for key, value in dictionary.items():
    #         if string in key:
    #             filtered_dict[key] = value
    #
    #     return filtered_dict

    for masechet in masechtot:
        masechet_map = filter_dictionary_by_string(map_text, masechet)
        print("ingesting masechet "+ masechet)


        index = library.get_index('Lechem Shamayim on Mishnah '+ masechet)
        cur_version = VersionSet({'title': 'Lechem Shamayim on Mishnah '+ masechet})
        if cur_version.count() > 0:
            cur_version.delete()
            print("deleting existing version")
        chapter = index.nodes.create_skeleton()
        version = Version({"versionTitle": "Jerusalem, 1978",
                           "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH990012730190205171/NLI",
                           "title": 'Lechem Shamayim on Mishnah '+ masechet,
                           "language": "he",
                           "chapter": chapter,
                           "digitizedBySefaria": True,
                           "license": "PD",
                           "status": "locked"
                           })
        modify_bulk_text(superuser_id, version, masechet_map)

def read_docx(file_path):
    doc = docx.Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def create_index_dict(masechet_name_en, masechet_name_he):
    node = JaggedArrayNode()
    # addressTypes': ['Perek', 'Mishnah', 'Integer'], 'sectionNames': ['Chapter', 'Mishnah', 'Comment'],
    node.sectionNames = ['Chapter', 'Mishnah', 'Comment']
    node.add_structure(['Chapter', 'Mishnah', 'Comment'])
    node.addressTypes = ['Perek', 'Mishnah', 'Integer']
    # node.key = 'Lechem Shamayim on Mishna' + masechet_name_en
    node.add_primary_titles('Lechem Shamayim on Mishnah ' + masechet_name_en, 'לחם שמים על משנה '+ masechet_name_he)
    node.validate()

    index_dict = {'title': 'Lechem Shamayim on Mishnah '+ masechet_name_en,
                      'categories': ['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim', 'Seder ' + seder],
                    "schema": node.serialize(),
                      # 'schema': {'nodeType': 'JaggedArrayNode', 'depth': 3, 'addressTypes': ['Perek', 'Mishnah', 'Integer'], 'sectionNames': ['Chapter', 'Mishnah', 'Comment'],
                      #            'titles': [{'lang': 'he', 'text': 'לחם שמים על '+ masechet_name_he, 'primary': True},
                      #                       {'text': 'Lechem Shamayim on ' + masechet_name_en, 'lang': 'en', 'primary': True}],
                      #            'key': 'Lechem Shamayim on '+ masechet_name_en},
                      'authors': ['yaakov-emden'],
                      'enDesc': "Commentary of R' Yaakov Emden on Mishnah.", 'heDesc': "ביאור לר' יעקב עמדין על המשנה.",
                      'pubDate': '1728', 'compDate': '1725', 'pubPlace': 'Altona', 'errorMargin': '3', 'era': 'AH',
                      'dependence': 'Commentary',
                        'base_text_titles': ['Mishnah ' + masechet_name_en],
                      'base_text_mapping': None,
                      'collective_title': 'Lechem Shamayim'}
    return index_dict
def post_indices():
    from sources.functions import post_index, post_text
    for masechet_en, masechet_he in zip(masechtot, masechtot_he):
       index = create_index_dict(masechet_en, masechet_he)
       # post_index(index)
       post_index(index, server="https://lechemshamayim.cauldron.sefaria.org")         #, server = "https://piaseczno.cauldron.sefaria.org"

def prettify_version(text_object):
    def add_bold_tags(text):
        # Add <b> tags before @11
        text = re.sub(r'(@11)', r'<b>\1', text)

        # Add </b> tags before @33
        text = re.sub(r'(@33)', r'</b>\1', text)

        # Add <b> tags before @44
        text = re.sub(r'(@44)', r'<b>\1', text)

        # Add </b> tags before @55
        text = re.sub(r'(@55)', r'</b>\1', text)



        return text

    def remove_at_and_digits(text):
        cleaned_text = re.sub(r'[@\d]', '', text)
        return cleaned_text

    for ref, line in text_object.items():
        line = add_bold_tags(line)
        line = remove_at_and_digits(line)
        text_object[ref] = line

def validate_document(file_path):
    def find_misplaced_endings(strings):
        def extract_integers(string):
            pattern = r'\d+'
            matches = re.findall(pattern, string)
            integers = [int(match) for match in matches]
            return integers



        misplaced_indexes = []
        last_ending = None
        last_cardinal_tuple = (0,0,0)
        for i, string in enumerate(strings):
            ending = extract_integers(string)
            cardinal_tuple = (ending[0], ending[1], ending[2])


            if last_cardinal_tuple and cardinal_tuple < last_cardinal_tuple:
                misplaced_indexes.append(i)
            last_cardinal_tuple = cardinal_tuple

        return misplaced_indexes

    def get_key_value_by_index(dictionary, index):
        items = list(dictionary.items())
        if 0 <= index < len(items):
            return items[index]
        else:
            raise IndexError("Index out of range")

    docx_text = read_docx(file_path)
    parsed_version = parse_text(docx_text)
    text_obj = create_text_object(parsed_version)
    # prettify_version(text_obj)

    for masechet in masechtot:
        masechet_map = filter_dictionary_by_string(text_obj, masechet)
        refs_in_order = list(masechet_map.keys())
        misplaced = find_misplaced_endings(refs_in_order)
        for index in misplaced:
            print("mismatches masechet " + masechet)
            ref, text = get_key_value_by_index(masechet_map, index)
            print(ref + " :")
            print(text)


if __name__ == '__main__':
    print("hello world")
    # add_new_categories()
    file_path = "lechem_tahorot.docx"
    # post_indices()
    #
    docx_text = read_docx(file_path)
    parsed_version = parse_text(docx_text)
    text_obj = create_text_object(parsed_version)
    prettify_version(text_obj)
    ingest_version(text_obj)



    # "Guide for the Perplexed, Part 1 2:7"
    # ingest_nodes()

    # obj = create_text_object()
    # print(obj)
    # ingest_version(obj)
    # add_new_categories()
    # validate_document(file_path)






