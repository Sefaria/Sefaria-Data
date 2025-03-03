import django
import re
from bs4 import BeautifulSoup


django.setup()
from sefaria.model import *

list_of_jewish_bible_books = [
    # # Torah (Five Books of Moses)
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
]

def extract_biblical_reference_and_title(line):
    match = re.match(r"\(([^)]+)\)<br><b>([^<]+)</b>", line)
    if match:
        biblical_reference = match.group(1).strip()
        title = match.group(2).strip()
        return biblical_reference, title
    return None, None

def start_new_chunk(html_text):
    """Check if the given HTML text starts with a title formatted like in the image."""
    soup = BeautifulSoup(html_text, "html.parser")
    first_span = soup.find("span", class_="mediumGrey")
    return first_span is not None and first_span.find("i") is not None


if __name__ == '__main__':
    print("hi")
    passage_breakups = []
    chunk = []
    for book in list_of_jewish_bible_books:
        verses_refs = library.get_index(book).all_segment_refs()
        for i, verse_ref in enumerate(verses_refs):
            verse_text = verse_ref.text(vtitle="The Kehot Chumash; Chabad House Publications, Los Angeles").text

            if i > 0 and start_new_chunk(verse_text):  # If not the first verse and a new chunk starts
                passage_breakups.append(chunk)  # Save the previous chunk
                chunk = []  # Start a new chunk

            chunk.append(verse_ref) # Add verse to the current chunk
            if i == len(verses_refs) - 1:  # If this is the last verse in the book
                passage_breakups.append(chunk)  # Close the final chunk
                chunk = []  # Reset chunk for the next book

        if chunk:  # Append the last chunk after looping
            passage_breakups.append(chunk)
    for chunk in passage_breakups:
        Passage({
            "full_ref": chunk[0].to(chunk[-1]).tref,
            "type": "biblical-story",
            "source": "Kehot Chumash",
        }).save()
