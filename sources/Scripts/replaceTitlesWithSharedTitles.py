import django
django.setup()
from sefaria.model import *
from sources.functions import *

special_book_cases = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Judges"]

def replaceWithSharedTitle(indices, field=""):
    for index in indices:
        nodes = index.nodes.children
        if doReplace(nodes, field):
            index.save()
            print "{} was changed.".format(index)

        if index.get_alt_structures():
            nodes = index.get_alt_struct_nodes("en")
            if doReplace(nodes, field):
                index.save()
                print "{} was changed.".format(index)


def doReplace(nodes, field):
    save = False
    node_count = 0
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
                        save = True
                        print "{} was changed.".format(shared_title)
                        break
            except KeyError:
                continue
        node_count += 1
    return save


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


indices = []
for index in library.all_index_records():
    # print index
    indices.append(index)
replaceWithSharedTitle(indices, "Parasha")
# replaceWithSharedTitle([library.get_index("Yalkut Shimoni on Torah")], "Parasha")