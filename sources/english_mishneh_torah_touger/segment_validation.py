import django

django.setup()
from sefaria.model import *
from utilities import sefaria_book_names

if __name__ == '__main__':
    alt_version_books = ['Reading the Shema',
                         'Prayer and the Priestly Blessing',
                         'Tefillin, Mezuzah and the Torah Scroll',
                         'Fringes',
                         'Blessings',
                         'Circumcision',
                         'The Order of Prayer']
    for book in sefaria_book_names:
        index = library.get_index(f"Mishneh Torah, {book}")
        en_version_title = "Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007"
        he_version_title = "Torat Emet 363" if book not in alt_version_books else 'Torat Emet 370'
        for section_ref in index.all_section_refs():
            en_text = section_ref.text("en", vtitle=en_version_title).text
            he_text = section_ref.text("he").text

            # filter empty segments
            en_text = list(filter(lambda x: len(x) > 0, en_text))
            he_text = list(filter(lambda x: len(x) > 0, he_text))

            if len(en_text) != len(he_text):
                print(f"{section_ref.normal()} has non-equal he and en: he: {len(he_text)}, en: {len(en_text)}")
