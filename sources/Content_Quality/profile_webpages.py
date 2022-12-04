import cProfile
from sources.functions import *
from sefaria.system.database import ensure_indices, db
from pymongo.errors import OperationFailure
#
from sefaria.model.webpage import *
from sefaria.model.text import *
from sefaria.helper.category import *
from sefaria.helper.topic import *
import requests
# script.py
from keybert import KeyBERT

doc = """
    Supervised learning is the machine learning task of learning a function that
    maps an input to an output based on example input-output pairs. It infers a
    function from labeled training data consisting of a set of training examples.
    In supervised learning, each example is a pair consisting of an input object
    (typically a vector) and a desired output value (also called the supervisory signal). 
    A supervised learning algorithm analyzes the training data and produces an inferred function, 
    which can be used for mapping new examples. An optimal scenario will allow for the 
    algorithm to correctly determine the class labels for unseen instances. This requires 
    the learning algorithm to generalize from the training data to unseen situations in a 
    'reasonable' way (see inductive bias).
"""

kw_model = KeyBERT()
keywords = kw_model.extract_keywords(doc)

print(kw_model.extract_keywords(doc, keyphrase_ngram_range=(1, 1), stop_words=None))
#[
#    ('learning', 0.4604),
#    ('algorithm', 0.4556),
#    ('training', 0.4487),
#    ('class', 0.4086),
#    ('mapping', 0.3700)
#]
count = 0
for book in sorted(library.get_indexes_in_category("Federalist Papers"), key=lambda x: int(x.split()[2])):
    count += 1
    book = library.get_index(book)
    book.order = [count]
    book.save()

cats = CategorySet({"path.0": "Constituting America"})
for cat in cats:
    if len(cat.path) == 2:
        cat.order += 5
        cat.save()

books = """United States Constitution
Articles of Confederation
The Proposed Bill of Rights
The US Bill of Rights
Amendments XI through XXVII""".splitlines()
for b, book in enumerate(books):
    i = library.get_index(book)
    i.order = [b+1, 1]
    i.save()
