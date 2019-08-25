import django
django.setup()
from sefaria.model import *
from sources.functions import *
import csv
import codecs
nodes = []
current_schema_node = None
part = 0
for count, row in enumerate(csv.reader(open("alt.csv"))):
    he, en = row
    node = ArrayMapNode()
    node.add_primary_titles(en, he)
    node.depth = 0
    node.wholeRef = "Mivchar HaPeninim {}".format(count+1)
    node.refs = []
    node.validate()
    nodes.append(node.serialize())

index = get_index_api("Mivchar HaPeninim", server="http://shmuel.sandbox.sefaria.org")
index['alt_structs'] = {"Topic": {"nodes": nodes}}
post_index(index, server="http://shmuel.sandbox.sefaria.org")