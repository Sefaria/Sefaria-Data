#encoding=utf-8

import django
django.setup()

from sources.functions import *
from sefaria.model import *

SERVER = 'current server'


def create_commentary_LT_category():
    c = Category()
    c.add_primary_titles('Commentary', u'מפרשים')
    c.path = [u'Midrash', u'Aggadic Midrash', u'Midrash Lekach Tov', u'Commentary']
    c.save()
    return c


def add_collective_titles_terms():
    add_term('Notes and Corrections', u'הערות ותיקונים')
    add_term("Beur HaRe'em", u'באור הרא"ם')

def change_i_tags(ind):
    Ref(ind.title).text('he').text


if __name__ == "__main__":
    c = create_commentary_LT_category()
    add_collective_titles_terms()
    import re
    for book in ["Beur HaRe'em on Midrash Lekach Tov", "Notes and Corrections on Midrash Lekach Tov", "Notes and Corrections on Midrash Lekach Tov on Esther"]:
        ind = library.get_index(book)
        ind.collective_title = re.split(u' on', book, 1)[0]
        ind.categories = [u'Midrash', u'Aggadic Midrash', u'Midrash Lekach Tov', u'Commentary']
        ind.save()
