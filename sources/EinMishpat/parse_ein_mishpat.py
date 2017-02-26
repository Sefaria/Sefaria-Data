# coding=utf-8

from optparse import OptionParser
import unicodecsv as csv
from ein_parser import segment_column
from sources.functions import post_link


def validity_and_cluster(dict_list):
    clean = True
    all_clusters = []
    for i, row in enumerate(dict_list):
        col_refs = []
        if not row['Segment']:
            continue
        seg_ref = Ref(row['Segment'])  # two lines so to see where it leaves the try on the ref creation?
        col_refs.append(seg_ref)
        for col in ['Rambam', 'Semag', 'Tur Shulchan Arukh']:
            try:
                if not row[col]:
                    continue
                com_list = eval(row[col])
                for cit in com_list:
                    r = Ref(cit)
                    if r.is_empty():
                        print u"Line: {} No text at Ref: {}".format(i, cit)
                        clean = False
                    col_refs.append(r)
            except InputError as e:
                    print u"Line: {} Failed to parse Ref: {}".format(i, cit)
                    clean = False
            except AttributeError as e:
                print u"Line: {} Malformed Ref: {}".format(i, cit)
                clean = False
        all_clusters.append(col_refs)
    return (clean, all_clusters)

# c - a list of refs all to be interconnected
def create_cluster(c, massekhet):
    return create_link_cluster(c, 30044, "Ein Mishpat / Ner Mitsvah",
                        attrs={"generated_by": "Ein Mishpat Cluster {}".format(massekhet)},
                        exception_pairs=[("Tur", "Shulchan Arukh")])
#
def save_links_local(dict_list, massekhet):
    v_and_c = validity_and_cluster(dict_list)
    if not v_and_c[0]:
        return
    for cluster in v_and_c[1]:
        create_cluster(cluster, massekhet)

def post_ein_mishpat(massekhet):
    query = {"generated_by":"Ein Mishpat Cluster {}".format(massekhet)}
    linkset = LinkSet(query)
    links = [l.contents() for l in linkset]
    for l in links:
        l["generated_by"] = "Ein Mishpat Cluster"
    post_link(links)


# usage = "\n%prog [options] inputfile\n  inputfile is a TSV, with references in columns Q-U"
# parser = OptionParser(usage=usage)
# parser.add_option("-c", "--check", action="store_true", dest="check_only",
#                   help="Check references only, don't write links")
# parser.add_option("-s", "--statcheck", action="store_true", dest="check_stats",
#                   help="Check for statistical outliers")
# parser.add_option("-f", "--force", action="store_true", dest="force",
#                   help="Force post of data, even with known errors")
# (options, args) = parser.parse_args()
#
# if len(args) != 1:
#     print "Please supply a data file name on the command line."
#     exit()

# Delay import, so that --help case doesn't delay on library load
from sefaria.system.exceptions import InputError
from sefaria.model import *
from sefaria.helper.link import create_link_cluster

