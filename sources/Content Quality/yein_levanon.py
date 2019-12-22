import django
django.setup()
from sefaria.model import *
import csv
from sources.functions import *
import re
new_link_ref = None
links = []
def add_link(start, end):
    avot = "Pirkei " + start.replace("Yein Levanon on ", "").rsplit(":", 1)[0]
    if start == end:
        links.append({"refs": [start, avot], "generated_by": "yein_levanon_to_avot", "auto": True, "type": "Commentary"})
    elif start.rsplit(":", 1)[0] == end.rsplit(":", 1)[0]:
        range_ref = start+"-"+end.rsplit(":", 1)[-1]
        links.append({"refs": [range_ref, avot], "generated_by": "yein_levanon_to_avot", "auto": True, "type": "Commentary"})
    else:
        print start
        print end

with open("Yein Levanon on Avot - he - Yein Levanon, Rishon Letzion 2013.csv") as f:
    for row in csv.reader(f):
        ref, text = row
        if row[0].startswith("Yein Levanon") and not "Conclusion" in ref:
            dh = re.search("<b>.*?</b>", text)
            if dh:
                if new_link_ref:
                    add_link(new_link_ref, prev_ref)
                new_link_ref = ref
            prev_ref = ref
    add_link(new_link_ref, prev_ref)
print len(links)
post_link(links)