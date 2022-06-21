import django

django.setup()

import csv
import re

from sefaria.model import *
from sefaria.model.schema import AddressTalmud


class MishnahRow:

    def __init__(self, mishnah_tref, talmud_tref, mishnah_mishnah_text, yerushalmi_mishnah_text):
        self.mishnah_tref = mishnah_tref
        self.talmud_tref = talmud_tref
        self.mishnah_mishnah_text = mishnah_mishnah_text
        self.yerushalmi_mishnah_text = yerushalmi_mishnah_text

    def __str__(self):
        return f"Mishnah Tref: {self.mishnah_tref}, " \
               f"Talmud Tref: {self.talmud_tref}, " \
               f"Mishnah Mishnah Text: {self.mishnah_mishnah_text}, " \
               f"Yerushalmi Mishnah Text: {self.yerushalmi_mishnah_text}"

    # Returns a dictionary representation of the row
    def get_row(self):
        return {
            "mishnah_tref": self.mishnah_tref,
            "talmud_tref": self.talmud_tref,
            "mishnah_mishnah_text": self.mishnah_mishnah_text,
            "yerushalmi_mishnah_text": self.yerushalmi_mishnah_text
        }

    # Accessors and Mutators
    def set_mishnah_tref(self, new_tref):
        self.mishnah_tref = new_tref

    def set_talmud_tref(self, new_tref):
        self.talmud_tref = new_tref

    def set_mishnah_mishnah_text(self, new_text):
        self.mishnah_mishnah_text = new_text

    def set_yerushalmi_mishnah_text(self, new_text):
        self.yerushalmi_mishnah_text = new_text

    def get_mishnah_tref(self):
        return self.mishnah_tref

    def get_talmud_tref(self):
        return self.talmud_tref

    def get_mishnah_mishnah_text(self):
        return self.mishnah_mishnah_text

    def get_yerushalmi_mishnah_text(self):
        return self.yerushalmi_mishnah_text


class FrenchMishnahManager:

    def __init__(self):
        pass


# Todo - create a utility file?

# This function generates a CSV given a list of dicts
def generate_csv(dict_list, headers, file_name):
    with open(f'{file_name}.csv', 'w+') as file:
        c = csv.DictWriter(file, fieldnames=headers)
        c.writeheader()
        c.writerows(dict_list)
    print(f"File writing of {file_name} complete")


def clean_text(raw_text):
    raw_text = str(raw_text)
    text_array = re.sub(r"\[|\]|\{|\}", "", raw_text)
    return text_array


def get_numbers_from_yerushalmi_tref(y_tref):
    result = re.findall(r".* (\d*:\d*:\d*)$", y_tref)
    if result:
        return result[0]
    else:
        return y_tref


def create_list_yerushalmi_masechtot():
    yerushalmi_masechtot = []
    talmud_indices = library.get_indexes_in_category("Yerushalmi")
    for index in talmud_indices:
        masechet = re.findall(r"Jerusalem Talmud (.*?)$", index)
        yerushalmi_masechtot.append(masechet[0])
    return yerushalmi_masechtot


# This function creates a list of mishnah trefs, and extracts any masechtot
# that are not also found in the Yerushalmi
def create_list_of_yerushalmi_mishnah_trefs():
    full_tref_list = []

    # Clean out non-Yerushalmi references
    talmud_indices = library.get_indexes_in_category("Yerushalmi", full_records=True)
    for index in talmud_indices:
        mishnah_refs = index.all_segment_refs()
        for mishnah in mishnah_refs:
            mishnah_tref = mishnah.normal()
            first_segment = re.match(r".*:1$", mishnah_tref)

            # First segment is usually the Mishnah text
            if first_segment:
                full_tref_list.append(mishnah_tref)
    return full_tref_list


# This function creates a list of mishnah trefs, and extracts any masechtot
# that are not Yerushalmi
def create_list_of_mishnah_mishnah_trefs():
    mishnah_indices = library.get_indexes_in_category("Mishnah", full_records=True)
    full_tref_list = []
    yerushalmi_mishnah_mishnah_refs = []
    for index in mishnah_indices:
        mishnah_refs = index.all_segment_refs()
        for mishnah in mishnah_refs:
            full_tref_list.append(mishnah.normal())
    yerushalmi_masechtot = create_list_yerushalmi_masechtot()

    for mishnah in full_tref_list:
        mishnah_masechet = Ref(mishnah).index.title
        if mishnah_masechet in yerushalmi_masechtot:
            yerushalmi_mishnah_mishnah_refs.append(mishnah)
    return yerushalmi_mishnah_mishnah_refs


def get_french_text(talmud_ref):
    french_text = talmud_ref.text('en', vtitle='Le Talmud de Jérusalem, traduit par Moise Schwab, 1878-1890 [fr]')
    french_text = french_text.text
    french_text = clean_text(french_text)
    return french_text


def get_hebrew_text(ref, type='yerushalmi-mishnah'):
    if type == 'yerushalmi-mishnah':
        heb_text = ref.text('he', vtitle='Mechon-Mamre')
        heb_text = heb_text.text
    elif type == 'mishnah-mishnah':
        heb_text = ref.text('he', vtitle='Torat Emet 357')
        heb_text = heb_text.text
        heb_text = heb_text[:-1]

    return heb_text


