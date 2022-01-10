import django
django.setup()
from sefaria.model import *
import itertools
import csv

REPORT = []

def issubref(r1, r2):
    return set(r1.all_segment_refs()).issubset(set(r2.all_segment_refs()))

def find_subref(r1, r2):
    #returns the on is subref ot the other. if none returns None. if r1==r2 returns r1
    if issubref(r1, r2):
        return r1
    elif issubref(r2, r1):
        return r2

def link_other_ref(trefs, ref):
    tref = [r for r in trefs if not set(ref.all_segment_refs()) & set(Ref(r).all_segment_refs())]
    if len(tref) != 1:
        print(f'problem in finding other ref for {ref} while link refs     are {trefs}')
        return
    return tref[0]

def ref_links_according_book(ref):
    links = ref.linkset()
    links = [l for l in links if any("JTmock" not in r for r in l.refs)]
    books = {}
    for link in links:
        tref = link_other_ref(link.refs, ref)
        try:
            books[Ref(tref).book].append(link)
        except KeyError:
            books[Ref(tref).book] = [link]
    return books

def ref_intersect(tref1, tref2):
    refs = set(Ref(tref1).all_segment_refs()) & set(Ref(tref2).all_segment_refs())
    for ref in refs:
        if all(not ref.follows(r) for r in refs):
            first = ref
        if all(not r.follows(ref) for r in refs):
            last = ref
        try:
            return f'{first.normal()}-{last.normal().split()[-1]}'
        except NameError:
            pass

def handle_double_links(two_links, ref):
    #two_links should be of the given ref. preferable all links to a given book
    other_tref1 = link_other_ref(two_links[0].refs, ref)
    tref1 = (set(two_links[0].refs)-{other_tref1}).pop()
    other_tref2 = link_other_ref(two_links[1].refs, ref)
    tref2 = (set(two_links[1].refs)-{other_tref2}).pop()
    other_tref = find_subref(Ref(other_tref1), Ref(other_tref2))
    if other_tref:
        other_tref = other_tref.tref
        ref = find_subref(Ref(tref1), Ref(tref2))
        if ref:
            tref = ref.tref
        else:
            tref = ref_intersect(tref1, tref2)
        two_links[0].refs = [tref, other_tref]
        two_links[0].save()
        two_links[1].delete()
        print(f'old links: 1. {tref1}, {other_tref1}; 2. {tref2}, {other_tref2}')
        print(f'new link: {tref}, {other_tref}')
        return True

def handle_links_ref(ref):
    linksets = ref_links_according_book(ref).values()
    couples = [couple for linkset in linksets for couple in itertools.combinations(linkset, 2) if len(linkset) > 1]
    for couple in couples:
        if handle_double_links(couple, ref):
            handle_links_ref(ref)
            break

def del_self(ref):
    for link in ref.linkset():
        if all(Ref(r).contains(ref) for r in link.refs):
            print(f'del self link: {link.refs}')
            link.delete()

def self_ref(trefs, tref):
    return (set(trefs) - {tref}).pop()

def get_linked_trefs(ref):
    linked_trefs = {}
    for link in ref.linkset():
        other = link_other_ref(link.refs, ref)
        first = self_ref(link.refs, other)
        if other and first and Ref(first).is_segment_level():
            linked_trefs[other] = first
    return linked_trefs

def accur_by_3rd_party(ref):
    links = ref.linkset()
    if len(links) < 2:
        return
    linked_trefs = get_linked_trefs(ref)
    for link in links:
        trefs = set(link.refs)
        if any(not Ref(r).is_segment_level() for r in trefs):
            tref1 = link_other_ref(trefs, ref)
            linked_trefs0 = {k: v for k, v in linked_trefs.items() if v != tref1}
            exp_linked_trefs0 = {r.tref: v for tr, v in linked_trefs0.items() for r in Ref(tr).all_segment_refs()}
            linked_trefs1 = get_linked_trefs(Ref(tref1))
            exp_linked_trefs1 = {r.tref: v for tr, v in linked_trefs1.items() for r in Ref(tr).all_segment_refs()}
            common = exp_linked_trefs0.keys() & exp_linked_trefs1.keys()
            options = {(exp_linked_trefs0[exp], exp_linked_trefs1[exp]) for exp in common}
            if len(options) == 1:
                REPORT.append({'refs_before': trefs, 'vectors': common, 'accurated': options, 'changed': True})
                if len(options) == 1:
                    link.refs = list(options)[0]
                    link.save()
            elif len(options) > 1:
                REPORT.append({'refs_before': trefs, 'vectors': common, 'accurated': options, 'changed': False})

if __name__ == '__main__':
    indexes = [ind for ind in library.get_indexes_in_category('Yerushalmi')]
    for ind in indexes:
        print(ind)
        for ref in Ref(ind).all_segment_refs():
            del_self(ref)
            handle_links_ref(ref)
            accur_by_3rd_party(ref)
    with open('vectors_report.csv', 'w', encoding='utf-8', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=['refs_before', 'vectors', 'accurated', 'changed'])
        writer.writeheader()
        for row in REPORT:
            writer.writerow(row)
