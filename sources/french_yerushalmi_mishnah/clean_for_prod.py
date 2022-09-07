import django

django.setup()

import statistics
import re
import csv
from sefaria.model import *



def renumber_footnotes_by_chapter():
    dict_list = []
    with open('french_mishnah_original.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        chapter = 1
        count = 1
        renumbered_list = []
        for row in german_mishnah_csv:
            cur_chapter = Ref(row['mishnah_tref']).sections[0]
            de_text = row['yerushalmi_french_text']
            if chapter != cur_chapter:
                # Reset chapter
                chapter = cur_chapter
                # Reset the count
                count = 1

            # Todo - add explanatory comments
            matches = re.finditer(r"<sup>(\d*)<\/sup><i class=\"footnote\">", row['yerushalmi_french_text'])
            matches = list(matches)
            fixed_footnote_text = ''
            is_first_match = True
            old_idx = 0
            if len(matches) > 0:
                last = matches[-1]
            for match in matches:
                is_last_match = True if match == last else False
                start_idx = match.start()
                end_idx = match.end()
                match_str = de_text[start_idx:end_idx]
                fixed_footnote = re.sub(r"\d+", str(count), match_str)

                if is_first_match:
                    fixed_footnote_text += de_text[:start_idx]
                else:
                    fixed_footnote_text += de_text[old_idx:start_idx]

                # Fix punctuation issue (i.e. if no punctuation, add a space)
                if de_text[end_idx] != "," or de_text[end_idx] != "." or de_text[end_idx] != ";" or de_text[end_idx] != " ":
                    fixed_footnote += " "
                    end_idx += 1

                fixed_footnote_text += fixed_footnote

                if is_last_match:
                    fixed_footnote_text += de_text[end_idx-1:]

                count += 1
                is_first_match = False
                old_idx = end_idx-1

            if len(fixed_footnote_text) > 1:
                renumbered_list.append({'mishnah_tref': row['mishnah_tref'], 'yerushalmi_french_text': fixed_footnote_text})
            else:
                renumbered_list.append(row)
        return renumbered_list


def post_process(mishnah_list):
    cleaned_text_list = []
    # if de text starts with a space, or punctuation
    for mishnah in mishnah_list:
        cleaned_text = mishnah['yerushalmi_french_text']
        cleaned_text = cleaned_text.lstrip(".")
        cleaned_text = cleaned_text.lstrip(",")
        cleaned_text = cleaned_text.lstrip(";")
        cleaned_text = cleaned_text.lstrip()
        cleaned_text_list.append({'mishnah_tref': mishnah['mishnah_tref'], 'yerushalmi_french_text': cleaned_text})
    return cleaned_text_list




# This function generates the CSV of the Mishnayot
def generate_csv(mishnah_list):
    headers = ['mishnah_tref',
               'yerushalmi_french_text']
    with open(f'french_mishnah_cleaned.csv', 'w+') as file:
        mishnah_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
        c = csv.DictWriter(file, fieldnames=headers)
        c.writeheader()
        c.writerows(mishnah_list)

    print("File writing complete")


# Updates the CSV to renumber the footnotes and delete the roman numerals
def run():
    mishnah_list = renumber_footnotes_by_chapter()
    mishnah_list = post_process(mishnah_list)
    generate_csv(mishnah_list)


if __name__ == "__main__":
    run()