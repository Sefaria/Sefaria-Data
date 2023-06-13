import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db

import csv

superuser_id = 171118
# import statistics

import json
from sefaria.model import *

all_indices = ['Eliyahu Rabbah on Mishnah Kelim',
    'Eliyahu Rabbah on Mishnah Makhshirin',
    'Eliyahu Rabbah on Mishnah Mikvaot',
    'Eliyahu Rabbah on Mishnah Negaim',
    'Eliyahu Rabbah on Mishnah Niddah',
    'Eliyahu Rabbah on Mishnah Oholot',
    'Eliyahu Rabbah on Mishnah Oktzin',
    'Eliyahu Rabbah on Mishnah Parah',
    'Eliyahu Rabbah on Mishnah Tahorot',
    'Eliyahu Rabbah on Mishnah Tevul Yom',
    'Eliyahu Rabbah on Mishnah Yadayim',
    'Eliyahu Rabbah on Mishnah Zavim'
]
def get_last_two_words(s):
    words = s.split()
    if len(words) < 2:
        return None
    else:
        if "Tevul Yom" in s:
            return ' '.join(words[-3:])
        else:
            return ' '.join(words[-2:])
def delete_until_last_colon(s):
    if ':' in s:
        s = s[:s.rindex(':')]
    return s
def delete_until_first_digit(s):
    for i in range(len(s)):
        if s[i].isdigit():
            return s[i:]
    return s
def clean_links():
    query = {"refs": {"$regex" : "Eliyahu Rabbah"}}
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        print("deleted link!")
        l.delete()


def ingest_version(version_map):
    vs = VersionState(index=library.get_index("Eliyahu Rabbah on Mishnah Kelim"))
    vs.delete()
    print("deleted version state")
    index = library.get_index("Eliyahu Rabbah on Mishnah Kelim")

    chapter = index.nodes.create_skeleton()
    version_obj = Version({"versionTitle": "Vilna, 1901",
                               "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH003488483/NLI",
                               "title": "Eliyahu Rabbah on Mishnah Kelim",
                               "chapter": chapter,
                               "language": "he",
                               "digitizedBySefaria": True,
                               "license": "CC-BY-NC",
                               "status": "locked"
                               })

    modify_bulk_text(superuser_id, version_obj, version_map)

    print("finished updating version db")
def csv_to_dict(csv_file):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        result_dict = {}
        for row in reader:
            result_dict[row[0]] = row[1]
    return result_dict

def insert_links_to_db(list_of_links):
    for l in list_of_links:

        l.save()

def list_of_dict_to_links(dicts):
    list_of_dicts = []
    for d in dicts:
        list_of_dicts.append(Link(d))
    return list_of_dicts

def fix_indices():
    from sources.functions import post_index, post_text
    for index_title in all_indices:
        masechet_name = get_last_two_words(index_title)
        index = {"title": index_title}
        index = post_index(index, method='GET', server="https://piaseczno.cauldron.sefaria.org") #https://piaseczno.cauldron.sefaria.org
        index["base_text_titles"] = [masechet_name]
        index['dependence'] = 'commentary'
        index["categories"] =  ["Mishnah", "Acharonim on Mishnah", "Gra", "Seder Tahorot"]
        index["collective_title"] = 'Eliyahu Rabbah'
        post_index(index, server = "https://piaseczno.cauldron.sefaria.org")

if __name__ == '__main__':
   r = Ref("Mishnah Niddah 8:5").text().text
   for index in all_indices:
       masechet_name = get_last_two_words(index)
       segment_refs = Ref(index).all_segment_refs()
       for seg_ref in segment_refs:
           mishsa_tref = masechet_name + ' ' + delete_until_first_digit(delete_until_last_colon(seg_ref.tref))
           if Ref(mishsa_tref).text().text == '':
               print(mishsa_tref)

   print("hi")
