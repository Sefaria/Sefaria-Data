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
from docx import Document


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
    create_category(['Jewish Thought', 'Guide for the Perplexed'], 'Guide for the Perplexed', "מורה נבוכים")
    create_category(['Jewish Thought', 'Guide for the Perplexed', "Commentary"], 'Commentary', "מפרשים")

def create_text_object():
    ref_prefix = "Crescas on Guide for the Perplexed, "
    sections = ["Introduction, Letter to R Joseph son of Judah", "Introduction, Prefatory Remarks",
                "Introduction, Introduction",
                "Part 1", "Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]
    ref = ''
    ref_chapter = 0
    ref_paragraph = 0
    # Open the docx file
    document = Document('crescas.docx')

    comm_list = []
    letter_to_R_Joseph_son_of_Judah = {}
    prefatory_Remarks = {}
    introduction = {}
    part_1 = {}
    part_2_introduction = {}
    part_2 = {}
    part_3_introduction = {}
    part_3 = {}
    comm_list = [letter_to_R_Joseph_son_of_Judah, prefatory_Remarks, introduction, part_1, part_2_introduction, part_2,
                 part_3_introduction, part_3]

    # Print the text of the docx file
    section_index = -1
    for para in document.paragraphs:
        if para.text == '' or para.text == ' ' or para.text == '  ' or '@22' in para.text:
            continue
        if '@00' in para.text and not para.text.startswith("@00פרק"):
            section_index += 1
            ref_chapter = 0
            ref_paragraph = 0
            print(para.text)

        elif '@00' in para.text:
            ref_chapter += 1;
            if '@00פרק' in para.text:
                ref_chapter = compute_gematria(extract_last_word(para.text))
            ref_paragraph = 0
            print(para.text)

        else:
            ref_paragraph += 1
            if section_index in {0, 1, 2, 4, 6}:
                ref = str(ref_prefix) + sections[section_index] + ' ' + str(ref_paragraph)

            else:
                ref = str(ref_prefix) + sections[section_index] + ' ' + str(ref_chapter) + ":" + str(
                    ref_paragraph)
            text = ''
            # Iterate over the runs in the paragraph
            for run in para.runs:
                if run.bold and run.text != '@' and not run.text.isnumeric():
                    text += "<b>" + run.text + "</b>"
                else:
                    text += run.text

            # print(text)
            # comm_list[section_index][ref] = para.text.translate(str.maketrans("", "", "0123456789@"))
            comm_list[section_index][ref] = text.translate(str.maketrans("", "", "0123456789@")).replace("</b><b>", "").replace("</b> <b>", "").replace(" </b>", "</b> ")
            # comm_list[section_index][ref] = "AAAAAAAAAAA"
    return {**comm_list[0], **comm_list[1], **comm_list[2], **comm_list[3], **comm_list[4], **comm_list[5], **comm_list[6], **comm_list[7]}


def ingest_version(map_text):
    # vs = VersionState(index=library.get_index("Introductions to the Babylonian Talmud"))
    # vs.delete()
    # print("deleted version state")
    index = library.get_index("Crescas on Guide for the Perplexed")
    cur_version = VersionSet({'title': 'Crescas on Guide for the Perplexed'})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Warsaw, 1872",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH990017717720205171/NLI",
                       "title": "Crescas on Guide for the Perplexed",
                       "language": "he",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })


    modify_bulk_text(superuser_id, version, map_text)
