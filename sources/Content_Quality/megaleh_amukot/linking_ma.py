import django

django.setup()

from sefaria.model import *


# Run DH on each parasha
# Post all created links

def get_parasha_text_ref(section_title):
    sec_title_key = section_title.normal().split(", ")
    parasha = sec_title_key[1] if "For" not in sec_title_key[1] else None  # filter out holidays
    if parasha and parasha != "Matot Masei":
        return Ref(parasha)
    elif parasha == "Matot Masei":
        return Ref("Matot-Masei")


if __name__ == '__main__':
    ma = Index().load({'title': 'Megaleh Amukot on Torah'})

    sections = ma.all_section_refs()
    for section_title in sections:
        parasha_text_ref = get_parasha_text_ref(section_title)

        # TODO - match goes here.
        print(f"{section_title} <<>> {parasha_text_ref}")
