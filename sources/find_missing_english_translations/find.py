import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import NoVersionFoundError

from tqdm import tqdm
import csv
import os
CSV_FILENAME = "language_analytics.csv"
BATCH_SIZE = 10
ERROR_LOG_FILENAME = "error_log.txt"


# def is_full_text_available(index: Index):
#     all_segment_refs = index.all_segment_refs()
#     for segment_ref in all_segment_refs:
#         try:
#             text = segment_ref.text(language_family_name='english').text
#             if bool(len(text) and all(text)):
#                 continue
#             else:
#                 return False
#         except NoVersionFoundError:
#             return False
#     return True
def log_error(title, error_message):
    """Logs errors to a separate file."""
    with open(ERROR_LOG_FILENAME, "a", encoding="utf-8") as f:
        f.write(f"{title}: {error_message}\n")
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

def read_existing_titles():
    """Reads existing titles from the CSV to avoid duplicate entries."""
    if not os.path.exists(CSV_FILENAME):
        return set()

    with open(CSV_FILENAME, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row["title"] for row in reader}


def write_language_analytics_to_csv(data, mode="a"):
    """Writes a batch of language analytics data to the CSV file."""
    file_exists = os.path.exists(CSV_FILENAME)

    with open(CSV_FILENAME, mode, newline='', encoding='utf-8') as f:
        fieldnames = ["title", "primary_category", "num_uncovered_segments", "primary_languages"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or mode == "w":
            writer.writeheader()  # Write header only if the file is new

        writer.writerows(data)

if __name__ == '__main__':
    existing_titles = read_existing_titles()
    language_analytics = []
    all_indexes = library.all_index_records()

    for index in tqdm(all_indexes, desc="Processing indexes"):
        title = index.title
        if title in existing_titles:
            continue  # Skip already processed entries

        try:
            num_of_uncovered_refs = get_num_of_uncovered_refs(index)
        except Exception as e:
            log_error(title, str(e))  # Write error to log file
            continue  # Skip this index and move to the next one
        primary_languages = get_primary_version_languages(title)

        language_analytics.append({
            "title": title,
            "primary_category": index.get_primary_category(),
            "num_uncovered_segments": num_of_uncovered_refs,
            "primary_languages": primary_languages
        })

        # Write in batches
        if len(language_analytics) >= BATCH_SIZE:
            write_language_analytics_to_csv(language_analytics)
            existing_titles.update(entry["title"] for entry in language_analytics)
            language_analytics = []  # Clear batch

    # Write remaining data
    if language_analytics:
        write_language_analytics_to_csv(language_analytics)