def parse_french_mishnah():
    mishnah_list = []

    ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})

    for link in ls:
        refs = link.refs
        mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
        french_text = get_french_text(Ref(talmud_ref))
        mm_text = get_hebrew_text(Ref(mishnah_ref), type="mishnah-mishnah")
        ym_text = get_hebrew_text(Ref(talmud_ref), type="yerushalmi-mishnah")
        mishnah_list.append(MishnahRow(mishnah_ref, talmud_ref, mm_text, ym_text).get_row())
    return mishnah_list


def get_yerushalmi_linkset_mishnahs():
    ym_list = []
    ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})
    for link in ls:
        refs = link.refs
        mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
        ym_list.append(mishnah_ref)
    return ym_list


def create_normalized_ref_list(mishnah):
    refs = Ref(mishnah['mishnah_tref']).range_list()
    refs_normal = []
    for ref in refs:
        refs_normal.append(ref.normal())
    return refs_normal


def check_overlap(refs_normal):
    ym_list = get_yerushalmi_linkset_mishnahs()
    is_overlapping = False
    for each_ref in refs_normal:
        if each_ref in ym_list:
            is_overlapping = True
    return is_overlapping


# Given a tref, where the prev tref is the same
# Concatenate this yerushalmi mishnah text to the prev
# Delete this row

# TODO - Concatenate ref
def handle_duplicated_single_ref(mishnah_list):
    cleaned_mishnah_list = [mishnah_list[0]]

    for i in range(1, len(mishnah_list) - 1):

        prev = mishnah_list[i - 1]
        cur = mishnah_list[i]
        next = mishnah_list[i + 1]

        # If there's a case of a repeated tref, concatenate the text
        # and eliminate the redundancy.
        if cur['mishnah_tref'] == prev['mishnah_tref']:
            prev['yerushalmi_mishnah_text'] += f" {cur['yerushalmi_mishnah_text']}"
            prev['talmud_tref'] += f", {get_numbers_from_yerushalmi_tref(cur['talmud_tref'])}"
            cleaned_mishnah_list.append(prev)
        elif cur['mishnah_tref'] != next['mishnah_tref']:  # avoid double counting bug
            cleaned_mishnah_list.append(cur)
    return cleaned_mishnah_list


def handle_non_overlapping_ranged_ref(cleaned_mishnah_list, refs_normal, mishnah):
    cleaned_mishnah_list.append(
        MishnahRow(refs_normal[0], mishnah['talmud_tref'], mishnah['mishnah_mishnah_text'],
                   mishnah['yerushalmi_mishnah_text']).get_row())
    for j in range(1, len(refs_normal)):
        cleaned_mishnah_list.append(MishnahRow(refs_normal[j], '', '', '').get_row())


def handle_overlap(cleaned_mishnah_list, refs_normal, mishnah, mishnah_list, i):
    # Determine, is the overlap with the prev or the next
    prev = mishnah_list[i - 1] if i != 0 else None
    next = mishnah_list[i + 1] if i != len(mishnah_list) - 1 else None
    # if prev, pre-concat to the ranged ref
    if prev['mishnah_tref'] in refs_normal:
        mishnah[
            'yerushalmi_mishnah_text'] = f"{prev['yerushalmi_mishnah_text']} {mishnah['yerushalmi_mishnah_text']}"
        mishnah[
            'talmud_tref'] = f"{prev['talmud_tref']}, {get_numbers_from_yerushalmi_tref(mishnah['talmud_tref'])}"
        cleaned_mishnah_list.remove(prev)  # already was appended

    # if next, concat to the ranged ref
    if next['mishnah_tref'] in refs_normal:
        mishnah['yerushalmi_mishnah_text'] += f" {next['yerushalmi_mishnah_text']}"
        mishnah['talmud_tref'] += f", {get_numbers_from_yerushalmi_tref(next['talmud_tref'])}"
        mishnah_list.remove(next)

    # only append the ranged ref
    cleaned_mishnah_list.append(mishnah)


def process_ranged_ref(mishnah_list):
    cleaned_mishnah_list = []
    i = 0
    while i < len(mishnah_list):  # changes dynamically with remove()
        mishnah = mishnah_list[i]
        if Ref(mishnah['mishnah_tref']).is_range():
            refs_normal = create_normalized_ref_list(mishnah)
            is_overlapping = check_overlap(refs_normal)

            # In the case of a ranged ref without overlap with other refs
            if not is_overlapping:
                handle_non_overlapping_ranged_ref(cleaned_mishnah_list, refs_normal, mishnah)

            # if it is an overlapping ranged ref
            elif is_overlapping:
                handle_overlap(cleaned_mishnah_list, refs_normal, mishnah, mishnah_list, i)

        # If not a ranged ref
        else:
            cleaned_mishnah_list.append(mishnah)
        i += 1

    return cleaned_mishnah_list


# Todo - processors - part of the manager class
def post_processing_data(mishnah_list):
    print("parsing single refs")
    mishnah_list = handle_duplicated_single_ref(mishnah_list)
    print("parsing ranged refs")
    mishnah_list = process_ranged_ref(mishnah_list)
    return mishnah_list


def generate_linkset_validation_csv():
    mishnah_list = parse_french_mishnah()
    print("parsed mishnah")
    print("beginning to parse the data")
    mishnah_list = post_processing_data(mishnah_list)
    mishnah_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
    generate_csv(mishnah_list, ['mishnah_tref',
                                'talmud_tref',
                                'mishnah_mishnah_text',
                                'yerushalmi_mishnah_text'], 'french_mishnah_list')


if __name__ == "__main__":
    generate_linkset_validation_csv()
