# TODO - Write validation code here
# - Check same number of <sup>s as segments per mishnah

import django

django.setup()

from sefaria.model import *
import re

mishnah_text = {}
num_commentaries = {}
bold_text = {}


def retrieve_mishnah_action(segment_str, tref, he_tref, version):
    global mishnah_text
    mishnah_text[tref] = segment_str


def retrieve_comm_action(segment_str, tref, he_tref, version):
    global num_commentaries
    mishnah_key = re.findall(r"German Commentary on (.*?\d{1,2}:\d{1,2}):\d{1,2}", tref)
    mishnah_key = mishnah_key[0] if mishnah_key else "No commentary"

    if mishnah_key in num_commentaries:
        num_commentaries[mishnah_key] += 1
    else:
        num_commentaries[mishnah_key] = 1


# A check for bolded text that is just a comma or a period
def retrieve_bold_action(segment_str, tref, he_tref, version):
    global bold_text

    bold_dh = re.findall(r"<b>(.*?)</b>", segment_str)
    bold_text[tref] = bold_dh[0] if bold_dh else ""


def retrieve_version_text():
    version_query = {"versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
                     "title": {"$regex": "^Mishnah"}}
    mishnah_version = VersionSet(version_query)
    for v in mishnah_version:
        v.walk_thru_contents(retrieve_mishnah_action)

    version_query["title"] = {"$regex": "^German"}
    comm_version = VersionSet(version_query)
    for v in comm_version:
        v.walk_thru_contents(retrieve_comm_action)
        v.walk_thru_contents(retrieve_bold_action)


def contains_punct(text):
    text = text[:-1]
    return re.match(r"[,.?'\"!]", text)


def count_validator():
    # For each mishnah
    # Check with count of commentary segments for that Mishnah
    more_ftn_errors = 0
    more_ftn_mishnahs = []
    more_cmmt_errors = 0
    more_cmmt_mishnahs = []
    for m in mishnah_text:
        text = mishnah_text[m]
        footnote_sups = re.findall(r"<sup class=\"footnote-marker\">.*?</sup><i class=\"footnote\">", text)
        num_sups = len(footnote_sups)
        if m in num_commentaries:
            if num_sups != num_commentaries[m]:
                if num_sups > num_commentaries[m]:
                    print(f"ERROR - MORE FTNS: {m} - {num_sups} footnotes | {num_commentaries[m]} commentaries")
                    more_ftn_errors += 1
                    more_ftn_mishnahs.append(m)
                else:
                    print(f"ERROR - MORE COMMENTS: {m} - {num_sups} footnotes | {num_commentaries[m]} commentaries")
                    more_cmmt_errors += 1
                    more_cmmt_mishnahs.append(m)
    print(f"TOTAL: {more_ftn_errors} Mishnayot had more footnotes\n{more_cmmt_errors} Mishnayot had more comments")
    print(f"More Footnote Mishnahs: {more_ftn_mishnahs}")
    print(f"\nMore Commentary Mishnahs: {more_cmmt_mishnahs}")
    print(f"Makkot 1:5 is supposed to throw an error based on its odd nested footnote structure.")


def dh_validator():
    bad_dhs = []
    num_mishnahs = 0
    for tref in bold_text:
        num_mishnahs += 1
        dh = bold_text[tref]
        # Too short
        if "Introduction" not in tref and bold_text[tref] != "" and len(dh) < 3 and not dh.isalpha():
            print(f"{tref}: {bold_text[tref]}")
            bad_dhs.append(tref)
        # Too long
        if "Introduction" not in tref and bold_text[tref] != "" and len(dh) > 50 and contains_punct(dh):
            print(f"{tref}: {bold_text[tref]}")
            bad_dhs.append(tref)
    print(len(bad_dhs))
    print(f"Total commentaries {num_mishnahs}")
    print(f"Disregard errors in Mishnah Oktzin 1:2")
    print(f"Percent of unvalidated mishnahs: {len(bad_dhs)/num_mishnahs}")


if __name__ == '__main__':
    retrieve_version_text()
    count_validator()
    dh_validator()
