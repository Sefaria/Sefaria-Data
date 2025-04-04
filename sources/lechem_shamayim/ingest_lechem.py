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
import Levenshtein

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
# masechtot = ["Shabbat",
#  "Eruvin",
#  "Pesachim",
#  "Shekalim",
#  "Yoma",
#  "Sukkah",
#  "Beitzah",
#  "Rosh Hashanah",
#  "Ta'anit",
#  "Megillah",
#  "Moed Katan",
#  "Chagigah"
# ]
# masechtot = ["Yevamot",
#  "Ketubot",
#  "Nedarim",
# "Nazir",
#  "Sotah",
#  "Gittin",
# "Kiddushin",
# ]
# masechtot = [
# "Bava Kamma",
#  "Bava Metzia",
#  "Bava Batra",
#  "Sanhedrin",
#  "Makkot",
#  "Shevuot",
#  "Eduyot",
#  "Avodah Zarah",
# # "Pirkei Avot",
# "Horayot"
# ]
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
        # if masechet == 'Berakhot':
        #     continue
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
       post_index(index)
       # post_index(index, server="https://lechemshamayim.cauldron.sefaria.org")         #, server = "https://piaseczno.cauldron.sefaria.org"
def post_intro_index():
    from sources.functions import post_index

    index_dict = {'title': 'Lechem Shamayim, Introduction to Mishnah Commentary',
                  'categories': ['Mishnah', 'Acharonim on Mishnah', 'Lechem Shamayim'],
                  "schema": {"nodeType": "JaggedArrayNode", "depth": 1, "addressTypes": ["Integer"], "sectionNames": ["Paragraph"], "titles": [{"primary": True, "lang": "en", "text": "Lechem Shamayim, Introduction to Mishnah Commentary"}, {"primary": True, "lang": "he", "text": "לחם שמים, הקדמה לפירוש המשנה"},], "key": "Lechem Shamayim, Introduction to Mishnah Commentary"},
                  # 'schema': {'nodeType': 'JaggedArrayNode', 'depth': 3, 'addressTypes': ['Perek', 'Mishnah', 'Integer'], 'sectionNames': ['Chapter', 'Mishnah', 'Comment'],
                  #            'titles': [{'lang': 'he', 'text': 'לחם שמים על '+ masechet_name_he, 'primary': True},
                  #                       {'text': 'Lechem Shamayim on ' + masechet_name_en, 'lang': 'en', 'primary': True}],
                  #            'key': 'Lechem Shamayim on '+ masechet_name_en},
                  'authors': ['yaakov-emden'],
                  # 'enDesc': "Commentary of R' Yaakov Emden on Mishnah.", 'heDesc': "ביאור לר' יעקב עמדין על המשנה.",
                  'pubDate': '1728', 'compDate': '1725', 'pubPlace': 'Altona', 'errorMargin': '3', 'era': 'AH',
                  'collective_title': 'Lechem Shamayim'}
    post_index(index_dict,  server="https://lechemshamayim.cauldron.sefaria.org")
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

def extract_integers(string):
    pattern = r'\d+'
    matches = re.findall(pattern, string)
    integers = [int(match) for match in matches]
    return integers
def validate_document(file_path):
    def find_misplaced_endings(strings):

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

def parse_and_ingest_intro(file_path):
    docx_text = read_docx(file_path)
    lines = docx_text.split('\n')
    lines = [line for line in lines if line != '']
    intro_map = {}
    for index, line in enumerate(lines):
        # Add <b> tags before @11
        if '@22' in line:
            line = '<b>' + line + '</b>'
        # Add <b> tags before @11
        line = re.sub(r'(@11)', r'<b>\1', line)

        # Add </b> tags before @33
        line = re.sub(r'(@33)', r'</b>\1', line)

        # Add <b> tags before @44
        line = re.sub(r'(@44)', r'<b>\1', line)

        # Add </b> tags before @55
        line = re.sub(r'(@55)', r'</b>\1', line)

        line = re.sub(r'[@\d]', '', line)
        intro_map["Lechem Shamayim, Introduction to Mishnah Commentary "+ str(index+1)] = line
    index = library.get_index('Lechem Shamayim, Introduction to Mishnah Commentary')
    cur_version = VersionSet({'title': 'Lechem Shamayim, Introduction to Mishnah Commentary'})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleting existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Jerusalem, 1978",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH990012730190205171/NLI",
                       "title": 'Lechem Shamayim, Introduction to Mishnah Commentary',
                       "language": "he",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })
    modify_bulk_text(superuser_id, version, intro_map)

