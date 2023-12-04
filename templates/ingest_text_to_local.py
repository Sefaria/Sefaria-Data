import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sources.functions import post_text

# Make sure in your Sefaria-Data/sources/ directory you create a local_settings file.
# There, you can list your SEFARIA_SERVER and API_KEY variables.
from sources.local_settings import SEFARIA_SERVER


def create_mappings():
    """
    This function takes a CSV of text organized by "ref" and "text" (assuming the text has already been processed
    to Sefaria-specific standards), and ingests it as a defaultdict, organized by index, and within that by
    textual reference (tref), with the text of the specific segment as the value.
    :return mappings:
    """
    mappings = defaultdict(dict)
    with open("my_sample_commentary_text.csv", 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            tref = row['ref']
            text = row['text']
            mappings[Ref(tref).index.title][tref] = text

    return mappings


def generate_text_post_format(text=""):
    """
    To use post_text() to post to the Sefaria API, the text must be in the format returned by this function.
    NOTE: The "text" value will be wrapped in a list, depending on how you are posting.
    If you are posting segment-by-segment, as we are in this case, the text is not wrapped by a list.
    If you are posting at an index level, the number of lists wrapping the text should match the depth of the text, with the
    outer-most bracket representing the index level.
    so for example:
        a) A text of depth-3, like a commentary:
                             [
                               [
                                 ["chapter 1, segment 1, comment 1", "chapter 1, segment 1, comment 2", "chapter 1, segment 1, comment 3],
                                 ["chapter 1, segment 2, comment 1", "chapter 1, segment 2, comment 2", "chapter 1, segment 2, comment 3]
                               ],
                               [
                                 ["chapter 2, segment 1, comment 1", "chapter 2, segment 1, comment 2", "chapter 2, segment 1, comment 3],
                                 ["chapter 2, segment 2, comment 1", "chapter 2, segment 2, comment 2", "chapter 2, segment 2, comment 3]
                               ]
                            ]
       b) A text of depth-2, like a book of Tanach:
                               [
                                 ["chapter 1, segment 1", "chapter 1, segment 2", "chapter 1, segment 3],
                                 ["chapter 2, segment 2", "chapter 2, segment 2", "chapter 2, segment 2]
                               ]
    :param text: The actual text to be posted
    :return: A formatted dictionary for posting the text, adhering to the Sefaria-specific post_text() standards.
    """
    return {
        "text": text,
        "versionTitle": "My Sample Commentary - Dummy Data for Templating Purposes",
        "versionSource": "www.mysamplecommentary.data",
        "versionNotes": "Notes, or a dedication would go here",
        "language": "en"
    }


def upload_text(mappings):
    """
   This function takes the `mappings` defaultdict, and posts each textual reference (tref) and text value
   to the Sefaria server using post_text(), a function that wraps the Sefaria API call to api/v2/raw/index/.
   :param mappings: The default dict with the index, tref, and text
   :return: None
    """

    # For each Index, and corresponding dictionary in mappings
    for book, book_map in mappings.items():

        # Print the name of the current index. post_text() can take a while, so this
        # is useful for tracking purposes.
        print(f"Uploading text for {book}")

        # For each textual reference (tref) in the book_map
        for tref in book_map:
            # Generate the proper text format for post_text()
            formatted_text = generate_text_post_format(book_map[tref])
            # Using that format, post the text using post_text()
            post_text(ref=tref, text=formatted_text, server=SEFARIA_SERVER)


if __name__ == '__main__':

    # Step One: Create mappings
    mapper = create_mappings()
    print("UPDATE: Text map generated")

    # Step Two: Upload the text
    upload_text(mapper)
    print("UPDATE: Text ingest complete")