#encoding=utf-8
import django
django.setup()
from sefaria.model import *
import csv
from sources.functions import *
alt_node = ArrayMapNode()
alt_node.add_primary_titles("Chapters", u"פרקים")
alt_node.depth = 1
alt_node.wholeRef = "Malbim Ayelet HaShachar 1-613"
alt_node.refs = []
alt_node.add_structure(["Chapters"])
with open("Malbim_Ayelet_HaShachar_alt_struct_-_Sheet1.csv") as f:
    for i, row in enumerate(csv.reader(f)):
        if i == 0:
            continue
        alt_struct_ch, start, end = row
        start = "Malbim Ayelet HaShachar {}".format(start)
        alt_node.refs += [start+"-"+end]

    alt_node.validate()



    index = get_index_api("Malbim Ayelet HaShachar", server="http://ste.sandbox.sefaria.org")
    index['alt_structs'] = {"Chapters": {"nodes": [alt_node.serialize()]}}
    post_index(index, server="http://ste.sandbox.sefaria.org")
