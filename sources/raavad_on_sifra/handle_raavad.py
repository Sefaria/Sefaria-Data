import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import remove_branch
# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
from sefaria.utils.talmud import daf_to_section, section_to_daf
from bs4 import BeautifulSoup
import re
import copy
import string



def ingest_raavad(book_map):
    index = library.get_index("Ra'avad on Sifra")
    cur_version = VersionSet({'title': "Ra'avad on Sifra",
                              "versionTitle" : "Wien, 1862"})

    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Wien, 1862",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH990020310840205171/NLI",
                       "title": "Ra'avad on Sifra",
                       "language": "he",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })
    modify_bulk_text(superuser_id, version, book_map)
def compute_gematria(word):
    # Define the numerical values of each letter
    gematria = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

    # Compute the Gematria of the word
    total = 0
    for letter in word:
        if letter in gematria:
            total += gematria[letter]
    return total

def number_to_hebrew(number):
    hebrew_units = {
        0: '',
        1: 'א',
        2: 'ב',
        3: 'ג',
        4: 'ד',
        5: 'ה',
        6: 'ו',
        7: 'ז',
        8: 'ח',
        9: 'ט',
        10: 'י'
    }

    hebrew_tens = {
        0: '',
        1: 'י',
        2: 'כ',
        3: 'ל',
        4: 'מ',
        5: 'נ',
        6: 'ס',
        7: 'ע',
        8: 'פ',
        9: 'צ'
    }

    if number <= 10:
        return hebrew_units[number]
    elif number == 15:
        return 'טו'
    elif number == 16:
        return 'טז'
    elif number < 20:
        return 'י' + hebrew_units[number % 10]
    else:
        tens = hebrew_tens[number // 10]
        units = hebrew_units[number % 10]
        if units == '':
            return tens
        elif tens == '':
            return units
        else:
            return tens + units

def csv_to_list_of_dicts(csv_file):
    result = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        # headers = next(reader)  # Extract headers
        headers = ["parasha", "section_or_chapter", "paragraph", "text"]
        for row in reader:
            row_dict = {}
            for i, value in enumerate(row[:4]):
                row_dict[headers[i]] = value
            result.append(row_dict)
    return result

def clean_text(lines):
    for line in lines:
        text = line['text']
        regex = re.compile(r'@11(.*?)@33')
        replaced_text = regex.sub(r'<b>\1</b>', text)
        line['text'] = replaced_text


def fill_in_schema_data(data):
    # Iterate over each dictionary in the list
    for i, d in enumerate(data):
        # Iterate over each key-value pair in the dictionary
        for key, value in d.items():
            # Check if the value is an empty string
            if value == '':
                # Iterate over predecessors to find the first non-empty value
                for j in range(i - 1, -1, -1):
                    if data[j][key] != '':
                        # Update the value with the non-empty value from the predecessor
                        data[i][key] = data[j][key]
                        break
def add_segment_nums(data):
    segment_num = 1
    # Iterate over each dictionary in the list
    for i, d in enumerate(data):
        # Check if the current dictionary is not the first one
        if i > 0:
            # Check if the current dictionary is equal to the previous one in all fields except "text"
            if all(d[key] == data[i - 1][key] for key in d if key != 'text'):
                # Increment the segment number
                segment_num += 1
            else:
                # Reset the segment number to 1
                segment_num = 1

        # Add the "segment num" field to the current dictionary
        d['segment_num'] = segment_num

sifra_schema_string = """
ברייתא דרבי ישמעאלויקרא דבורא דנדבהפרק אפרק בפרשה בפרק גפרשה גפרק דפרשה דפרק הפרק ופרשה הפרק זפרשה ופרק חפרשה זפרק טפרשה חפרק יפרשה טפרק יאפרשה יפרק יבפרשה יאפרק יגפרשה יבפרק ידפרשה יגפרק טופרק טזפרק יזפרשה ידפרק יחפרק יטפרק כ
ויקרא דבורא דחובהפרשה אפרק אפרשה בפרק בפרק גפרשה גפרק דפרק הפרשה דפרק ופרשה הפרק זפרשה ופרק חפרק טפרשה זפרק יפרק יאפרשה חפרק יבפרק יגפרשה טפרק ידפרק טופרק טזפרק יזפרשה יפרק יחפרק יטפרשה יאפרק כפרשה יבפרק כאפרק כבפרשה יגפרק כג
צופרק אפרק בפרשה בפרק גפרשה גפרק דפרק הפרשה דפרק ופרק זפרק חפרשה הפרק טפרק יפרשה ופרק יאפרשה זפרק יבפרשה חפרק יגפרשה טפרק ידפרק טופרשה יפרשה יאפרק טזפרק יזפרק יחמכילתא דמילואים א
שמינימכילתא דמילואים בפרשה אפרק אפרק בפרשה בפרק גפרק דפרשה גפרק הפרשה דפרק ופרשה הפרק זפרשה ופרק חפרשה זפרק טפרשה חפרק יפרשה טפרק יאפרשה יפרק יב
תזריע פרשת יולדתפרשה אפרק אפרק בפרק גפרק ד
תזריע פרשת נגעיםפרק אפרק בפרשה בפרק ב*פרשה גפרק גפרק דפרק הפרק ופרשה דפרק זפרשה הפרק חפרק טפרק יפרק יאפרק יבפרק יגפרק ידפרק טופרק טז
מצורעפרשה אפרק אפרשה בפרק בפרשה גפרק גפרשה דפרשה הפרשה ופרק דפרשה זפרק ה
מצורע פרשת זביםפרשה אפרק אפרק בפרשה בפרק גפרק דפרשה גפרק הפרק ופרשה דפרק זפרשה הפרק חפרק ט
אחרי מותפרשה אפרק אפרשה בפרק בפרק גפרשה גפרק דפרשה דפרק הפרק ופרשה הפרק זפרק חפרשה ופרק טפרק יפרשה זפרק יאפרק יבפרשה חפרק יג
קדושיםפרשה אפרק אפרק בפרק גפרשה בפרק דפרק הפרשה גפרק ופרק זפרק חפרשה דפרק טפרק יפרק יאפרק יב
אמורפרשה אפרק אפרשה בפרק בפרשה גפרק גפרשה דפרק דפרשה הפרשה ופרק הפרק ופרשה זפרק זפרשה חפרק חפרק טפרשה טפרק יפרק יאפרשה יפרק יבפרק יגפרשה יאפרק ידפרשה יבפרק טופרק טזפרק יזפרשה יגפרק יחפרשה ידפרק יטפרק כ
בהרפרשה אפרק אפרשה בפרק בפרק גפרשה גפרק דפרק הפרשה דפרק ופרשה הפרק זפרשה ופרק חפרק ט
בחוקתיפרשה אפרק אפרק בפרק גפרשה בפרק דפרק הפרק ופרק זפרק חפרשה גפרק טפרשה דפרק יפרק יאפרשה הפרק יבפרק יג

"""
chafetz_chaim_schema_string = """הקדמה
ברייתא דרבי ישמעאל
ויקרא דבורא דנדבה פרק א
פרק ב
פרשה ב
פרק ג
פרשה ג
פרק ד
פרשה ד
פרק ה
פרק ו
פרשה ה
פרק ז
פרשה ו
פרק ח
פרשה ז
פרק ט
פרשה ח
פרק י
פרשה ט
פרק יא
פרשה י
פרק יב
פרשה יא
פרק יג
פרשה יב
פרק יד
פרשה יג
פרק טו
פרק טז
פרק יז
פרשה יד
פרק יח
פרק יט
פרק כ
ויקרא דבורא דחובה פרשה א
פרק א
פרשה ב
פרק ב
פרק ג
פרשה ג
פרק ד
פרק ה
פרשה ד
פרק ו
פרשה ה
פרק ז
פרשה ו
פרק ח
פרק ט
פרשה ז
פרק י
פרק יא
פרשה ח
פרק יב
פרק יג
פרשה ט
פרק יד
פרק טו
פרק טז
פרק יז
פרשה י
פרק יח
פרק יט
פרשה יא
פרק כ
פרשה יב
פרק כא
פרק כב
פרשה יג
פרק כג
צו פרק א
פרק ב
פרשה ב
פרק ג
פרשה ג
פרק ד
פרק ה
פרשה ד
פרק ו
פרק ז
פרק ח
פרשה ה
פרק ט
פרק י
פרשה ו
פרק יא
פרשה ז
פרק יב
פרשה ח
פרק יג
פרשה ט
פרק יד
פרק טו
פרשה י
פרשה יא
פרק טז
פרק יז
פרק יח
מכילתא דמילואים א
שמיני מכילתא דמילואים ב
פרשה א
פרק א
פרק ב
פרשה ב
פרק ג
פרק ד
פרשה ג
פרק ה
פרשה ד
פרק ו
פרשה ה
פרק ז
פרשה ו
פרק ח
פרשה ז
פרק ט
פרק ח
פרק י
פרשה ט
פרק יא
פרשה י
פרק יב
תזריע פרשת יולדת פרשה א
פרק א
פרק ב
פרק ג
פרק ד
תזריע פרשת נגעים פרק א
פרק ב
פרשה ב
פרק ב*
פרשה ג
פרק ג
פרק ד
פרק ה
פרק ו
פרשה ד
פרק ז
פרשה ה
פרק ח
פרק ט
פרק י
פרק יא
פרק יב
פרק יג
פרק יד
פרק טו
פרק טז
מצורע פרשה א
פרק א
פרשה ב
פרק ב
פרשה ג
פרק ג
פרשה ד
פרשה ה
פרק ו
פרק ד
פרשה ז
פרק ה
מצורע פרשת זבים פרשה א
פרק א
פרק ב
פרשה ב
פרק ג
פרק ד
פרשה ג
פרק ה
פרק ו
פרשה ד
פרק ז
פרשה ה
פרק ח
פרק ט
אחרי מות פרשה א
פרק א
פרשה ב
פרק ב
פרק ג
פרשה ג
פרק ד
פרשה ד
פרק ה
פרק ו
פרשה ה
פרק ז
פרק ח
פרשה ו
פרק ט
פרק י
פרשה ז
פרק יא
פרק יב
פרשה ח
פרק יג
קדושים פרשה א
פרק א
פרק ב
פרק ג
פרשה ב
פרק ד
פרק ה
פרשה ג
פרק ו
פרק ז
פרק ח
פרשה ד
פרק ט
פרק י
פרק יא
פרק יב
אמור פרשה א
פרק א
פרשה ב
פרק ב
פרשה ג
פרק ג
פרשה ד
פרק ד
פרשה ה
פרשה ו
פרק ה
פרק ו
פרשה ז
פרק ז
פרשה ח
פרק ח
פרק ט
פרשה ט
פרק י
פרק יא
פרשה י
פרק יב
פרק יג
פרשה יא
פרק יד
פרשה יב
פרק טו
פרק טז
פרק יז
פרשה יג
פרק יח
פרשה יד
פרק יט
פרק כ
בהר פרשה א
פרק א
פרשה ב
פרק ב
פרק ג
פרשה ג
פרק ד
פרק ה
פרשה ד
פרק ו
פרשה ה
פרק ז
פרשה ו
פרק ח
פרק ט
בחוקתי פרשה א
פרק א
פרק ב
פרק ג
פרשה ב
פרק ד
פרק ה
פרק ו
פרק ז
פרק ח
פרשה ג
פרק ט
פרשה ד
פרק י
פרק יא
פרשה ה
פרק יב
פרק יג
"""


def prettify_schema_string(schema_string):
    schema_string = schema_string.replace("פרק", "\n"+'פרק')
    schema_string = schema_string.replace("פרשה", "\n" + 'פרשה')
    schema_string = schema_string.replace("ויקרא דבורא דנדבה", "\n" + 'ויקרא דבורא דנדבה')
    schema_string = schema_string.replace("מכילתא", "\n" + 'מכילתא')
    return (schema_string)

def print_dict_values(dict_list, keys):
    for d in dict_list:
        for key in keys:
            if key in d and d[key] != "":
                print(d[key])

def replace_substring(data, old_substring, new_substring):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = replace_substring(value, old_substring, new_substring)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = replace_substring(item, old_substring, new_substring)
    elif isinstance(data, str):
        if old_substring in data:
            data = data.replace(old_substring, new_substring)
    return data
def create_raavad_index():
    from sources.functions import post_index
    raavad_index = {}
    chafetz_chaim = library.get_index('Chafetz_Chaim_on_Sifra')
    # chafetz_chaim_schema = chafetz_chaim.schema

    raavad_index['title'] = "Ra'avad on Sifra"
    raavad_index['categories'] = chafetz_chaim.categories
    del chafetz_chaim.schema['titles'][0]
    raavad_index['schema'] = chafetz_chaim.schema
    replace_substring(raavad_index, 'Chafetz Chaim', "Ra'avad")
    replace_substring(raavad_index, 'חפץ חיים', 'ראב"ד')
    # raavad_index["categories"] = ["Midrash", "Commentary"]
    raavad_index['dependence'] = 'commentary'
    post_index(raavad_index)


    print('hi')


def create_text_map(lines):
    map = {}
    title = 'ראב"ד על ספרא'
    for line in lines:
        ref = (f"{title}, {line.get('parasha')}, {line.get('section_or_chapter', '')},"
               f" {line.get('paragraph').replace('(','').replace(')','').replace('ד ה','ד').replace('ו ז','ו').replace('ב ג','ב')},"
               f" {number_to_hebrew(line.get('segment_num'))}")
        ref = ref.replace(', ,', ',')
        map[ref] = line.get('text')
    return map

def handle_empty(node):
    ref = Ref(str(node))
    if ref.is_empty():
        print(ref)
        remove_branch(node)


def remove_empty_nodes():
    raavad_index = library.get_index("Ra'avad on Sifra")
    raavad_nodes = raavad_index.nodes
    raavad_nodes.traverse_tree(handle_empty)

def creaet_link(raavad_ref, sifra_ref):
    return(
        {
            "refs": [
                raavad_ref,
                sifra_ref
            ],
            # "generated_by": "Guide for the Perplexed_to_Efodi",
            "type": "Commentary",
            "auto": True
        }
    )
def insert_dict_links_to_db(list_of_dict_links):
    list_of_links = []
    for d in list_of_dict_links:
        list_of_links.append(Link(d))
    for l in list_of_links:
        l.save()


def link_raavad():
    link_dicts = []
    raavad_index = library.get_index("Ra'avad on Sifra")
    raavad_refs = raavad_index.all_segment_refs()
    for ref in raavad_refs:
        print(ref)
        raavad_tref = ref.tref
        sifra_tref = raavad_tref[:raavad_tref.rfind(':')].replace("Ra'avad on ", "")
        print(sifra_tref)
        link_dicts += [creaet_link(Ref(raavad_tref).normal(), Ref(sifra_tref).normal())]
    insert_dict_links_to_db(link_dicts)

if __name__ == '__main__':
    print("hello world")
    # create_raavad_index()
    # raavad_lines = csv_to_list_of_dicts('Raavad_on_Sifra_updated.csv')
    # clean_text(raavad_lines)
    # fill_in_schema_data(raavad_lines)
    # add_segment_nums(raavad_lines)
    # text_map = create_text_map(raavad_lines)
    # ingest_raavad(text_map)
    # remove_empty_nodes()


    link_raavad()



    # sifra = library.get_index("Sifra")
    # # print(chafetz_chaim_schema_string)
    # print(prettify_schema_string(sifra_schema_string))
    #
    # # print_dict_values(raavad_lines, ["parasha", "section_or_chapter"])
    print("end")











