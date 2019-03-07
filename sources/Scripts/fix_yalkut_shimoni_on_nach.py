# encdoing=utf-8
from __future__ import unicode_literals
import requests
import unicodecsv as csv

import django
django.setup()
from sefaria.model import *
from sources.functions import post_index


def get_title(node):
    titles = node["titles"]
    for t in titles:
        if t["lang"] == "en" and t.get('primary', False):
            return t["text"]


def no_overlap(ref_list):
    ref_list = [Ref(tref) for tref in ref_list]
    for cur_oref, next_oref in zip(ref_list[:-1], ref_list[1:]):
        if next_oref.overlaps(cur_oref) or not next_oref.follows(cur_oref):
            return False
    return True


def find_overlap(ref_list):
    overlaps = []
    ref_list = [Ref(tref) for tref in ref_list]

    for ref_num, (cur_ref, next_ref) in enumerate(zip(ref_list[:-1], ref_list[1:])):
        if next_ref.overlaps(cur_ref) or not next_ref.follows(cur_ref):
            print "{} overlaps with {}".format(cur_ref.normal(), next_ref.normal())
            overlaps.append(ref_num)
    return overlaps


def post_overlap(ref_list, issue_tracker):
    for prev_ref, cur_ref in zip(ref_list[:-1], ref_list[1:]):
        if cur_ref.overlaps(prev_ref):
            issue_tracker.add_issue(cur_ref, "Overlap", "Overlaps with {}".format(prev_ref))


def post_protrusion(ref_list, container_ref, issue_tracker):
    for tref in ref_list:
        if not container_ref.contains(tref):
            issue_tracker.add_issue(tref, "Protrusion", "Protrudes from book range ({})".format(container_ref.normal()))


def post_gap(ref_list, container_ref, issue_tracker):
    range_start, range_end = container_ref.starting_ref(), container_ref.ending_ref()
    first_uncovered_ref = range_start

    for tref in ref_list:
        if tref.sections > first_uncovered_ref.sections:
            issue_tracker.add_issue(tref, "Gaps", "{} is left uncovered".format(first_uncovered_ref.normal()))
        first_uncovered_ref = tref.next_segment_ref()

    if ref_list[-1].toSections < range_end.sections:
        message = "Last ref ends before book ends (book ends at {})".format(range_end.normal())
        old_message = issue_tracker.get_issue("Gaps")
        if old_message:
            message = '{}; {}'.format(old_message, message)
        issue_tracker.add_issue(ref_list[-1], "Gaps", message)


def bind_refs_to_wholerefs(book_node):
    wholeref = Ref(book_node['wholeRef'])
    whole_start, whole_end = wholeref.starting_ref(), wholeref.ending_ref()

    first_ref = Ref(book_node['refs'][0])
    first_start, first_end = first_ref.starting_ref(), first_ref.ending_ref()
    if first_start.normal() != whole_start.normal():
        first_ref = whole_start.to(first_end)
        book_node['refs'][0] = first_ref.normal()

    last_ref = Ref(book_node['refs'][-1])
    last_start, last_end = last_ref.starting_ref(), last_ref.ending_ref()
    if last_end.normal() != whole_end.normal():
        last_ref = last_start.to(whole_end)
        book_node['refs'][-1] = last_ref.normal()


def check_full_coverage(ref_list, range_start, range_end):
    ref_list = sorted([Ref(tref) for tref in ref_list], key=lambda x: x.starting_ref().sections)
    end_of_coverage = range_start

    for oref in ref_list:
        if oref.sections > end_of_coverage.sections:
            # print "gap found at {}".format(oref.normal())
            return False
        elif oref.ending_ref().sections >= range_end.sections:
            return True
        else:
            end_of_coverage = oref.ending_ref().next_segment_ref()

    return False  # we finished iterating, but didn't reach the end of the range


def check_node_full_coverage(node_item):
    node_refs = [tref for tref in node_item['refs'] if tref]
    wholeref = Ref(node_item['wholeRef'])
    range_start, range_end = wholeref.starting_ref(), wholeref.ending_ref()

    if not check_full_coverage(node_refs, range_start, range_end):
        print "Gaps found in {}".format(get_title(node_item))


class RefListTracker(object):
    def __init__(self, node_object):
        self.book = get_title(node_object)
        self.whole_ref = node_object['wholeRef']
        self.ref_list = node_object['refs']
        self.sorted_ref_list = self._create_sorted_ref_list()
        self.ref_issue_map = {tref: {} for tref in self.ref_list}

    def _create_sorted_ref_list(self):
        return sorted([Ref(tref) for tref in self.ref_list if tref], key=lambda x: x.sections)

    def get_data_for_csv_dump(self):
        rows = [
            {
                'Book': self.book,
                'Chapter': chap_num,
                'ref': tref
            } for chap_num, tref in enumerate(self.ref_list, 1)
        ]
        for row in rows:
            row.update(self.ref_issue_map[row['ref']])
        return rows

    def add_issue(self, tref, issue_type, message):
        if isinstance(tref, Ref):
            tref = tref.normal()
        self.ref_issue_map[tref][issue_type] = message

    def get_issue(self, tref, issue_type):
        if isinstance(tref, Ref):
            tref = tref.normal()
        return self.ref_issue_map[tref].get(issue_type, '')