# 16 Talmud - Segment
# 17 Rambam - Rambam
# 18 Smag - Semag
# 19 ShuA - Tur Shulchan Arukh
# 20 Tur
#
# def validity_check(filename):
#     # Checking for validity of references
#     clean = True
#     line_num = 2
#     with open(u'{}.csv'.format(filename), 'r') as csvfile:
#         linkes = []
#         file_reader = csv.DictReader(csvfile)
#         for i, row in enumerate(file_reader):
#             if not row['Segment']:
#                 continue
#             for col in ['Rambam', 'Semag', 'Tur Shulchan Arukh']:
#                 try:
#                     if not row[col]:
#                         continue
#                     com_list = eval(row[col])
#                     for cit in com_list:
#                         r = Ref(cit)
#                         tc = TextChunk(r, 'he')
#                         # link = (
#                         #     {
#                         #         "refs": [
#                         #             row['Segment'], r
#                         #         ],
#                         #         "type": "Ein Mishpat",
#                         #         "auto": True,
#                         #         "generated_by": "Ein Mishpat Cluster"
#                         #     })
#                         # linkes.append(link)
#                         if tc.is_empty():
#                             print u"Line: {} No text at Ref: {}".format(i, cit)
#                             clean = False
#                 except InputError as e:
#                         print u"Line: {} Failed to parse Ref: {}".format(i, cit)
#                         clean = False
#                 except AttributeError as e:
#                     print u"Line: {} Malformed Ref: {}".format(i, cit)
#                     clean = False
#
#
#
# def create_cluster(c):
#     return create_link_cluster(c, 30044, "Ein Mishpat / Ner Mitsvah",
#                         attrs={"generated_by": "Ein Mishpat Cluster"},
#                         exception_pairs=[("Tur", "Shulchan Arukh")])
#
# def Lev_cheking(args, line_num = 2):
#     with open(args[0]) as tsv:
#         next(tsv)
#         next(tsv)
#         for l in csv.reader(tsv, dialect="excel-tab"):
#             line_num += 1
#             if not l[16]:
#                 continue
#             for n in range(16, 21):
#                 try:
#                     if not l[n]:
#                         continue
#                     r = Ref(l[n])
#                     tc = TextChunk(r, "he")
#                     if tc.is_empty():
#                         print u"Line: {} No text at Ref: {}".format(line_num, l[n])
#                         clean = False
#                 except InputError as e:
#                     print u"Line: {} Failed to parse Ref: {}".format(line_num, l[n])
#                     clean = False
#                 except AttributeError as e:
#                     print u"Line: {} Malformed Ref: {}".format(line_num, l[n])
#                     clean = False
#
# # # Statistical model - not working very well
# # def Lev_statistical():
# #     if options.check_stats:
# #         data = {}
# #         sas = {}
# #         rms = {}
# #
# #     def add_to_ref_dict(d, from_ref, to_ref):
# #         if not d.get(from_ref):
# #             d[from_ref] = {}
# #         if d[from_ref].get(to_ref):
# #             d[from_ref][to_ref] += 1
# #         else:
# #             d[from_ref][to_ref] = 1
# #
# #     def check_ref_dict(d):
# #         for ref_from, to_dict in d.iteritems():
# #             if len(to_dict) < 2:
# #                 continue
# #             total = float(sum(to_dict.values()))
# #             card = float(len(to_dict))
# #             for ref_to, count in to_dict.iteritems():
# #                 if count < float(total / card):
# #                     tls = data.get((ref_to, ref_from), data.get((ref_from, ref_to)))
# #                     print "Suspect: {},  Compared to: {}".format(ref_to, ref_from)
# #                     print "Total: {}, Cardinality: {}, Count: {}".format(int(total), int(card), count)
# #                     print "Others: {}".format(
# #                         ", ".join(["{}({})".format(r.normal(), c) for r, c in to_dict.items() if r != ref_to]))
# #                     print "Found at: {}\n".format(", ".join([r.normal() for r in tls]))
# #
# #
# #     with open(args[0]) as tsv:
# #         next(tsv)
# #         next(tsv)
# #         for l in csv.reader(tsv, dialect="excel-tab"):
# #             if not l[16] or not l[17] or not l[19]:
# #                 continue
# #             tl = Ref(l[16])
# #             rm = Ref(l[17])
# #             sa = Ref(l[19])
# #
# #             if not data.get((rm,sa)):
# #                 data[(rm, sa)] = []
# #             data[(rm, sa)] += [tl]
# #
# #             add_to_ref_dict(sas, sa, rm)
# #             add_to_ref_dict(rms, rm, sa)
# #
# #     check_ref_dict(sas)
# #     check_ref_dict(rms)
# #
# #
# # if options.check_only or options.check_stats:
# #     exit()
# # if not clean and not options.force:
# #     exit()
#
#
# def create_cluster(c):
#     return create_link_cluster(c, 30044, "Ein Mishpat / Ner Mitsvah",
#                         attrs={"generated_by": "Ein Mishpat Cluster"},
#                         exception_pairs=[("Tur", "Shulchan Arukh")])
#
# Aggregate and Post links
# def aggregate_post(args, options):
#     total = 0
#     cluster_refs = None
#     with open(args[0]) as tsv:
#         next(tsv)
#         next(tsv)
#         for l in csv.reader(tsv, dialect="excel-tab"):
#             if not l[16]:
#                 continue
#
#             if options.check_only:
#                 continue
#
#             current_ref = Ref(l[16])
#             if not current_ref:
#                 print u"Not a ref? {}".format(l[16])
#                 continue
#
#             # first line
#             if cluster_refs is None:
#                 cluster_refs = [Ref(l[n]) for n in range(16, 21) if l[n]]
#
#             # If this line's ref differs from the last
#             elif cluster_refs and current_ref != cluster_refs[0]:
#                 # Load up the previous collection
#                 total += create_cluster(cluster_refs)
#
#                 # and start new cluster, including Talmud
#                 cluster_refs = [Ref(l[n]) for n in range(16, 21) if l[n]]
#             else:
#             # otherwise is for the same ref as the last
#                 # Add these references to the last collection
#                 cluster_refs += [Ref(l[n]) for n in range(17, 21) if l[n]]
#
#
#     #last line
#     if cluster_refs:
#         total += create_cluster(cluster_refs)
#
#     print total

if __name__ == "__main__":
    massekhet = 'Chagigah'
    # final_list = segment_column(u'Ein Mishpat - Chagigah.csv', u'hg_test_done.csv', massekhet)
    # validation = validity_and_cluster(final_list)
    # save_links_local(final_list,massekhet)
    post_ein_mishpat(massekhet)
    print 'done'