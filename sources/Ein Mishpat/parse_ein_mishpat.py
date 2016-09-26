# coding=utf-8

from optparse import OptionParser
import unicodecsv as csv

usage = "\n%prog [options] inputfile\n  inputfile is a TSV, with references in columns Q-U"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--check", action="store_true", dest="check_only",
                  help="Check references only, don't write links")
parser.add_option("-f", "--force", action="store_true", dest="force",
                  help="Force post of data, even with known errors")
(options, args) = parser.parse_args()

if len(args) != 1:
    print "Please supply a data file name on the command line."
    exit()

# Delay import, so that --help case doesn't delay on library load
from sefaria.system.exceptions import InputError
from sefaria.model import *
from sefaria.helper.link import create_link_cluster

# 16 Talmud
# 17 Rambam
# 18 Smag
# 19 ShuA
# 20 Tur
clean = True
line_num = 2
with open(args[0]) as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        line_num += 1
        if not l[16]:
            continue
        for n in range(16, 21):
            try:
                if not l[n]:
                    continue
                r = Ref(l[n])
                tc = TextChunk(r, "he")
                if tc.is_empty():
                    print u"Line: {} No text at Ref: {}".format(line_num, l[n])
                    clean = False
            except InputError as e:
                print u"Line: {} Failed to parse Ref: {}".format(line_num, l[n])
                clean = False
            except AttributeError as e:
                print u"Line: {} Malformed Ref: {}".format(line_num, l[n])
                clean = False


def create_cluster(c):
    return create_link_cluster(c, 28, "Ein Mishpat / Ner Mitsvah",
                        attrs={"generated_by": "Ein Mishpat Cluster"},
                        exception_pairs=[("Tur", "Shulchan Arukh")])


if options.check_only:
    exit()
if not clean and not options.force:
    exit()

total = 0
cluster_refs = None

with open(args[0]) as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        line_num += 1
        if not l[16]:
            continue

        if options.check_only:
            continue

        current_ref = Ref(l[16])
        if not current_ref:
            print u"Not a ref? {}".format(l[16])
            continue

        # first line
        if cluster_refs is None:
            cluster_refs = [Ref(l[n]) for n in range(16, 21) if l[n]]

        # If this line's ref differs from the last
        elif cluster_refs and current_ref != cluster_refs[0]:
            # Load up the previous collection
            total += create_cluster(cluster_refs)

            # and start new cluster, including Talmud
            cluster_refs = [Ref(l[n]) for n in range(16, 21) if l[n]]
        else:
        # otherwise is for the same ref as the last
            # Add these references to the last collection
            cluster_refs += [Ref(l[n]) for n in range(17, 21) if l[n]]


#last line
if cluster_refs:
    total += create_cluster(cluster_refs)

print total