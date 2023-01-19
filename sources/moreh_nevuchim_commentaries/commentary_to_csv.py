import django

django.setup()

django.setup()

# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.system.database import db
import time
from docx import Document


def latin_numeral_to_hebrew_numeral(latin_numeral):
    if latin_numeral == "I":
        return ("א'")
    if latin_numeral == "II":
        return ("ב'")
    if latin_numeral == "III":
        return ("ג'")
    if latin_numeral == "IV":
        return ("ד'")
    if latin_numeral == "V":
        return ("ה'")
    if latin_numeral == "VI":
        return ("ו'")
    if latin_numeral == "VII":
        return ("ז'")
    if latin_numeral == "VIII":
        return ("ח'")
    if latin_numeral == "IX":
        return ("ט'")
    if latin_numeral == "X":
        return ("י'")
    if latin_numeral == "XI":
        return ('י"א')
    if latin_numeral == "XII":
        return ('י"ב')
    if latin_numeral == "XIII":
        return ('י"ג')
    if latin_numeral == "XIV":
        return ('י"ד')
    if latin_numeral == "XV":
        return ('ט"ו')
    if latin_numeral == "XVI":
        return ('ט"ז')
    if latin_numeral == "XVII":
        return ('י"ז')
    if latin_numeral == "XVIII":
        return ('י"ח')
    if latin_numeral == "XIX":
        return ('י"ט')
    if latin_numeral == "XX":
        return ("כ'")
    if latin_numeral == "XXI":
        return ('כ"א')
    if latin_numeral == "XXII":
        return ('כ"ב')
    if latin_numeral == "XXIII":
        return ('כ"ג')
    if latin_numeral == "XXIV":
        return ('כ"ד')
    if latin_numeral == "XXV":
        return ('כ"ה')
    if latin_numeral == "XXVI":
        return ('כ"ו')
    if latin_numeral == "XXVII":
        return ('כ"ז')
    if latin_numeral == "XXVIII":
        return ('כ"ח')
    if latin_numeral == "XXIX":
        return ('כ"ט')
    if latin_numeral == "XXX":
        return ("ל'")


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
    # structure:
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
    # index = library.get_index("Introductions to the Babylonian Talmud")
    # parent = index.nodes
    nodes_list = []
    current_masechet = "no masechet yet"
    for segment_dict in list_of_masechtot:
        if (segment_dict['masechet'] == starting_masechet_name) or found_starting_masechet_flag:
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
            # insert_last_child(masechet_node, parent)
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
    print("finished updating index db")


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


def ingest_english_version():
    vs = VersionState(index=library.get_index("Introductions to the Babylonian Talmud"))
    vs.delete()
    print("deleted version state")
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


def ingest_hebrew_version():
    vs = VersionState(index=library.get_index("Introductions to the Babylonian Talmud"))
    vs.delete()
    print("deleted version state")
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


def delete_all_existing_versions():
    cur_version = VersionSet({'title': 'Introductions to the Babylonian Talmud',
                              'versionTitle': "William Davidson Edition - Hebrew"})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing hebrew version")

    cur_version = VersionSet({'title': 'Introductions to the Babylonian Talmud',
                              'versionTitle': "William Davidson Edition - English"})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing english version")


def reorder_masechet_nodes():
    masechtot_keys_ordered = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Rosh Hashanah", "Yoma", "Sukkah", "Beitzah",
                              "Taanit", "Megillah", "Moed Katan", "Chagigah",
                              "Yevamot", "Ketubot", "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin",
                              "Bava Kamma", "Bava Metzia", "Bava Batra", "Sanhedrin", "Makkot", "Shevuot",
                              "Avodah Zarah", "Horayot",
                              "Zevachim", "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah", "Keritot", "Meilah",
                              "Tamid", "Niddah"]
    index = library.get_index("Introductions to the Babylonian Talmud")
    reorder_children(index.nodes, masechtot_keys_ordered)
    print("finished re-ordering")


def roman_to_int(s):
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]
    return int_val


def create_links(csv_object):
    links = []
    for ref_dict in csv_object:
        raw_ref = ref_dict['ref']
        if "Perek" in raw_ref:
            # exact_ref = library.get_index('Berakhot').get_alt_structs['Perek'][0]['wholeRef']
            chapter_num = roman_to_int(raw_ref.split("Perek", 1)[1].strip())
            exact_ref = Ref(ref_dict["masechet"] + ", Chapter " + str(chapter_num)).normal()
            # text_display_en = ref_dict["masechet"] + ", Chapter " + str(chapter_num)
            # text_display_he = ref_dict["masechet_hebrew"] + ", פרק " + str(chapter_num)


        else:
            exact_ref = str(Ref(ref_dict["masechet"]).as_ranged_segment_ref())
            # text_display_en = ref_dict["masechet"]
            # text_display_he = ref_dict["masechet_hebrew"]

        new_link_dict = {
            "refs": [ref_dict['ref'], exact_ref],               #[ref_dict['ref'], exact_ref], [ref_dict['ref'], "Berakhot 2a:1"]
            "type": "essay",
            "versions": [
                {
                    "title": "NONE", "language": "en" # "title": "ALL", "language": "en"  "title": "NONE", "language": "en"
                },
                {
                    "title": "ALL", "language": "ALL"
                }
            ],
            "displayedText": [
                {
                    "en": ref_dict["title"],  # raw_ref.split("Talmud,", 1)[1].strip(),
                    "he": ref_dict["title_hebrew"]  # raw_ref.split("Talmud,", 1)[1].strip()
                },
                {
                    "en": "",
                    "he": ""
                }
            ]

        }
        new_link = Link(new_link_dict)

        links.append(new_link)

    return (links)

    # refs: list with two trefs
    # type: "essay"
    # versions: list with version titles
    # displayedText: list with displayed text
    #


