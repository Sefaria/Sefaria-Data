# import json

import django
django.setup()

# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.system.database import db


def latin_numeral_to_hebrew_numeral(latin_numeral):
    if latin_numeral == "I":
        return("א'")
    if latin_numeral ==  "II":
        return("ב'")
    if latin_numeral ==  "III":
        return("ג'")
    if latin_numeral == "IV":
        return("ד'")
    if latin_numeral == "V":
        return("ה'")
    if latin_numeral == "VI":
        return("ו'")
    if latin_numeral == "VII":
        return("ז'")
    if latin_numeral == "VIII":
        return("ח'")
    if latin_numeral ==  "IX":
        return("ט'")
    if latin_numeral == "X":
        return("י'")
    if latin_numeral == "XI":
        return('י"א')
    if latin_numeral ==  "XII":
        return('י"ב')
    if latin_numeral ==  "XIII":
        return('י"ג')
    if latin_numeral == "XIV":
        return('י"ד')
    if latin_numeral == "XV":
        return('ט"ו')
    if latin_numeral == "XVI":
        return('ט"ז')
    if latin_numeral == "XVII":
        return('י"ז')
    if latin_numeral == "XVIII":
        return('י"ח')
    if latin_numeral ==  "XIX":
        return('י"ט')
    if latin_numeral == "XX":
        return("כ'")
    if latin_numeral == "XXI":
        return('כ"א')
    if latin_numeral == "XXII":
        return('כ"ב')
    if latin_numeral == "XXIII":
        return('כ"ג')
    if latin_numeral == "XXIV":
        return('כ"ד')
    if latin_numeral == "XXV":
        return('כ"ה')
    if latin_numeral == "XXVI":
        return('כ"ו')
    if latin_numeral == "XXVII":
        return('כ"ז')
    if latin_numeral == "XXVIII":
        return('כ"ח')
    if latin_numeral ==  "XXIX":
        return('כ"ט')
    if latin_numeral == "XXX":
        return("ל'")



def translate_title_to_hebrew(title, masechet_hebrew):
    hebrew_title = ''
    if 'Introduction to' in title:
        hebrew_title += 'הקדמה ל'

        if " Perek " in title:
            hebrew_title += 'פרק '
            hebrew_title += latin_numeral_to_hebrew_numeral(title.split(' ')[3].strip())
            return hebrew_title

        else:
            hebrew_title += "מסכת "
            hebrew_title += masechet_hebrew
            return hebrew_title

    if 'Summary of' in title:
        hebrew_title += 'סיכום לפרק '
        numeral = title.split(' ')[3].strip()
        hebrew_title += latin_numeral_to_hebrew_numeral(numeral)
        return hebrew_title

def parse_csv_to_object():
    list_of_dicts = []
    #structure:
    [{'ref': ...,
    'english_text': [],
    'hebrew_text': [],
    'masechet': ...,
    'masechet_hebrew': ...,
    'title': 'Introduction to Berakhot',
    'title_hebrew': ''}]
    with open('introductions.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')

        current_ref_dict = {}
        for row in r:
            ref = row[0]
            if ref != '':
                current_ref_dict = {}
                current_ref_dict["ref"] = ref
                current_ref_dict['english_text'] = []
                current_ref_dict['english_text'].append(row[1])
                current_ref_dict['hebrew_text'] = []
                current_ref_dict['hebrew_text'].append(row[2])

                ##########################
                # getting titles and mesechtot:

                ref_parts = ref.split(',')

                masechet = ref_parts[1].strip()
                masechet_hebrew = Ref(masechet).he_normal()

                title = ref_parts[2].strip()
                title_hebrew = translate_title_to_hebrew(title, masechet_hebrew)

                current_ref_dict["masechet"] = masechet
                current_ref_dict["masechet_hebrew"] = masechet_hebrew
                current_ref_dict["title"] = title
                current_ref_dict["title_hebrew"] = title_hebrew
                if len(current_ref_dict["english_text"]) == 1:
                    list_of_dicts.append(current_ref_dict)
            else:
                current_ref_dict['english_text'].append(row[1])
                current_ref_dict['hebrew_text'].append(row[2])

    return (list_of_dicts)

