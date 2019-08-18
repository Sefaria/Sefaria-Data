import django
django.setup()
from sefaria.model import *
from sources.functions import *
from sefaria.helper import schema

special_book_cases = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Judges"]

def replaceTitleWithSharedTitle(indices, limiter=""):
    iterateNodes(indices, doReplace, limiter)

# iterate through the nodes of the indices and call the replacer function
def iterateNodes(indices, replacer, limiter=""):
    for index in indices:
        # replace default nodes
        nodes = index.nodes.all_children()
        if replacer(nodes, limiter):
            index.save()
            print "{} was changed.".format(index)

        # replace alt struct nodes
        if index.get_alt_structures():
            nodes = index.get_alt_struct_nodes()
            if replacer(nodes, limiter):
                index.save()
                print "{} was changed.".format(index)

# replacer function
def doReplace(nodes, limiter):
    save = False
    for node in nodes:
        if node.get_primary_title() in special_book_cases:
            continue
        if not vars(node)["sharedTitle"]:  # if node doesn't already have a shared title
            try:
                titles = node.get_titles()
                for title in titles:  # iterate through titles until a potential shared title is found
                    shared_title = checkTerm(title, limiter)
                    if shared_title:
                        node.add_shared_term(shared_title)
                        save = True
                        print "{} was changed.".format(shared_title)
                        break
            except KeyError:  # if there is no "scheme" field in the term of checkTerm()
                continue
    return save

# check if the given title is a term
# PARAM: limiter - checks if the term must also adhere to the given property (in this case, it can only be a parasha)
def checkTerm(title, limiter=None):
    term = Term().load_by_title(title)
    if limiter == "Parasha":
        if term:
            if "scheme" in vars(term).keys():
                if vars(term)["scheme"] == limiter:
                    return term.get_primary_title()
    else:
        if term:
            return term.get_primary_title()

if __name__ == "__main__":
    indices = library.all_index_records()
    replaceTitleWithSharedTitle(indices, limiter="Parasha")