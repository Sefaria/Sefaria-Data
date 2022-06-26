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
        self.yerushalmi_french_text = ""

    def __str__(self):
        return f"Mishnah Tref: {self.mishnah_tref}, " \
               f"Talmud Tref: {self.talmud_tref}, " \
               f"Mishnah Mishnah Text: {self.mishnah_mishnah_text}, " \
               f"Yerushalmi Mishnah Text: {self.yerushalmi_mishnah_text}," \
               f"French Yerushalmi Mishnah Text: {self.yerushalmi_french_text}"

    def get_row(self):
        """
        Returns a dictionary representation of the Row object
        """
        return {
            "mishnah_tref": self.mishnah_tref,
            "talmud_tref": self.talmud_tref,
            "mishnah_mishnah_text": self.mishnah_mishnah_text,
            "yerushalmi_mishnah_text": self.yerushalmi_mishnah_text,
            "yerushalmi_french_text": self.yerushalmi_french_text
        }

    # template for new init minus french mishna
    def get_template_row(self):
        """
        In certain cases, we need to copy the row to a new init
        without the French Mishnah field. This function returns a dictionary
        representation of the object for all fields but French Mishnah.
        """
        return {
            "mishnah_tref": self.mishnah_tref,
            "talmud_tref": self.talmud_tref,
            "mishnah_mishnah_text": self.mishnah_mishnah_text,
            "yerushalmi_mishnah_text": self.yerushalmi_mishnah_text}

    def add_french_text(self, text):
        """
        Simple mutator to modify the French Text field
        :param text: String
        """
        self.yerushalmi_french_text = text


class FrenchMishnahManager:

    def __init__(self):
        self.mishnah_list = []
        self.cleaned_mishnah_list = []  # for processing
        self.ym_list = []  # list of Yerushalmi mishnahs

    def run(self):
        """
        Runner function which orchestrates all of the processes for the
        complete French Mishnah Parse.
        The steps are as follows:
        1. Parse French Mishnah - collect the refs based on the linkset
        2. Post Processing Data - clean up the data for manual work
            a. Single refs
            b. Ranged refs
        3. Add French Text - add the French Text to the cleaned refs
        4. Sort the data according to Mishnah Tref
        5. Generate a CSV
        """
        print("Parsing French Mishnah")
        self.parse_french_mishnah()
        print("Post Processing the Data")
        self.post_processing_data()
        print("Adding french text")
        self.mishnah_list = self.add_french_text()
        print("Sorting the Data")
        self.mishnah_list.sort(key=lambda x: Ref(x.mishnah_tref).order_id())
        print("Writing to a CSV")
        self.generate_csv()

    def parse_french_mishnah(self):
        """
        Collects the initial data based on the linkset
        """
        ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})

        for link in ls:
            refs = link.refs
            mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
            mm_text = get_hebrew_text(Ref(mishnah_ref), type="mishnah-mishnah")
            ym_text = get_hebrew_text(Ref(talmud_ref), type="yerushalmi-mishnah")
            self.mishnah_list.append(MishnahRow(mishnah_ref, talmud_ref, mm_text, ym_text))

    def post_processing_data(self):
        """
        Handles the post processing of the data, calls the functions
        which handle the single, then the ranged refs.
        """
        self.mishnah_list = handle_duplicated_single_ref(self.mishnah_list)
        self.mishnah_list = process_ranged_ref(self.mishnah_list)

    def add_french_text(self):
        """
        Iterates through mishnah_list, and for each MishnahRow adds the
        appropriate French text according to the processed Talmud Ref

        Three main cases:
        1. No talmud ref - keep the French Text blank
        2. Multiple talmud refs separated by commas - build a concatenation of the French text for
                                                      each of those refs and append to the Mishnah Row
        3. One talmud ref - Add the French Text

        Since we were having some referencing issues, we copy the existing Mishnah Row object,
        edit the copy, and then overwrite the new object with a new Mishnah List of the
        copied and edited objects.
        """
        list_with_french_text = []
        for mishnah in self.mishnah_list:
            if mishnah.talmud_tref == "":
                mishnah_dict = mishnah.get_template_row()
                mishnah_copy = MishnahRow(**mishnah_dict)
                mishnah_copy.add_french_text("")
                list_with_french_text.append(mishnah_copy)
            elif ", " in mishnah.talmud_tref:  # multiple refs
                tref_prefix = re.findall(r"(Jerusalem Talmud [A-Za-z ]*)\s", mishnah.talmud_tref)[0]
                concat_text = ""
                trefs = mishnah.talmud_tref.split(", ")
                for i in range(len(trefs)):
                    french_text = get_french_text(Ref(trefs[i])) if i == 0 else get_french_text(
                        Ref(f"{tref_prefix} {trefs[i]}"))
                    concat_text += f" {french_text}"
                    print(f"french text for {mishnah.talmud_tref} is {concat_text}")
                mishnah_dict = mishnah.get_template_row()
                mishnah_copy = MishnahRow(**mishnah_dict)
                mishnah_copy.add_french_text(concat_text)
                list_with_french_text.append(mishnah_copy)
            else:
                french_text = get_french_text(Ref(mishnah.talmud_tref))
                print(f"french text for {mishnah.talmud_tref} is {french_text}")
                mishnah_dict = mishnah.get_template_row()
                mishnah_copy = MishnahRow(**mishnah_dict)
                mishnah_copy.add_french_text(french_text)
                list_with_french_text.append(mishnah_copy)
        print(list_with_french_text)
        return list_with_french_text

    def generate_csv(self):
        """
        Generates a CSV based on a list of dictionaries containing the data
        """
        dict_list = []
        for mishnah in self.mishnah_list:
            dict_list.append(mishnah.get_row())
        headers = ['mishnah_tref',
                   'talmud_tref',
                   'mishnah_mishnah_text',
                   'yerushalmi_mishnah_text',
                   'yerushalmi_french_text']
        with open('french_mishnah.csv', 'w+') as file:
            c = csv.DictWriter(file, fieldnames=headers)
            c.writeheader()
            c.writerows(dict_list)
        print(f"File writing of french mishnah complete")


