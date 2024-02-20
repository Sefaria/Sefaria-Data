import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
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


def post_indices():
    from sources.functions import post_index, post_term
    yahel_or_term = {"name": "Yahel Ohr", "titles": [{"lang": "en", "text": "Yahel Ohr", "primary": True},
                                        {"lang": "he", "text": "יהל אור", "primary": True}], "scheme": "toc_categories"}
    # post_term(yahel_or_term, server="https://yahel-ohr.cauldron.sefaria.org")
    nefesh_david_index = post_index({'title': 'Nefesh David on Zohar'}, server="https://www.sefaria.org.il", method="GET")
    yahel_or_index = nefesh_david_index
    yahel_or_index["title"] = "Yahel Ohr on Zohar"
    yahel_ohr_first_node = yahel_or_index["schema"]
    yahel_or_index["schema"] = {"nodes":[{},{}], "titles": '', "key": ''}
    yahel_or_index["schema"]["nodes"][0] = yahel_ohr_first_node
    del yahel_ohr_first_node["titles"]
    del yahel_ohr_first_node['key']
    yahel_ohr_first_node["default"] = True
    yahel_ohr_first_node["key"] = "default"
    yahel_or_index["schema"]["nodes"][1] =  {
                "nodeType" : "JaggedArrayNode",
                "depth" : 1,
                "addressTypes" : [
                    "Integer"
                ],
                "sectionNames" : [
                    "Paragraph"
                ],
                "titles" : [
                    {
                        "text" : "Addenda",
                        "lang" : "en",
                        "primary" : True
                    },
                    {
                        "text" : "ליקוטים",
                        "lang" : "he",
                        "primary" : True
                    }
                ],
                "key" : "Addenda",
                # "default" : False
            }
    yahel_or_index["schema"]["titles"] = [{'lang': 'en', 'text': 'Yahel Ohr'}, {'lang': 'he', 'primary': True, 'text': 'יהל אור על ספר הזהר'}, {'lang': 'he', 'text': 'יהל אור על הזהר'}, {'lang': 'he', 'text': 'יהל אור'}, {'lang': 'en', 'primary': True, 'text': 'Yahel Ohr on Zohar'}]
    yahel_or_index["schema"]["key"] = 'Yahel Ohr on Zohar'
    del yahel_or_index['enDesc']
    del yahel_or_index['heDesc']
    del yahel_or_index["enShortDesc"]
    del yahel_or_index["heShortDesc"]
    yahel_or_index['collective_title'] = "Yahel Ohr"
    post_index(yahel_or_index, server="https://yahel-ohr.cauldron.sefaria.org")
    # post_index(yahel_or_index)

def ingest_yahel(book_map):
    index = library.get_index("Yahel Ohr on Zohar")
    cur_version = VersionSet({'title': "Yahel Ohr on Zohar",
                              "versionTitle" : "Vilna 1882"})

    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Vilna 1882",
                       "versionSource": "https://he.wikisource.org/wiki/%D7%99%D7%94%D7%9C_%D7%90%D7%95%D7%A8",
                       "title": "Yahel Ohr on Zohar",
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


def prettify_sifra_schema_string(schema_string):
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

if __name__ == '__main__':
    print("hello world")
    raavad_lines = csv_to_list_of_dicts('Raavad_on_Sifra_updated.csv')
    sifra = library.get_index("Sifra")
    print(prettify_sifra_schema_string(sifra_schema_string))
    print_dict_values(raavad_lines, ["parasha", "section_or_chapter"])
    print("end")











