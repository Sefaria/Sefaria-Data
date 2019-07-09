import django
django.setup()
from sefaria.model import *
from sources.functions import *
from sefaria.helper import schema

special_book_cases = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Judges"]

def replaceTitleWithSharedTitle(indices, field=""):
    iterateNodes(indices, doReplace, field)

# iterate through the nodes of the indices and call the replacer function
def iterateNodes(indices, replacer, field=""):
    for index in indices:
        # nodes = index.nodes.children
        nodes = index.nodes.all_children()
        if replacer(nodes, field):
            index.save()
            print "{} was changed.".format(index)

        if index.get_alt_structures():
            nodes = index.get_alt_struct_nodes("en")
            if replacer(nodes, field):
                index.save()
                print "{} was changed.".format(index)

# replacer function
def doReplace(nodes, field):
    save = False
    for node in nodes:
        if node.get_primary_title() in special_book_cases:
            continue
        if not vars(node)["sharedTitle"]:
            try:
                titles = node.get_titles()
                for title in titles:
                    shared_title = checkTerm(title, field)
                    if shared_title:
                        node.add_shared_term(shared_title)
                        # schema.change_node_title(node, title, "en", shared_title, True)
                        save = True
                        print "{} was changed.".format(shared_title)
                        break
            except KeyError:
                continue
    return save

# check if the given title is a term
# PARAM: field - checks if the term must also adhere to the given property (right now can only be a parasha)
def checkTerm(title, field=None):
    term = Term().load_by_title(title)
    if field == "Parasha":
        if term:
            if "scheme" in vars(term).keys():
                if vars(term)["scheme"] == field:
                    return term.get_primary_title()
    else:
        if term:
            return term.get_primary_title()
