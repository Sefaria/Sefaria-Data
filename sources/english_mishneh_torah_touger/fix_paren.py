import django

django.setup()

import csv
import re

from sefaria.model import *
from sefaria.tracker import modify_text

from post_processing import setup_data, create_book_name_map, rename_refs_to_sefaria
from mt_utilities import sefaria_book_names


def get_chabad_text_map():
    # Old text map
    text_map = {}
    chabad_book_names, mishneh_torah_list = setup_data()
    name_map = create_book_name_map(chabad_book_names, sefaria_book_names)
    mishneh_torah_list = rename_refs_to_sefaria(mishneh_torah_list, name_map)

    for halakha in mishneh_torah_list:
        ref = halakha['ref']
        text = halakha['text']
        text_map[ref] = text
    return text_map


def find_bad_links(link_patt, text, boolean_res=False):
    bad_links = re.findall(link_patt, text)
    if boolean_res:
        return len(bad_links) > 0
    else:
        return bad_links


def fix_bad_links(ref, text, link_patt, text_map):
    # Find bad link
    bad_links = find_bad_links(link_patt, text)
    for i in range(len(bad_links)):
        bad_link = bad_links[i]
        original_text = text_map[ref]
        # Search old text for proper citation
        sefer_name = re.findall(r"\(([a-zA-z ]{1,20}) .*\)", bad_link)[0]
        link_finder_str = "\(<a href=\".*?\">("+ sefer_name +" .*?)\)"
        link_finder_patt = re.compile(link_finder_str)
        correct_link = re.findall(link_finder_patt, original_text)[0]
        correct_link = re.sub(r"</a>", "", correct_link)
        correct_link = f"({correct_link})"
        # print(f"Fixing {ref}, {bad_link} >>> {correct_link}")

        # Substitute
        new_text = text.replace(bad_link, correct_link, 1)
        text = new_text  # if not last
    return new_text


def fix_multi_links(ref, text, link_patt):
    link_map = {
        "(Leviticus 18:1), 20:14)": "(Leviticus 18:1, 20:14)",
        "(II Kings 2:4, 4:30), 4:30)": "(II Kings 2:4, 4:30)",
        "(Exodus 30:2), 35:16)": "(Exodus 30:28, 35:16)",
        "(Leviticus 16:2); 4:15)": "(Leviticus 16:21; 4:15)",
        "(Exodus 12:4), 9)": "(Exodus 12:46, 9)"
    }

    # Find bad multi-links and remap
    bad_multi_links = find_bad_links(link_patt, text)
    for bad_link in bad_multi_links:
        correct_link = link_map[bad_link]
        new_text = text.replace(bad_link, correct_link, 1)
        return new_text



def fix_long_multi_links(ref, text, link_patt):
    link_map = {
        "(Isaiah 10:3)-4, 11:1-16, 12:1-6)": "(Isaiah 10:32-4, 11:1-16, 12:1-6)",
        "(Exodus 32:1)-14, 34:1-10)": "(Exodus 32:11-14, 34:1-10)",
        "(II Kings 11:1)-20, 12:1-17)": "(II Kings 11:17-20, 12:1-17)",
        "(Ezekiel 45:1)-25, 46:1-18)": "(Ezekiel 45:16-25, 46:1-18)"
    }

    # Find bad long multi-links and remap
    bad_multi_links = find_bad_links(link_patt, text)
    for i in range(len(bad_multi_links)):
        bad_link = bad_multi_links[i]
        correct_link = link_map[bad_link]
        new_text = text.replace(bad_link, correct_link, 1)
        text = new_text
    return new_text


def generate_fixes():
    mt_fixes = []
    chabad_text_map = get_chabad_text_map()
    with open('mishneh_torah_data_non_manual_cleaned.csv', newline='') as f:
        reader = csv.reader(f)
        for line in reader:
            ref = line[0]
            text = line[1]

            # Find bad links that were corrupted
            single_link_patt = r"(\(.{1,20}:\d*?\)-.{1,5}\))"
            has_bad_links = find_bad_links(link_patt=single_link_patt, text=text, boolean_res=True)
            if has_bad_links:
                text = fix_bad_links(ref=ref, text=text, link_patt=single_link_patt, text_map=chabad_text_map)

            single_link_patt = r"(\([A-Za-z ]* \d{1,3}:\))"
            has_bad_links = find_bad_links(link_patt=single_link_patt, text=text, boolean_res=True)
            if has_bad_links:
                text = fix_bad_links(ref=ref, text=text, link_patt=single_link_patt, text_map=chabad_text_map)

            multi_link_patt = link_patt = r"(\(.{1,20}\d{1,3}:\d*\)[,;] \d{1,3}.*?\))"
            has_bad_multi_links = find_bad_links(link_patt=multi_link_patt, text=text, boolean_res=True)
            if has_bad_multi_links:
                text = fix_multi_links(ref, text, link_patt)

            multi_long_link_patt = link_patt = r"(\(.{1,20}\d{1,3}:\d*\)[,; -][\d -:,]{10,20}\))"
            has_bad_long_multi_links = find_bad_links(link_patt=multi_long_link_patt, text=text,
                                                             boolean_res=True)
            if has_bad_long_multi_links:
                text = fix_long_multi_links(ref, text, link_patt)

            mt_fixes.append({'ref': ref, 'text': text})

    return mt_fixes


def validate():
    mt_fixes = generate_fixes()
    for halakha in mt_fixes:
        ref = halakha['ref']
        text = halakha['text']
        uncaught_links = re.findall(r"\([^)]+\)[^(]{1,30}\)", text)
        for link in uncaught_links:
            print(f"ERROR: {ref} - uncaught: {link}")
        uncaught_small_links = re.findall(r"(\([A-Za-z ]* \d{1,3}:\))", text)
        for link in uncaught_small_links:
            print(f"ERROR: {ref} - uncaught: {link}")



def unlock_all():
    rambam_vs = VersionSet(
        {'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'})
    for version in rambam_vs:
        version.status = ''
        version.save()


def lock_all():
    rambam_vs = VersionSet(
        {'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'})
    for version in rambam_vs:
        version.status = 'locked'
        version.save()


def ingest_fixes(ref, new_text):
    oref = Ref(f"Mishneh Torah, {ref}")
    modify_text(user=142625,
                oref=oref,
                vtitle="Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007",
                lang="en",
                text=new_text)
    # print(f"Saved new text for {ref}")


def run_ingest_fixes():
    mt_fixes = generate_fixes()
    unlock_all()
    for halakha in mt_fixes:
        ref = halakha['ref']
        text = halakha['text']
        ingest_fixes(ref, text)
    lock_all()


if __name__ == '__main__':
    # validate()
    run_ingest_fixes()