def delete_existing_links(query={"generated_by": "Koren Intro Parse Script"}):
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        l.delete()

def delete_existing_koren_links(query={"generated_by": "Koren Intro Parse Script"}):
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        l.delete()

def delete_existing_automated_links(query={"type": "", "refs": {"$regex" : "Introductions to the Babylonian Talmud"}}):
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        if Ref(l.refs[0]).is_bavli():
            l.delete()

def delete_existing_correct_essay_links(query={"type":"essay", "refs": {"$regex" : "Introductions to the Babylonian Talmud"}}):
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
            l.delete()

def insert_links_to_db(list_of_links):
    for l in list_of_links:
        l.save()



    # m = library._index_map
    # index = library.get_index("Introductions to the Babylonian Talmud")

    # english_version = Version().load({"title": "Introductions to the Babylonian Talmud", "versionTitle": "William Davidson Edition - English"})

    # hebrew_version = Version().load(
    #     {"title": "Introductions to the Babylonian Talmud", "versionTitle": "William Davidson Edition - Hebrew"})
    # with open("introductions_to_the_babylonian_talmud_index.json") as f:
    #     new_index = json.load(f)
    #
    # db.index.insert_one(new_index)
    # index = library.get_index("Introductions to the Babylonian Talmud")


if __name__ == '__main__':
    print("hello world")
    # "Guide for the Perplexed, Part 1 2:7"
    ref_prefix = "Efodi on Guide for the Perplexed, "
    sections = ["Introduction, Letter to R Joseph son of Judah", "Introduction, Prefatory Remarks", "Introduction, Introduction",
                "Part 1", "Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]
    ref = ''
    ref_chapter = 0
    ref_paragraph = 0
    # Open the docx file
    document = Document('efodi.docx')

    comm_list = []
    letter_to_R_Joseph_son_of_Judah = {}
    prefatory_Remarks = {}
    introduction = {}
    part_1 = {}
    part_2_introduction = {}
    part_2 = {}
    part_3_introduction = {}
    part_3 = {}
    comm_list = [letter_to_R_Joseph_son_of_Judah, prefatory_Remarks, introduction, part_1, part_2_introduction, part_2, part_3_introduction, part_3]



    # Print the text of the docx file
    section_index = -1
    for para in document.paragraphs:
        print(para.text)
        if para.text == '' or '@22' in para.text:
            continue
        if '@00' in para.text and not para.text.startswith("@00פרק"):
            section_index += 1
            ref_chapter = 0
            ref_paragraph = 0

        elif '@00' in para.text:
            ref_chapter += 1;
            ref_paragraph = 0

        else:
            ref_paragraph += 1
            if section_index in {0,1,2,4,6}:
                ref = str(ref_prefix) + sections[section_index] + ' ' + str(ref_paragraph)

            else:
                ref = str(ref_prefix) + sections[section_index] + ' ' + str(ref_chapter) + ' ' + ":" + str(ref_paragraph)
            comm_list[section_index][ref] = para.text.translate(str.maketrans("", "", "0123456789@"))
        # cleaned_string = para.text.translate(str.maketrans("", "", "0123456789@"))
        # print(cleaned_string)
    he_title, en_title = """רב פנינים על משלי / Rav Peninim on Proverbs""".split(" / ")
    en_title = 'Efodi on Guide for the Perplexed'
    he_title = 'אפודי על מורה נבוכים'
    root = SchemaNode()
    root.add_primary_titles(en_title, he_title)
    intro = SchemaNode()
    intro.add_shared_term("Introduction")
    letter = JaggedArrayNode()
    letter.add_structure(["Paragraph"])
    prefatory = JaggedArrayNode()
    prefatory.add_structure(["Paragraph"])
    introduction = JaggedArrayNode()
    introduction.add_structure(["Paragraph"])
    intro.key = "Introduction"
    letter.ket = "Letter to R Joseph son of Judah"
    prefatory.key = "Prefatory Remarks"
    introduction.key = "Introduction"

    part2_intro = JaggedArrayNode()
    part2_intro.add_structure(["Paragraph"])
    part2_intro.key = "Part 2 Introduction"

    part2 = JaggedArrayNode()

    # default = JaggedArrayNode()
    # default.default = True
    # default.key = "default"
    # default.add_structure(["Chapter", "Verse", "Comment"])
    root.append(intro)
    # root.append(default)
    root.validate()
    # post_index({"title": en_title,
    #             "base_text_titles": ["Proverbs"],
    #             "base_text_mapping": "many_to_one_default_only",
    #             "dependence": "Commentary", "collective_title": "Alshich",
    #             "categories": ["Tanakh", "Commentary", "Alshich", "Writings"], "schema": root.serialize()})

    superuser_id = 171118

