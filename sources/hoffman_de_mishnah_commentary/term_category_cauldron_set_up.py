# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sefaria.helper import category


def create_term_and_category():
    # Create Term, if it doesn't yet exist
    ts = TermSet({'name': 'German Commentary'})
    if ts.count() == 0:
        t = Term()
        t.name = "German Commentary"
        t.add_primary_titles("German Commentary", "פירוש גרמני")
        t.save()

    # Create a Category, if it doesn't yet exist
    print("Creating general German Commentary category")
    category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary"])
    print("Creating seder-specific German Commentary category")
    sedarim = ["Seder Zeraim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Kodashim", "Seder Tahorot"]
    for seder in sedarim:
        category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary", seder])


if __name__ == '__main__':
    create_term_and_category()