def handle_mishne(file_path_mishne, file_path_lechem):
    docx_text_mishne = read_docx(file_path_mishne)
    parsed_version_mishne = parse_text(docx_text_mishne)
    text_obj_mishne = create_text_object(parsed_version_mishne)
    prettify_version(text_obj_mishne)

    docx_text = read_docx(file_path_lechem)
    parsed_version = parse_text(docx_text)
    text_obj = create_text_object(parsed_version)
    prettify_version(text_obj)

    def find_key_and_max_last_integer(dictionary, prefix):
        matched_keys = [key for key in dictionary if key.startswith(prefix)]
        matched_keys_with_integer = [key for key in matched_keys if key[len(prefix):].split(':')[-1].isdigit()]

        if not matched_keys_with_integer:
            return None, 0

        max_key = max(matched_keys_with_integer, key=lambda key: int(key[len(prefix):].split(':')[-1]))
        max_integer = int(max_key[len(prefix):].split(':')[-1])
        return max_key, max_integer

    for key in text_obj_mishne:
        prefix = key.split(':')[0]+':'
        print(prefix)
        a,b = find_key_and_max_last_integer(text_obj, prefix)
        mishne_lechem_string = "משנה לחם"
        text_obj[prefix+str(b+1)] = "<small>" + mishne_lechem_string + "<br>" + text_obj_mishne[key].rstrip() + "</small>"

    ingest_version(text_obj)

