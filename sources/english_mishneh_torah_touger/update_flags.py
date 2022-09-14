import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
from mt_utilities import add_chabad_book_names_alt_titles


def get_priority(book):
    versions = VersionSet({'title': f'{book}', 'language': 'en'})
    max_priority = max(versions, key=lambda v: getattr(v, 'priority', 0))
    touger_priority = getattr(max_priority, 'priority', 0) + 1
    return touger_priority


def get_touger_books():
    books = VersionSet({'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'})
    books = filter(lambda v: v.title, books)
    books = list(books)
    return books


if __name__ == '__main__':

    # If first time running
    add_chabad_book_names_alt_titles

    # Fix version issue
    german_version_query = {'title': 'Mishneh Torah, Forbidden Foods',
                            'versionTitle': 'Jad Haghasakkah, trans. by L. Mandelstamm. St. Petersburg, 1851. Corrected and edited by Igor Itkin - German [de]'}
    priority_flag_correction = {'priority': 0.0}  # Fix string priority and convert to float
    Version().update(german_version_query, priority_flag_correction)

    books = get_touger_books()

    # For all books update version notes with sponsorship
    sponsorship_message_version_notes = """
    <i>Dedicated in memory of Irving Montak, z"l</i><br><br>© Published and Copyright by Moznaim Publications.<br>Must obtain written permission from Moznaim Publications for any commercial use. Any use must cite Copyright by Moznaim Publications. Released into the commons with a CC-BY-NC license.
    """
    for book in books:
        version_query = {'title': f'{book.title}',
                         'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'}
        version_flags = {"versionNotes": sponsorship_message_version_notes}
        Version().update(version_query, version_flags)
        print(f"Sponsorship message changed for {book.title}")

    # Specific updates for Eruvin, Transmission of Oral Law, Positive Mitzvot and Negative Mitzvot:
    for book in ['Mishneh Torah, Eruvin', 'Mishneh Torah, Positive Mitzvot', 'Mishneh Torah, Negative Mitzvot', 'Mishneh Torah, Transmission of the Oral Law']:
        touger_priority = get_priority(book)
        version_query = {'title': f'{book}',
                         'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'}
        version_flags = {"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001020101/NLI",
                         "language": "en",
                         "digitizedBySefaria": False,
                         "license": "CC-BY-NC",
                         "status": "locked",
                         "purchaseInformationImage": "https://storage.googleapis.com/sefaria-physical-editions/touger-mishneh-torah-hilkhot-teshuvah-purchase-img.png",
                         "purchaseInformationURL": "https://moznaim.com/products/mishneh-torah-rambam",
                         "priority": touger_priority
                         }
        Version().update(version_query, version_flags)
        print(f"Updated {book} to priority {touger_priority}")