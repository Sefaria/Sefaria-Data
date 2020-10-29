# coding=utf-8

import django
django.setup()

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
                        print(u"Line: {} No text at Ref: {}".format(i, cit))
                        clean = False
                    col_refs.append(r)
            except InputError as e:
                    print(u"Line: {} Failed to parse Ref: {}".format(i, cit))
                    clean = False
            except AttributeError as e:
                print(u"Line: {} Malformed Ref: {}".format(i, cit))
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
    # query_talmud = {''' "generated_by": "Ein Mishpat Cluster {}", $and: [ {{ "refs.0": /.*{}.*/i }} ] '''.format(massekhet,massekhet)}
    # query_tush = {''' "generated_by": "Ein Mishpat Cluster {}", $and: [ {{ "refs.0": /.*{}.*/i }} ] '''.format(massekhet)}
    # query_rambam = {''' "generated_by": "Ein Mishpat Cluster {}", $and: [ {{ "refs.0": /.*{}.*/i }} ] '''.format(massekhet)}
    # query_semag = {''' "generated_by": "Ein Mishpat Cluster {}", $and: [ {{ "refs.0": /.*{}.*/i }} ] '''.format(massekhet)}
    linkset = LinkSet(query)
    links = [l.contents() for l in linkset]
    # for l in links:
    #     l["generated_by"] = "Ein Mishpat Cluster"
    post_link(links)
    return links

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


if __name__ == "__main__":
    massekhet = 'Rif'
    # final_list = segment_column(u'done/niddah_little_letters.csv', u'done/niddah_little_letters.csv', massekhet, wikitext=False)
    # print final_list
    # validation = validity_and_cluster(final_list)
    # save_links_local(final_list, massekhet)
    links = post_ein_mishpat(massekhet)
    print('done')