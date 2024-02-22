import django

django.setup()

import re
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import match_text


# Run DH on each parasha
# Post all created links

def get_parasha_text_ref(section_title):
    sec_title_key = section_title.normal().split(", ")
    parasha = sec_title_key[1] if "For" not in sec_title_key[1] else None  # filter out holidays
    parasha_transliteration_map = {"Shemot": "Parashat Shemot",
                                   "Vayikra": "Parashat Vayikra",
                                   "Bamidbar": "Parashat Bamidbar",
                                   "Devarim": "Parashat Devarim",
                                   "Shoftim": "Parashat Shoftim",
                                   "Matot Masei": "Matot-Masei"}
    if parasha and parasha in ["Shemot", "Vayikra", "Bamidbar", "Devarim", "Shoftim", "Matot Masei"]:
        parasha = parasha_transliteration_map[parasha]
    return Ref(parasha) if parasha else None


def extract_dibbur_hamatchil(txt):
    dhm = re.findall(r"<b>(.*?)</b>", txt, re.DOTALL)
    if len(dhm) < 1:
        return ""
    dhm = re.sub(r'[^\w\s]', '', dhm[0])
    return dhm


def attempt_to_match(base_words, comment_list):
    results = match_text(base_words,
                         comment_list,
                         dh_extract_method=extract_dibbur_hamatchil,
                         word_threshold=0.1,
                         char_threshold=0.2,
                         lang='he')
    return results


if __name__ == '__main__':
    ma = Index().load({'title': 'Megaleh Amukot on Torah'})

    sections = ma.all_section_refs()
    for section_title in sections:
        parasha_text_ref = get_parasha_text_ref(section_title)

        if not parasha_text_ref:
            # Skip holidays
            continue

        segment_refs_for_parasha = parasha_text_ref.range_list()

        segment_refs_for_commentary = section_title.all_segment_refs()

        for comm_seg_ref in segment_refs_for_commentary:

            commentary_text = comm_seg_ref.text(lang="he").text

            for pasuk_ref in segment_refs_for_parasha:

                pasuk_text = pasuk_ref.text(lang="he", vtitle="Tanach with Text Only").text
                pasuk_text_words = []
                pasuk_cleaned = pasuk_text.replace("-", " ")
                pasuk_text_words += pasuk_cleaned.split(" ")

                match = attempt_to_match(base_words=pasuk_text_words, comment_list=[commentary_text])

                for i in range(len(match["matches"])):
                    if match["matches"][i] != (-1, -1):
                        num_words = match['match_text'][i][1].split(" ")
                        if len(num_words) < 2: # ignore one word matches
                            continue
                        print(f"{comm_seg_ref.normal()} <<>> {pasuk_ref.normal()}")
                        print(f"Score: {match['matches'][i]} for {match['match_text'][i]}")