import django

django.setup()

from sefaria.model import *
import re
import csv, json
# from linking_utilities.parallel_matcher import ParallelMatcher
from linking_utilities.parallel_matcher import *
import pandas as pd
# from sources.Content_Quality.beeri_mekhilta.beeri_utilities import write_to_csv


# For mesorat hashas link
# Map the Mekhilta side to the Beeri (if not already)
# Generate refined links, print

def get_mesorat_hashas_links():
    # Read the CSV file into a DataFrame
    df = pd.read_csv("../mekhilta_link_report_qa.csv", on_bad_lines='warn')

    # Filter rows where 'generated_by' is equal to 'mesorat_hashas'
    filtered_df = df[df['generated_by'] == 'mesorat_hashas.py All']
    filtered_df.drop(columns=["old_mekhilta_ref", "type", "all", "status"], inplace=True)

    # Convert the filtered DataFrame to a dictionary
    filtered_dict = filtered_df.to_dict(orient='records')
    return filtered_dict


def set_up_matcher(tokenizer=lambda x: re.sub('[^א-ת ]', '', x).split()):
    matcher = ParallelMatcher(tokenizer,
                              all_to_all=False,
                              min_words_in_match=5,
                              ngram_size=7,
                              min_distance_between_matches=0)
    return matcher


def parse_matcher(result_str):
    links = re.findall(r"- .*? - (.*)<===>.*?- .*? - (.*?): SCORE: (.*)", result_str)[0]
    beeri = links[0]
    other = links[1]
    score = links[2]
    return beeri, other, score

def get_snippet_from_mesorah_item(mesorah_item, pm):
    words = pm.word_list_map[mesorah_item.mesechta]
    return " ".join(words[mesorah_item.location[0]:mesorah_item.location[1]+1])

def print_mesorah_json(json_filename):
    with open(json_filename, 'r') as file:
        data = json.load(file)
    list_of_matches = []
    for item in data:
        dict_item = {'mekhilta': item[0], 'other': item[1]}
        list_of_matches.append(dict_item)
    for match in list_of_matches:
        print(match['mekhilta'])
        print(Ref(match['mekhilta']).text(lang="he").as_string())
        print(match['other'])
        print(Ref(match['other']).text(lang="he").as_string())
        print("###################################################")
def get_normalizer():
    from sefaria.helper.normalization import NormalizerComposer
    return NormalizerComposer(['unidecode', 'br-tag', 'itag', 'html', 'maqaf', 'cantillation', 'double-space'])

normalizer = get_normalizer()
def talmud_tokenizer(s):
    s = normalizer.normalize(s)
    s = re.sub(r'\u05BE', ' ', s)  # replace maqaf / hyphen with space
    s = re.sub(r'[\u0591-\u05C7]', '', s)
    s = re.sub(r'[\u2000-\u206F\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E]', '', s)  # remove punctuation
    for match in re.finditer(r'\(.*?\)', s):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            s = s.replace(match.group(), "")
    words = [w for w in re.split(r'\s+',s) if  w != '']
    return words

if __name__ == '__main__':
    matched_csv_dict = []
    unmatched_csv_dict = []
    matcher = set_up_matcher(talmud_tokenizer)
    # links = get_mesorat_hashas_links()

    # Try here matching the Mekhilta to Masechet Pesachim as a trial
    # For all index, do one at a time in comparison to Mekhilta (2 at a time, Mekhilta to Midrash, Mekhilta to Talmud)
    # for index in library.get_all in category

    # Running...
    # Generate btwn M and all TBSP in on go:
    # tref list... ["Mekhilta", "Pesachim|Midrash|Berakhot"]
    # Generated btwn M to M,
    # tref list ["Mekhilta"]... w "all-to-all" true.

    # Fallback: Fiddle w params

    match_list = matcher.match(["Mekhilta DeRabbi Yishmael, Tractate Pischa", "Pesachim 2a-50a"], return_obj=True)

    # filter_pasuk_matches("All", "mesorat_hashas_indexes.json")
    # print_mesorah_json("mesorat_hashas_pasuk_filtered_bad.json")



    if match_list:
        for m in match_list:
            print("Pesachim:")
            print(m.a.ref)
            text = m.a.ref.text(lang="he").as_string()
            print(text)
            text_of_match = get_snippet_from_mesorah_item(m.a, matcher)
            print(text_of_match)


            print("Mechilta:")
            print(m.b.ref)
            text = m.b.ref.text(lang="he").as_string()
            print(text)
            text_of_match = get_snippet_from_mesorah_item(m.b, matcher)
            print(text_of_match)

            print("###########################################################")

            # beeri_refined, other_refined, score = parse_matcher(str(m))
            # result_dict = {"beeri_ref": beeri_refined, "other_ref": other_refined}
            #
            # # Check for duplicates
            # if result_dict not in matched_csv_dict:
            #     matched_csv_dict.append(result_dict)

    # write to a CSV
    # print(f"Num Pesachim matches {len(matched_csv_dict)}")


    # write_to_csv("mekhilta_to_pesachim_links.csv", matched_csv_dict)
