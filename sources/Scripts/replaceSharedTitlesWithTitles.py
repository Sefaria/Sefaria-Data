import django
django.setup()
from sefaria.model import *
from sources.functions import *
from replaceTitlesWithSharedTitles import *

# remove term usage and replace with a separate instance of the term's title group
def replaceAndRemoveTerm(indices, term):
    if not checkTerm(term):
        print "{} is not a term.".format(term)
        return
    iterateNodes(indices, replaceTerms, term)

# replacer function
def replaceTerms(nodes, term):
    save = False
    for node in nodes:
        if node.remove_shared_term(term):
            save = True
            print "{} was changed.".format(term)
    return save
