import django
django.setup()
from sefaria.model import *
import csv
from sources.functions import *
nodes = []
with open("Maaseh_Rav_Alt_Structure_Guide.csv") as f:

    for n, row in enumerate(csv.reader(f)):
        if n == 0:
            continue
        he, en, simanim = row[0:3]
        node = ArrayMapNode()
        node.add_primary_titles(en, he)
        node.depth = 0
        node.wholeRef = "Maaseh Rav {}".format(simanim.split("-")[0])
        node.refs = []
        nodes.append(node.serialize())


    index = get_index_api("Maaseh Rav", server="http://ste.sandbox.sefaria.org")
    index['alt_structs'] = {"Subject": {"nodes": nodes}}
    post_index(index, server="http://ste.sandbox.sefaria.org")