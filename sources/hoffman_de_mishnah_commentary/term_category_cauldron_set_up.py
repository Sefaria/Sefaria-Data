# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *


def create_term_and_category():
    # Create Term, if it doesn't yet exist
    ts = TermSet({'name': 'German Commentary'})
    if ts.count() == 0:
        t = Term()
        t.name = "German Commentary"
        t.add_primary_titles("German Commentary", "פירוש גרמני")
        t.save()

    # Create a Category, if it doesn't yet exist
    cs = CategorySet({'sharedTitle': 'German Commentary'})
    if cs.count() == 0:
        c = Category()
        c.path = ["Mishnah", "Modern Commentary on Mishnah", "German Commentary"]
        c.add_shared_term("German Commentary")
        c.save()

if __name__ == '__main__':
    create_term_and_category()