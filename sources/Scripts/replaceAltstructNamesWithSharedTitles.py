# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from replaceTitlesWithSharedTitles import *
import codecs

# special cases in which the name of the altstruct is wrong
replacement_terms = {"Subject":"Topic", "Titles":"Topic", "Title":"Topic", "Books":"Book", "By Parasha":"Parasha", "Simanim":"Siman",
                     "Shaar":"Gate", "Pillars":"Amudim", "Amudim and Vavim":"Amudim", "30 Day Cycle":"Monthly Cycle"}

# iterated through the nodes for each index and replace the altstruct name with the shared title
def replaceAltstructWithSharedTitle(indices):
    addNewTerms()
    for index in indices:
        save = False
        for name, node in index.struct_objs.items():
            if not library.get_term(name):
                shared_title = Term().load_by_title(name)
                if shared_title:
                    index.struct_objs[shared_title.get_primary_title()] = index.struct_objs.pop(name)
                    save = True
                    print "{} was changed.".format(name)
                elif name in replacement_terms.keys():
                    index.struct_objs[replacement_terms.get(name)] = index.struct_objs.pop(name)
                    save = True
                    print "{} was changed.".format(name)
                else:
                    print "There was no term for the altstruct name, {}, of {}.".format(name, index)
        if save:
            index.save()
            print "{} was changed.".format(index)

# terms for altstructs that need to be added
def addNewTerms():
    add_term("Index", u"מפתחות")
    add_term("Amudim", u"עמודים")
    add_term("Monthly Cycle", u"לוח חודשי")