# # # # # Post-Processing Utility Functions # # # # #
def get_yerushalmi_linkset_mishnahs():
    """
    Generates a list of Mishnah Trefs linked to Yerushalmi segments
    :returns ym_list: list of Strings of Mishnah Trefs
    """
    ym_list = []
    ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})
    for link in ls:
        refs = link.refs
        mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
        ym_list.append(mishnah_ref)
    return ym_list


def create_normalized_ref_list(mishnah):
    """
    Given a ranged mishnah Ref, create a list
    of the normalized trefs (i.e. Berakhot 2:1-3 becomes ['Berakhot 2:1', 'Berakhot 2:2', 'Berakhot 2:3'])
    :param mishnah: ranged Mishnah Ref object
    :returns refs_normal: List of Strings, normalized refs
    """
    refs = Ref(mishnah.mishnah_tref).range_list()
    refs_normal = []
    for ref in refs:
        refs_normal.append(ref.normal())
    return refs_normal


def check_overlap(refs_normal):
    """
    For a ranged ref, checks if any of the component Mishnahs exist somewhere else in the linkset
    i.e. if we had "Mishnah Berakhot 1:1, Mishnah Berakhot 1:2-3, Mishnah Berakhot 1:3" in our linkset,
    we'd identify that Mishnah Berakhot 1:3 is an "overlapping" ref with two talmud segments associated with it
    which is critical for the post processing

    :param refs_normal: List of normalized mishnah trefs creating a ranged Ref
    :returns is_overlapping: Boolean if the ranged ref represented by refs_normal is considered overlapping
    """
    ym_list = get_yerushalmi_linkset_mishnahs()
    is_overlapping = False
    for each_ref in refs_normal:
        if each_ref in ym_list:
            is_overlapping = True
    return is_overlapping


