# coding=utf-8

from optparse import OptionParser
import unicodecsv as csv

usage = "\n%prog [options] inputfile\n  inputfile is a TSV, with references in columns Q-U"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--check", action="store_true", dest="check_only",
                  help="Check references only, don't write links")
parser.add_option("-s", "--statcheck", action="store_true", dest="check_stats",
                  help="Check for statistical outliers")
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

# Checking for validity of references
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

# Statistical model - not working very well
if options.check_stats:
    data = {}
    sas = {}
    rms = {}

    def add_to_ref_dict(d, from_ref, to_ref):
        if not d.get(from_ref):
            d[from_ref] = {}
        if d[from_ref].get(to_ref):
            d[from_ref][to_ref] += 1
        else:
            d[from_ref][to_ref] = 1

    def check_ref_dict(d):
        for ref_from, to_dict in d.iteritems():
            if len(to_dict) < 2:
                continue
            total = float(sum(to_dict.values()))
            card = float(len(to_dict))
            for ref_to, count in to_dict.iteritems():
                if count < float(total / card):
                    tls = data.get((ref_to, ref_from), data.get((ref_from, ref_to)))
                    print "Suspect: {},  Compared to: {}".format(ref_to, ref_from)
                    print "Total: {}, Cardinality: {}, Count: {}".format(int(total), int(card), count)
                    print "Others: {}".format(
                        ", ".join(["{}({})".format(r.normal(), c) for r, c in to_dict.items() if r != ref_to]))
                    print "Found at: {}\n".format(", ".join([r.normal() for r in tls]))


    with open(args[0]) as tsv:
        next(tsv)
        next(tsv)
        for l in csv.reader(tsv, dialect="excel-tab"):
            if not l[16] or not l[17] or not l[19]:
                continue
            tl = Ref(l[16])
            rm = Ref(l[17])
            sa = Ref(l[19])

            if not data.get((rm,sa)):
                data[(rm, sa)] = []
            data[(rm, sa)] += [tl]

            add_to_ref_dict(sas, sa, rm)
            add_to_ref_dict(rms, rm, sa)

    check_ref_dict(sas)
    check_ref_dict(rms)


if options.check_only or options.check_stats:
    exit()
if not clean and not options.force:
    exit()


def create_cluster(c):
    return create_link_cluster(c, 28, "Ein Mishpat / Ner Mitsvah",
                        attrs={"generated_by": "Ein Mishpat Cluster"},
                        exception_pairs=[("Tur", "Shulchan Arukh")])

# Aggregate and Post links
total = 0
cluster_refs = None
with open(args[0]) as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
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