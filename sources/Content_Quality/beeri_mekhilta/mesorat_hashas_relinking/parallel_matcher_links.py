import django

django.setup()

from sefaria.model import *
import re
import csv
from linking_utilities.parallel_matcher import ParallelMatcher
import pandas as pd
from sources.Content_Quality.beeri_mekhilta.beeri_utilities import write_to_csv


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


def set_up_matcher():
    matcher = ParallelMatcher(lambda x: re.sub('[^א-ת ]', '', x).split(),
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



if __name__ == '__main__':
    matched_csv_dict = []
    unmatched_csv_dict = []
    matcher = set_up_matcher()
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

    match_list = matcher.match(["Mekhilta DeRabbi Yishmael", "Pesachim"], return_obj=True)

    if match_list:
        for m in match_list:
            beeri_refined, other_refined, score = parse_matcher(str(m))
            result_dict = {"beeri_ref": beeri_refined, "other_ref": other_refined}

            # Check for duplicates
            if result_dict not in matched_csv_dict:
                matched_csv_dict.append(result_dict)

    # write to a CSV
    print(f"Num Pesachim matches {len(matched_csv_dict)}")
    write_to_csv("mekhilta_to_pesachim_links.csv", matched_csv_dict)


    #####

    """
    Old Mekhilta 12:1 (a,b,c,d,e) <<<>>>>> Pesachim 2a.1 (a,x,y,z)
    BM 1.1 (a)                    <<<<>>>> Pesachim 2a.1 (a,x,y,z) 
    ....
    """