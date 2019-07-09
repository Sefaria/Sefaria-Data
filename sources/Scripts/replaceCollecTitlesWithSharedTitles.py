# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from replaceTitlesWithSharedTitles import *
import codecs

# iterate through indices and check if (1) the title contains the word "on" and (2) the index has the category "Commentary"
def makeCollectiveTitleShared(indices):
    addNewTerms()
    specialCases()
    for index in indices:
        if "on" in index.get_title():
            if "Commentary" in index.categories:
                try:  #check if index already uses collective title
                    index.collective_title
                except AttributeError:
                    category_index = index.categories.index("Commentary") + 1
                    new_collect_title = index.get_title().split("on")[0].strip()
                    if not Term().load_by_title(new_collect_title):  # check if assumed collective title is actually a term
                        try:  # use backup method of checking other indices under same category
                            new_collect_title = getByCategory(index.categories[category_index])
                        except IndexError:
                            print "A collective title could not be found for the index : {}".format(index)
                    assert Term().load_by_title(new_collect_title)
                    index.collective_title = Term().load_by_title(new_collect_title).get_primary_title()  # doesn't always match with index title
                    index.save()
                    print "The collective title <{}> was added to the index <{}>.".format(index.collective_title, index.get_title())

# add new terms for the collective titles
def addNewTerms():
    add_term("Midrash Shmuel", u"מדרש שמואל")
    add_term("Immanuel of Rome", u"עמנואל הרומי")
    add_term("Haflaah", u"הפלאה")
    add_term("Revealment and Concealment in Language", u"גילוי וכיסוי בלשון")
    add_term("Beit HaLevi", u"בית הלוי")
    add_term("Riva", u"ריב\"א")

# special cases of indices that need specific attention
def specialCases():
    index1 = library.get_index("Commentaries on Revealment and Concealment in Language")
    index1.collective_title = "Revealment and Concealment in Language"
    index1.save
    term1 = Term().load_by_title(u"ברוך שאמר")
    term1.add_title("Barukh She'amar", "en")
    term1.save()

# DOESN'T ALWAYS HOLD TRUE (I.E. MIDRASH LEKACH TOV)
def getByCategory(category):
    for ind in library.all_index_records():
        if category in ind.categories:
            try:
                return ind.collective_title
            except AttributeError:
                None