def add_links():

    def list_of_dict_to_links(dicts):
        list_of_dicts = []
        for d in dicts:
            list_of_dicts.append(Link(d))
        return list_of_dicts

    def clean_links(masechet):
        query = {"refs": {"$regex": "Lechem Shamayim on Mishnah "+ masechet }}
        list_of_links = LinkSet(query).array()
        for l in list_of_links:
            print("deleted link!")
            l.delete()
    def insert_links_to_db(list_of_links):
        for l in list_of_links:
            l.save()
    def delete_until_last_colon(s):
        if ':' in s:
            s = s[:s.rindex(':')]
        return s

    def delete_until_first_digit(s):
        for i in range(len(s)):
            if s[i].isdigit():
                return s[i:]

    def check_bold_period(text):
        text = text.replace(" ", "")
        if text.startswith("<b>") and "</b>" in text and text.index("</b>") + len("</b>") < len(text) and text[
            text.index("</b>") + len("</b>")].strip() == '.':
            return True
        if text.startswith("<b>") and "</b>" in text and text.index("</b>") + len("</b>") < len(text) and text[
            text.index("</b>") -1].strip() == '.':
            return True
        else:
            return False

    # def get_bold_substring(text):
    #     start_tag = "<b>"
    #     end_tag = "</b>"
    #     start_index = text.find(start_tag)
    #     if start_index != -1:
    #         start_index += len(start_tag)
    #         end_index = text.find(end_tag, start_index)
    #         if end_index != -1:
    #             return text[start_index:end_index]
    #     return None
    def extract_dibbur(input_string):
        substring = input_string
        # Find the index of the first period
        # period_index = input_string.find('.')
        # if period_index != -1:
        #     # Extract the substring until the first period
        #     substring = input_string[:period_index]
        # etc_index = input_string.find("וכו'")
        # if etc_index != -1:
        #     # Extract the substring until the first period
        #     substring = input_string[:etc_index]
        # etc_index2 = input_string.find("כו'")
        # if etc_index2 != -1:
        #     # Extract the substring until the first period
        #     substring = input_string[:etc_index2]
        bold_index = input_string.find('</b>')
        if bold_index != -1:
            # Extract the substring until the first period
            substring = input_string[:bold_index]


        # Remove '<b>' and '</b>' from the substring
        substring = substring.replace('<b>', '').replace('</b>', '')

        return substring


    def is_likely_quoted(s1, s2):
        s1_length = len(s1)
        s2_length = len(s2)
        # if s1_length == 0:
        #     return False

        if s1_length >= s2_length:
            return False

        for i in range(s2_length - s1_length + 1):
            sub_s2 = s2[i:i + s1_length]

            distance = Levenshtein.distance(s1, sub_s2)
            similarity = 1 - (distance / s1_length)

            if similarity >= 0.7:  # Adjust this threshold as needed
                return True

        return False
    def start_new_sequence(tref, corresponding_mishnah_tref):


        seg_num = extract_integers(tref)[-1]
        if seg_num == 1:
            return True
        text = Ref(tref).text('he').text

        if "אבל מניחה לגת הבאה" in text:
            a = 8


        if "משנה לחם" in text:
            return True
        if check_bold_period(text.strip()):
            return True
        if not text.startswith('<b>'):
            False
        # if "$" in text or text == '':
        #     return False

        suspected_dibbur = extract_dibbur(text)
        if suspected_dibbur == None:
            return False
        suspected_dibbur = suspected_dibbur.strip()
        suspected_base_text = Ref(corresponding_mishnah_tref).text('he', "Mishnah, ed. Romm, Vilna 1913").text.strip()
        if is_likely_quoted(suspected_dibbur, suspected_base_text):
            return True

        else:
            return False






    auto_links = []

    for masechet in masechtot:
        # masechet_name = get_last_two_words(index)
        print("Linking Masechet "+ masechet)
        clean_links(masechet)

        segment_refs = Ref("Lechem Shamayim on Mishnah "+ masechet).all_segment_refs()
        trefs_sequence = []
        previous_tref_chapter = 0
        for seg_ref in segment_refs:
            current_tref_chapter = extract_integers(seg_ref.tref)[0]
            corresponding_mishnah_tref = "Mishnah " + masechet + ' ' + delete_until_first_digit(delete_until_last_colon(seg_ref.tref))


            if current_tref_chapter != previous_tref_chapter or start_new_sequence(seg_ref.tref, corresponding_mishnah_tref):
                if trefs_sequence:
                    extended_tref = Ref(trefs_sequence[0]).to(Ref(trefs_sequence[-1])).tref
                    auto_links.append(
                        {
                            "refs": [
                                extended_tref,
                                "Mishnah " + masechet + ' ' + delete_until_first_digit(delete_until_last_colon(trefs_sequence[-1]))
                            ],
                            "type": "Commentary",
                            "auto": True
                        }
                    )
                trefs_sequence.clear()
                trefs_sequence.append(seg_ref.tref)
            else:
                trefs_sequence.append(seg_ref.tref)
            previous_tref_chapter = current_tref_chapter
        if trefs_sequence:
            extended_tref = Ref(trefs_sequence[0]).to(Ref(trefs_sequence[-1])).tref
            auto_links.append(
                {
                    "refs": [
                        extended_tref,
                        corresponding_mishnah_tref
                    ],
                    "type": "Commentary",
                    "auto": True
                }
            )



    auto_links = list_of_dict_to_links(auto_links)
    insert_links_to_db(auto_links)


if __name__ == '__main__':
    print("hello world")
    # add_new_categories()ii
    file_path = "lechem_nashim.docx"
    # post_indices()
    #
    # docx_text = read_docx(file_path)
    # parsed_version = parse_text(docx_text)
    # text_obj = create_text_object(parsed_version)
    # prettify_version(text_obj)
    # ingest_version(text_obj)
    # handle_mishne("mishne_zeraim.docx", "lechem_zeraim.docx")



    # "Guide for the Perplexed, Part 1 2:7"
    # ingest_nodes()

    # obj = create_text_object()
    # print(obj)
    # ingest_version(obj)
    # add_new_categories()
    # validate_document("mishne_moed.docx")

    # post_intro_index()
    # parse_and_ingest_intro("lechem_intro.docx")

    add_links()