def get_list_of_masechtot_nodes(list_of_masechtot, starting_masechet_name):

    found_starting_masechet_flag = False
    #index = library.get_index("Introductions to the Babylonian Talmud")
    #parent = index.nodes
    nodes_list = []
    current_masechet = "no masechet yet"
    for segment_dict in list_of_masechtot:
        if(segment_dict['masechet'] == starting_masechet_name) or found_starting_masechet_flag:
            found_starting_masechet_flag = True
            if segment_dict['masechet'] != current_masechet:

                masechet_node = SchemaNode()
                masechet_node.key = segment_dict["masechet"]  # should be equal to primary title
                masechet_node.add_primary_titles(segment_dict["masechet"], segment_dict["masechet_hebrew"])

            leaf_node = JaggedArrayNode()
            leaf_node.add_primary_titles(segment_dict["title"], segment_dict["title_hebrew"])
            leaf_node.add_structure(["Paragraph"])
            masechet_node.append(leaf_node)
            if segment_dict['masechet'] != current_masechet:
                nodes_list.append(masechet_node)
            current_masechet = segment_dict['masechet']
            #insert_last_child(masechet_node, parent)
    return nodes_list

def list_of_masechtot_to_db(nodes_list):

    ####dangerous way to add new nodes:
    # index = library.get_index("Introductions to the Babylonian Talmud")
    # parent = index.nodes
    # for node in nodes_list:
    #     insert_last_child(node, parent)
    for node in nodes_list:
        index = library.get_index("Introductions to the Babylonian Talmud")
        parent = index.nodes
        insert_last_child(node, parent)


def object_to_dict_of_refs(csv_parsed_object, language):

    refs_dict = {}
    text_language = ""
    if language == "english":
        text_language = "english_text"
    if language == "hebrew":
        text_language = "hebrew_text"

    for chapter in csv_parsed_object:
            paragraph_num = 1
            for paragraph in chapter[text_language]:
                ref = chapter["ref"] + " " + str(paragraph_num)
                refs_dict[ref] = paragraph
                ##refs_dict[ref] = ":)"
                paragraph_num += 1
    return refs_dict


# m = library._index_map
# index = library.get_index("Introductions to the Babylonian Talmud")
if __name__ == '__main__':
    superuser_id = 171118
    # with open("introductions_to_the_babylonian_talmud_index.json") as f:
    #     new_index = json.load(f)
    #
    # db.index.insert_one(new_index)



    cur_version = VersionSet({'title': 'Introductions to the Babylonian Talmud',
                              'versionTitle': "William Davidson Edition - Hebrew"})
    if cur_version.count() > 0:
        cur_version.delete()

    cur_version = VersionSet({'title': 'Introductions to the Babylonian Talmud',
                              'versionTitle': "William Davidson Edition - English"})
    if cur_version.count() > 0:
        cur_version.delete()

    # with open("introductions_to_the_babylonian_talmud_index.json") as f:
    #     new_index = json.load(f)
    #
    # db.index.insert_one(new_index)
    # index = library.get_index("Introductions to the Babylonian Talmud")

    print("hello")


    csv_object = parse_csv_to_object()
    index_nodes = get_list_of_masechtot_nodes(csv_object, "Sanhedrin")
    list_of_masechtot_to_db(index_nodes)
    print("finished updating index db")


    #english_version = Version().load({"title": "Introductions to the Babylonian Talmud", "versionTitle": "William Davidson Edition - English"})




    # hebrew_version = Version().load(
    #     {"title": "Introductions to the Babylonian Talmud", "versionTitle": "William Davidson Edition - Hebrew"})





    index = library.get_index("Introductions to the Babylonian Talmud")

    chapter = index.nodes.create_skeleton()
    english_version = Version({"versionTitle": "William Davidson Edition - English",
                               "versionSource": "'https://korenpub.com/collections/the-noe-edition-koren-talmud-bavli-1'",
                               "title": "Introductions to the Babylonian Talmud",
                               "chapter": chapter,
                               "language": "en",
                               "digitizedBySefaria": True,
                               "license": "CC-BY-NC",
                               "status": "locked"
                               })

    version_text_map_english = object_to_dict_of_refs(csv_object, "english")
    modify_bulk_text(superuser_id, english_version, version_text_map_english)

    print("finished updating English version db")





    index = library.get_index("Introductions to the Babylonian Talmud")
    chapter = index.nodes.create_skeleton()
    hebrew_version = Version({"versionTitle": "William Davidson Edition - Hebrew",
                              "versionSource": "'https://korenpub.com/collections/the-noe-edition-koren-talmud-bavli-1'",
                              "title": "Introductions to the Babylonian Talmud",
                              "chapter": chapter,
                              "language": "he",
                              "digitizedBySefaria": True,
                              "license": "CC-BY-NC",
                              "status": "locked"
                              })
    version_text_map_hebrew = object_to_dict_of_refs(csv_object, "hebrew")
    modify_bulk_text(superuser_id, hebrew_version, version_text_map_hebrew)
    print("finished updating Hebrew version db")


