#encoding=utf-8

import django
django.setup()

from sefaria.model import *
from sources.functions import add_term
from sources.local_settings import *


def collective_title(index_name, collective_title_term):
    ind = library.get_index(index_name)
    t = term_check(collective_title_term)
    if not t:
        return
    ind.collective_title = t.get_primary_title('en')
    ind.save()


def term_check(term):
    t = Term().load_by_title(term)
    if not t:
        if type(term) == dict:
            add_term(term['en'], term['he'], server=SEFARIA_SERVER)
        else:
            print u"Please privide a term dict {'en': <english term spelling>, 'he': <hebrew term spelling>} as the collective_title_term"
            return False
    return t


if __name__ == "__main__":
    collective_title(u'ספרי במדבר', u'Sifrei')
    collective_title(u'ספרי דברים', u'Sifrei')
    collective_title(u'ילקוט שמעוני על נ"ך', u'ילקוט שמעוני')
    collective_title(u'ילקוט שמעוני על התורה', u'ילקוט שמעוני')