# Given a tref, where the prev tref is the same
# Concatenate this yerushalmi mishnah text to the prev
# Delete this row
def handle_duplicated_single_ref(mishnah_list):
    cleaned_mishnah_list = [mishnah_list[0]]

    for i in range(1, len(mishnah_list) - 1):

        prev = mishnah_list[i - 1]
        cur = mishnah_list[i]
        next = mishnah_list[i + 1]

        # If there's a case of a repeated tref, concatenate the text
        # and eliminate the redundancy.
        if cur.mishnah_tref == prev.mishnah_tref:
            prev.yerushalmi_mishnah_text += f" {cur.yerushalmi_mishnah_text}"
            prev.talmud_tref += f", {get_numbers_from_yerushalmi_tref(cur.talmud_tref)}"
            cleaned_mishnah_list.append(prev)
        elif cur.mishnah_tref != next.mishnah_tref:  # avoid double counting bug
            cleaned_mishnah_list.append(cur)
    return cleaned_mishnah_list


def split_ranged_refs(cleaned_mishnah_list, refs_normal, mishnah):
    cleaned_mishnah_list.append(
        MishnahRow(refs_normal[0],
                   mishnah.talmud_tref,
                   get_hebrew_text(Ref(refs_normal[0]), type="mishnah-mishnah"),
                   mishnah.yerushalmi_mishnah_text
                   ))
    for j in range(1, len(refs_normal)):
        cur_mishnah_ref = refs_normal[j]
        he_mishnah_mishnah_text = get_hebrew_text(Ref(cur_mishnah_ref), type="mishnah-mishnah")
        cleaned_mishnah_list.append(MishnahRow(cur_mishnah_ref, '', he_mishnah_mishnah_text, ''))


def handle_overlap(cleaned_mishnah_list, refs_normal, mishnah, mishnah_list, i):
    # Determine, is the overlap with the prev or the next
    prev = mishnah_list[i - 1] if i != 0 else None
    next = mishnah_list[i + 1] if i != len(mishnah_list) - 1 else None
    # if prev, pre-concat to the ranged ref
    if prev.mishnah_tref in refs_normal:
        mishnah.yerushalmi_mishnah_text = f"{prev.yerushalmi_mishnah_text} {mishnah.yerushalmi_mishnah_text}"
        mishnah.talmud_tref = f"{prev.talmud_tref}, {get_numbers_from_yerushalmi_tref(mishnah.talmud_tref)}"
        cleaned_mishnah_list.remove(prev)  # already was appended

    # if next, concat to the ranged ref
    if next.mishnah_tref in refs_normal:
        mishnah.yerushalmi_mishnah_text += f" {next.yerushalmi_mishnah_text}"
        mishnah.talmud_tref += f", {get_numbers_from_yerushalmi_tref(next.talmud_tref)}"
        mishnah_list.remove(next)

    # flatten out the concatenated ranged ref
    split_ranged_refs(cleaned_mishnah_list, refs_normal, mishnah)


def process_ranged_ref(mishnah_list):
    cleaned_mishnah_list = []
    i = 0
    while i < len(mishnah_list):  # changes dynamically with remove()
        mishnah = mishnah_list[i]
        if Ref(mishnah.mishnah_tref).is_range():
            refs_normal = create_normalized_ref_list(mishnah)
            is_overlapping = check_overlap(refs_normal)

            # In the case of a ranged ref without overlap with other refs
            if not is_overlapping:
                split_ranged_refs(cleaned_mishnah_list, refs_normal, mishnah)

            # if it is an overlapping ranged ref
            elif is_overlapping:
                handle_overlap(cleaned_mishnah_list, refs_normal, mishnah, mishnah_list, i)



        # If not a ranged ref
        else:
            cleaned_mishnah_list.append(mishnah)
        i += 1

    return cleaned_mishnah_list


# # # # General Utility Functions # # # #
def create_normalized_ref_list(mishnah):
    refs = Ref(mishnah.mishnah_tref).range_list()
    refs_normal = []
    for ref in refs:
        refs_normal.append(ref.normal())
    return refs_normal


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


if __name__ == "__main__":
    manager = FrenchMishnahManager()
    manager.run()