def ingest_nodes():
    from sources.functions import post_index
    from sources.functions import add_term

    en_title = 'Crescas on Guide for the Perplexed'
    he_title = 'קרשקש על מורה נבוכים'
    root = SchemaNode()
    root.add_primary_titles(en_title, he_title)
    introduction_node = SchemaNode()
    introduction_node.key = "Introduction"
    introduction_node.add_shared_term("Introduction")
    introduction_node.add_primary_titles("Introduction", 'הקדמה')

    letter_to_R_Joseph_son_of_Judah_node = JaggedArrayNode()
    letter_to_R_Joseph_son_of_Judah_node.add_structure(["Paragraph"])
    letter_to_R_Joseph_son_of_Judah_node.key = "Letter to R Joseph son of Judah"
    letter_to_R_Joseph_son_of_Judah_node.add_primary_titles("Letter to R Joseph son of Judah", 'איגרת')
    prefatory_Remarks_node = JaggedArrayNode()
    prefatory_Remarks_node.add_structure(["Paragraph"])
    prefatory_Remarks_node.key = "Prefatory Remarks"
    prefatory_Remarks_node.add_primary_titles("Prefatory Remarks", 'פתיחת הרמב"ם')
    inner_introduction_node = JaggedArrayNode()
    inner_introduction_node.add_structure(["Paragraph"])
    inner_introduction_node.key = "Introduction"
    inner_introduction_node.add_primary_titles("Introduction", 'הקדמה')


    # insert_last_child(introduction_node, letter_to_R_Joseph_son_of_Judah_node)
    # insert_last_child(introduction_node, prefatory_Remarks_node)
    # insert_last_child(introduction_node, inner_introduction_node)
    introduction_node.append(letter_to_R_Joseph_son_of_Judah_node)
    introduction_node.append(prefatory_Remarks_node)
    introduction_node.append(inner_introduction_node)

    part1_node = JaggedArrayNode()
    part1_node.add_structure(["Chapter", "Paragraph"])
    part1_node.key = "Part 1"
    part1_node.add_primary_titles("Part 1", 'חלק א')


    part2_introduction_node = JaggedArrayNode()
    part2_introduction_node.add_structure(["Paragraph"])
    part2_introduction_node.key = "Part 2 Introduction"
    part2_introduction_node.add_primary_titles("Part 2 Introduction", "חלק ב' הקדמה")

    part2_node = JaggedArrayNode()
    part2_node.add_structure(["Chapter", "Paragraph"])
    part2_node.key = "Part 2"
    part2_node.add_primary_titles("Part 2", 'חלק ב')

    part3_introduction_node = JaggedArrayNode()
    part3_introduction_node.add_structure(["Paragraph"])
    part3_introduction_node.key = "Part 3 Introduction"
    part3_introduction_node.add_primary_titles("Part 3 Introduction", "חלק ג' הקדמה")

    part3_node = JaggedArrayNode()
    part3_node.add_structure(["Chapter", "Paragraph"])
    part3_node.key = "Part 3"
    part3_node.add_primary_titles("Part 3", 'חלק ג')

    root.append(introduction_node)
    root.append(part1_node)
    root.append(part2_introduction_node)
    root.append(part2_node)
    root.append(part3_introduction_node)
    root.append(part3_node)
    root.validate()

    # add_term("Crescas", u"קרשקש", scheme='commentary_works', server="http://localhost:8000/")
    # t = Term()
    # term_dict = {
    #     'name': "Crescas",
    #     'scheme': "commentary_works",
    #     'titles': [{'lang': 'en', 'text': "Crescas", 'primary': True}, {'lang': 'he', 'text': "קרשקש", 'primary': True}]
    # }
    # add_term("Monthly Cycle", u"לוח חודשי")
    index = {
        "title": en_title,
        "schema": root.serialize(),
        "categories": ['Jewish Thought', 'Guide for the Perplexed', "Commentary"],
        "dependence": 'commentary',
        "base_text_titles": ["Guide for the Perplexed"],
        "collective_title": "Crescas"

        # "collective_title": {"en": "Crescas", "he": "קרשקש"}
    }
    post_index(index, server="https://guide-commentaries.cauldron.sefaria.org")
    # post_index(index)

if __name__ == '__main__':
    print("hello world")

    # t = Term()
    # t.name = 'Crescas'
    # t.scheme = 'commentary_works'
    # t.set_titles([{'lang': 'en', 'text': 'Crescas', 'primary': True}, {'lang': 'he', 'text': 'קרשקש', 'primary': True}])
    # t.save()

    ingest_nodes()

    # obj = create_text_object()
    # print(obj)
    # ingest_version(obj)
    # add_new_categories()