class FixedReport(object):

    def __init__(self, filename='Yalkut_on_Nach_repairs.csv'):
        self.books = self.build_book_map(filename)

    @staticmethod
    def build_book_map(filename):
        books = {}
        with open(filename) as fp:
            rows = list(csv.DictReader(fp))

        for row in rows:
            cur_book = books.setdefault(row['Book'], [])
            if int(row['Chapter']) - len(cur_book) != 1:
                print row
                raise IndexError
            cur_book.append(row.get('ref', ''))

        return books

    def get_book_refs(self, book_title):
        return self.books[book_title]


response = requests.get('https://www.sefaria.org/api/v2/raw/index/Yalkut_Shimoni_on_Nach')
my_index = response.json()

nodes = my_index['alt_structs']['Books']['nodes']

start_refs = '''Judges - 37:3
I Samuel - 76:8
II Samuel - 141:6
Joel - 533:8
Amos - 538:5
Micah - 551:4
Nahum - 560:2
Habakkuk - 561:7
Zephaniah - 566:2
Haggai - 567:10
Nehemiah - 1069:14
Lamentations - 995:1
II Chronicles - 1083:2'''.split('\n')
start_refs = [i.split(' - ') for i in start_refs]
start_refs = {i[0]: i[1] for i in start_refs}

full_refs = {
    'Ecclesiastes': 'Yalkut Shimoni on Nach 965:1-979:78',
    'Song of Songs': 'Yalkut Shimoni on Nach 980:1-994:11'
}

report_data = FixedReport()

for node in nodes:
    node_title = get_title(node)
    if node_title in start_refs:
        r = Ref("Yalkut Shimoni on Nach {}".format(start_refs[node_title]))
        end_r = Ref(node['wholeRef']).ending_ref()
        node['wholeRef'] = r.to(end_r).normal()

    elif node_title in full_refs:
        node['wholeRef'] = full_refs[node_title]
        # bind_refs_to_wholerefs(node)

    node['refs'] = report_data.get_book_refs(node_title)

    check_node_full_coverage(node)
    node_refs = [i for i in node['refs'] if i]
    has_no_overlaps = no_overlap(node_refs)
    if not has_no_overlaps:
        print "overlaps found in {}".format(node_title)
        find_overlap(node_refs)


print '\n'

for node in nodes:
    if all([Ref(node['wholeRef']).contains(Ref(r)) for r in node['refs'] if r]):
        # print "{} is good".format(get_title(node))
        pass
    else:
        print "{} has refs that go outside range".format(get_title(node))

"""
Still need to do:
Make sure ref list in each node starts at the beginning of wholeRef and ends at the end of wholeRef.
Make sure refs in ref list do not overlap
Check that refs in ref list have complete coverage
"""
sorted_nodes = sorted(nodes, key=lambda x: Ref(x['wholeRef']).starting_ref().sections)
whole_refs = [n['wholeRef'] for n in nodes]
by_start = sorted(whole_refs, key=lambda x: Ref(x).starting_ref().sections)
by_end = sorted(whole_refs, key=lambda x: Ref(x).ending_ref().sections)

# if by_start == by_end:
#     print "both sorting methods match"
# else:
#     print "sorting methods give different results"

print '\n'

if no_overlap(by_start):
    print "no overlap in wholeRefs"
else:
    print "problem with wholeRefs"
issues = find_overlap(by_start)
for issue in issues:
    print get_title(sorted_nodes[issue]), "->", get_title(sorted_nodes[issue + 1])

print '\n'
full_coverage = check_full_coverage(whole_refs, Ref("Yalkut Shimoni on Nach 1:1"), Ref("Yalkut Shimoni on Nach 1085:30"))
if full_coverage:
    print "full coverage for wholeRefs"
else:
    print "not full coverage for wholeRefs"


output_rows = []
for node in nodes:
    ref_tracker = RefListTracker(node)
    w_ref = Ref(node['wholeRef'])
    post_gap(ref_tracker.sorted_ref_list, w_ref, ref_tracker)
    post_overlap(ref_tracker.sorted_ref_list, ref_tracker)
    post_protrusion(ref_tracker.sorted_ref_list, w_ref, ref_tracker)
    output_rows.extend(ref_tracker.get_data_for_csv_dump())

with open("Yalkut on Nach report.csv", 'w') as fp:
    fieldnames = ["Book", "Chapter", "ref", "Gaps", "Overlap", "Protrusion"]
    writer = csv.DictWriter(fp, fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

my_index['alt_structs']['Books']['nodes'] = nodes
post_index(my_index, server='https://www.sefaria.org')
