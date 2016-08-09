# coding=utf-8

import unicodecsv as csv

from sefaria.model import *
from sefaria.helper.link import create_link_cluster

# 10 Talmud
# 11 Rambam
# 12 Smag
# 13 ShuA
# 14 Tur

total = 0
#todo: introduce error-checking to avoid dead links.  Checked by Ref on section level, but not segment.

def create_cluster(c):
    return create_link_cluster(c, 28, "Ein Mishpat / Ner Mitsvah",
                        attrs={"generated_by": "Ein Mishpat Cluster"},
                        exception_pairs=[("Tur", "Shulchan Arukh")])


cluster_refs = None
with open("Ein Mishpat - Rosh HaShanah - Links.tsv") as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        if not l[10]:
            continue

        current_ref = Ref(l[10])
        if not current_ref:
            print "Not a ref? {}".format(l[10])
            continue

        # first line
        if cluster_refs is None:
            cluster_refs = [Ref(l[n]) for n in range(10, 15) if l[n]]

        # If this line's ref differs from the last
        elif cluster_refs and current_ref != cluster_refs[0]:
            # Load up the previous collection
            total += create_cluster(cluster_refs)

            # and start new cluster, including Talmud
            cluster_refs = [Ref(l[n]) for n in range(10, 15) if l[n]]
        else:
        # otherwise is for the same ref as the last
            # Add these references to the last collection
            cluster_refs += [Ref(l[n]) for n in range(11, 15) if l[n]]

#last line
if cluster_refs:
    total += create_cluster(cluster_refs)

print total