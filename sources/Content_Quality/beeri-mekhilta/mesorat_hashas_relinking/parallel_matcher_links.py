import django

django.setup()

from sefaria.model import *
import re
import csv
from linking_utilities.parallel_matcher import ParallelMatcher
import pandas as pd
from beeri_utilities import write_to_csv


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
    matcher = ParallelMatcher(lambda x: re.sub('[^א-ת ]', '', x).split(), all_to_all=False)
    return matcher


def parse_matcher(result_str):
    links = re.findall(r"- .*? - (.*)<===>(.*?)-.*SCORE: (.*)", result_str)[0]
    beeri = links[0]
    other = links[1]
    score = links[2]
    return beeri, other, score



if __name__ == '__main__':
    matched_csv_dict = []
    unmatched_csv_dict = []
    matcher = set_up_matcher()
    links = get_mesorat_hashas_links()

    for link in links:

        beeri = link["beeri_mekhilta_ref"]
        other = link["other_text_ref"]

        try:
            match_list = matcher.match([beeri, other], return_obj=True)
        except Exception as e:
            print(f"Matcher failed for {link}")

        if match_list:
            for m in match_list:
                beeri_refined, other_refined, score = parse_matcher(str(m))
                result_dict = {"beeri_ref": beeri_refined, "other_ref": other_refined}

                # Check for duplicates
                if result_dict not in matched_csv_dict:
                    matched_csv_dict.append(result_dict)

        else:
            unmatched_csv_dict.append({"beeri_ref": beeri, "other_ref": other})

    # write to a CSV
    write_to_csv("mesorat_hashas_links_matched.csv", matched_csv_dict)
    write_to_csv("mesorat_hashas_links_unmatched.csv", unmatched_csv_dict)
