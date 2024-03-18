import django

django.setup()

import re
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import match_text
from sources.functions import match_ref_interface, post_link


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


def attempt_to_match(base_words, comments):
    results = match_text(base_words,
                         comments,
                         dh_extract_method=extract_dibbur_hamatchil,
                         word_threshold=0.1,
                         char_threshold=0.2,
                         lang='he')
    return results


def simple_tokenizer(text):
    """
    A simple tokenizer that splits text into tokens by whitespace,
    and removes apostrophes and periods from the tokens.
    """

    def remove_nikkud(hebrew_string):
        # Define a regular expression pattern for Hebrew vowel points
        nikkud_pattern = re.compile('[\u0591-\u05BD\u05BF-\u05C2\u05C4\u05C5\u05C7]')

        # Use the sub method to replace vowel points with an empty string
        cleaned_string = re.sub(nikkud_pattern, '', hebrew_string)

        return cleaned_string

    # Replace apostrophes and periods with empty strings
    text = text.replace("'", "")
    text = text.replace(".", "")
    text = text.replace("׳", "")
    text = text.replace("–", "")
    text = text.replace(";", "")
    text = remove_nikkud(text)

    # Split the text into tokens by whitespace
    tokens = text.split()
    return tokens


if __name__ == '__main__':
    ma = Index().load({'title': 'Megaleh Amukot on Torah'})

    sections = ma.all_section_refs()
    count = 1
    for section_title in sections:
        parasha_text_ref = get_parasha_text_ref(section_title)
        count += 1

        if not parasha_text_ref:
            # Skip holidays
            continue

        segment_refs_for_commentary = section_title.all_segment_refs()

        segs = section_title.all_segment_refs()
        comments = [seg.text("he").text for seg in segs]
        links = match_ref_interface(base_ref=parasha_text_ref.normal(),
                                    comm_ref=section_title.normal(),
                                    comments=comments,
                                    base_tokenizer=simple_tokenizer,
                                    dh_extract_method=extract_dibbur_hamatchil)

        for l in links:
            post_link(l)