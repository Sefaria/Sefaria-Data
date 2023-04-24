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

def post_playground_index():
    from sources.functions import post_index, post_text
    index = {"title": "Mishnat Eretz Yisrael on Pirkei Avot"}
    index = post_index(index, method='GET', server="https://piaseczno.cauldron.sefaria.org") #https://piaseczno.cauldron.sefaria.org
    index["title"] = "Mishnat Eretz Yisrael on Pirkei Avot Playground"
    index["schema"]["titles"] = [{'text': 'משנת ארץ ישראל על משנה אבות מגרש משחקים', 'lang': 'he', 'primary': True},
                                 {'text': 'Mishnat Eretz Yisrael on Pirkei Avot Playground', 'lang': 'en', 'primary': True}]
    # index["base_text_titles"] = [masechet_name]
    # index['dependence'] = 'commentary'
    # index["categories"] =  ["Mishnah", "Acharonim on Mishnah", "Gra", "Seder Tahorot"]
    # index["collective_title"] = 'Eliyahu Rabbah'
    post_index(index)
# def delete_all_existing_versions():
#     cur_version = VersionSet({'title': 'Introductions to the Babylonian Talmud',
#                               'versionTitle': "William Davidson Edition - Hebrew"})
#     if cur_version.count() > 0:
#         cur_version.delete()
#         print("deleted existing hebrew version")
#
#     cur_version = VersionSet({'title': 'Introductions to the Babylonian Talmud',
#                               'versionTitle': "William Davidson Edition - English"})
#     if cur_version.count() > 0:
#         cur_version.delete()
#         print("deleted existing english version")

def ingest_playground_version(version_map):
    # vs = VersionState(index=library.get_index("Mishnat Eretz Yisrael on Pirkei Avot Playground"))
    # vs.delete()
    # print("deleted version state")
    cur_version = VersionSet({'title': 'Mishnat Eretz Yisrael on Pirkei Avot Playground'})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    index = library.get_index("Mishnat Eretz Yisrael on Pirkei Avot Playground")

    chapter = index.nodes.create_skeleton()
    version_obj = Version({"versionTitle": "Mishnat Eretz Yisrael, Seder Nezikin, Jerusalem, 2013-",
                               "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH003570676/NLI",
                               "title": "Mishnat Eretz Yisrael on Pirkei Avot Playground",
                               "chapter": chapter,
                               "language": "en",
                               "digitizedBySefaria": True,
                               "license": "CC-BY-NC",
                               "status": "locked"
                               })

    modify_bulk_text(superuser_id, version_obj, version_map)

    print("finished updating version db")
if __name__ == '__main__':
    img_title_html_str = '<p class="mishna_project_image_title">Lorem ipsum dolor sit amet</p>'

    img1_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img1.jpg"   alt = "My Image" >' + img_title_html_str + "</div>"
    img2_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img2.jpg"  alt = "My Image" >'+ img_title_html_str + "</div>"
    img3_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img3.jpg"  alt = "My Image" >'+ img_title_html_str + "</div>"
    img4_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img4.jpg"  alt = "My Image" >'+ img_title_html_str + "</div>"
    lorem_str = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    duis_str = "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    version_map ={
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 1": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 2": img1_html_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 3": duis_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 4": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 5": img2_html_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 6": duis_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 7": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 8": img3_html_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 9": duis_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 10": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 11": img4_html_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 12": duis_str,
    }
    # post_playground_index()
    ingest_playground_version(version_map)



    print("hi")