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
    if parasha and parasha != "Matot Masei":
        return Ref(parasha)
    elif parasha == "Matot Masei":
        return Ref("Matot-Masei")

def extract_dibbur_hamatchil(txt):
    dhm = re.findall(r"<b>(.*?)</b>", txt, re.DOTALL)
    if len(dhm) < 1:
        return ""
    return dhm[0]

def attempt_to_match(base_words, comment_list):
    results = match_text(base_words,
                         comment_list,
                         dh_extract_method=extract_dibbur_hamatchil,
                         lang='en')
    print(results)
    return results['matches']


if __name__ == '__main__':
    ma = Index().load({'title': 'Megaleh Amukot on Torah'})

    sections = ma.all_section_refs()
    for section_title in sections:
        parasha_text_ref = get_parasha_text_ref(section_title)

        if not parasha_text_ref:
            # Skip holidays
            continue

        parasha_text = parasha_text_ref.text(lang="he").text
        parasha_text_words = []
        for perek in parasha_text:
            for pasuk in perek:
                pasuk_cleaned = pasuk.replace("-", " ")
                parasha_text_words += pasuk_cleaned.split(" ")

        commentary_text = section_title.text(lang="he").text
        attempt_to_match(base_words=parasha_text_words, comment_list=commentary_text)
        # print(f"{section_title} <<>> {parasha_text_ref}")
