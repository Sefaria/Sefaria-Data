import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import NoVersionFoundError

from tqdm import tqdm
import csv

def is_translation_complete(index, primary_version_title, translation_title):
    segment_refs = index.all_segment_refs()
    for ref in segment_refs:
        primary_segment_text = ref.text(vtitle=primary_version_title).text
        translation_segment_text = ref.text(vtitle=translation_title).text
        if primary_segment_text != "" and (translation_segment_text == '' or not translation_segment_text):
            return False
    return True

def exists_non_english_version(versions):
    if any(version.languageFamilyName == "english" for version in versions):
        return True
    return False

def no_english_version(versions):
    if all(version.languageFamilyName != "english" for version in versions):
        return True
def no_primary_version_in_english(versions):
    if all(not (version.isPrimary and version.languageFamilyName == "english") for version in versions):
        return True
    return False

def is_full_text_available(index: Index):
    all_segment_refs = index.all_segment_refs()
    for segment_ref in all_segment_refs:
        try:
            text = segment_ref.text(language_family_name='english').text
            if bool(len(text) and all(text)):
                continue
            else:
                return False
        except NoVersionFoundError:
            return False
    return True

def get_primary_version_languages(title: str):
    versions = VersionSet({"title": title, "isPrimary": True}).array()
    primary_version_languages = sorted(
        {version.languageFamilyName for version in versions}, reverse=True
    )
    return primary_version_languages
def get_num_of_uncovered_refs(index: Index):
    num_uncovered_refs = 0
    all_segment_refs = index.all_segment_refs()
    for segment_ref in all_segment_refs:
        try:
            text = segment_ref.text(language_family_name='english').text
            if bool(len(text) and all(text)):
                continue
            else:
                num_uncovered_refs += 1
        except NoVersionFoundError:
            return len(all_segment_refs)
    return num_uncovered_refs

def write_language_analytics_to_csv(data, filename="language_analytics.csv"):
    """Writes language analytics data to a CSV file, inferring field names dynamically."""
    if not data:
        print("No data to write.")
        return

    fieldnames = data[0].keys()  # Infer field names from the first dictionary

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

if __name__ == '__main__':

    language_analytics = []
    all_indexes = library.all_index_records()

    for index in tqdm(all_indexes, desc="Processing indexes"):
        title = index.title
        num_of_uncovered_refs = get_num_of_uncovered_refs(index)
        primary_languages = get_primary_version_languages(title)
        language_analytics.append({
            "title": title,
            "num_uncovered_segments": num_of_uncovered_refs,
            "primary_languages": primary_languages
        })

    write_language_analytics_to_csv(language_analytics)

    # index = library.get_index("Genesis")
    print("hi")

