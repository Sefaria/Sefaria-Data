import django

django.setup()

import csv
import re
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


# This function generates a CSV given a list of dicts
def generate_csv(dict_list, headers, file_name):
    dict_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
    with open(f'{file_name}.csv', 'w+') as file:
        c = csv.DictWriter(file, fieldnames=headers)
        c.writeheader()
        c.writerows(dict_list)

    print(f"File writing of {file_name} complete")


def clean_text(german_text):
    german_text = str(german_text)
    text_array = re.sub(r"\[|\]|\{|\}", "", german_text)
    return text_array


def get_french_text(talmud_ref):
    french_text = talmud_ref.text('en', vtitle='Le Talmud de Jérusalem, traduit par Moise Schwab, 1878-1890 [fr]')
    french_text = french_text.text
    french_text = clean_text(french_text)
    return french_text


def get_hebrew_text(talmud_ref):
    heb_text = talmud_ref.text('he', vtitle='Mechon-Mamre')
    heb_text = heb_text.text
    return heb_text


def parse_french_mishnah():
    mishnah_list = []

    ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})

    for link in ls:
        refs = link.refs
        mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
        french_text = get_french_text(Ref(talmud_ref))
        heb_text = get_hebrew_text(Ref(talmud_ref))

        mishnah_list.append({
            'mishnah_tref': mishnah_ref,
            'talmud_tref': talmud_ref,
            'french_text': french_text,
            'hebrew_text': heb_text
        })
    return mishnah_list


if __name__ == "__main__":
    mishnah_list = parse_french_mishnah()
    generate_csv(mishnah_list, ['mishnah_tref', 'talmud_tref', 'french_text', 'hebrew_text'], 'french_mishnah')
