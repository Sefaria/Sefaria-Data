import django
import re
django.setup()
from sefaria.model import *

list_of_jewish_bible_books = [
    # # Torah (Five Books of Moses)
    # "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",

    # Nevi'im (Prophets)
    "Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings", "Isaiah", "Jeremiah", "Ezekiel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum",
    "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    # Ketuvim (Writings)
    "Psalms", "Proverbs", "Job",
    "Song of Songs", "Ruth", "Lamentations", "Ecclesiastes", "Esther",
    "Daniel", "Ezra", "Nehemiah", "I Chronicles", "II Chronicles"
]

def extract_biblical_reference_and_title(line):
    match = re.match(r"\(([^)]+)\)<br><b>([^<]+)</b>", line)
    if match:
        biblical_reference = match.group(1).strip()
        title = match.group(2).strip()
        return biblical_reference, title
    return None, None

if __name__ == '__main__':
    print("hi")
    passage_breakups = []
    for book in list_of_jewish_bible_books:
        passage_refs = Ref(f"Steinsaltz Introductions to Tanakh, {book}, Section Preface").all_segment_refs()
        for passage_ref in passage_refs:
            text = passage_ref.text('en').text
            ref, title = extract_biblical_reference_and_title(text)
            passage_breakups.append((ref, title))
            print(f"{ref}, {title}")
    for ref, title in passage_breakups:
        Passage({
            "full_ref": ref,
            "type": "passage",
            "source": "Steinsaltz",
        }).save()
