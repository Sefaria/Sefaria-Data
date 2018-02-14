# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'


#from data_utilities.util import set_ranges_between_refs
from sefaria.model import *
#from sources.functions import *
from bson import ObjectId
from sefaria.system.exceptions import *

def set_ranges_between_refs(refs, section_ref):
    '''
    :refs: an unsorted list of segments such as [Ref(Rashi on Genesis 2:11), Ref(Rashi on Genesis 2:4), Ref(Rashi on Genesis 2:10)]
    where all refs have the same section
    :section_ref: the section reference for the list of refs, in this case Ref(Rashi on Genesis 2)
    :return: sorted list of ranged refs where the i-th element is a range from itself to the i+1-th element.
    The last ref in the list is a range from itself to the final segment in the section, which for Rashi on Genesis 2 is 25.
    In this case:
    [Ref(Rashi on Genesis 2:4-9), Ref(Rashi on Genesis 2:10), Ref(Rashi on Genesis 2:11-25)]
    If an empty list is passed as refs, we simply return a list with one range over the entire section, such as:
    [Ref(Rashi on Genesis 2:1-25)]
    '''
    if refs == []:
        first_ref = section_ref.subref(1)
        return [first_ref.to(section_ref.all_segment_refs()[-1])]


    ranged_refs = []
    len_list = len(refs)
    refs = sorted(refs, key=lambda x: x.order_id())
    last_ref = section_ref.all_segment_refs()[-1]
    #print "Refs: {}".format(refs)
    #print "Section: {}".format(section_ref)
    #print "Last ref: {}".format(last_ref)
    for i, ref in enumerate(refs):
        if ref.is_range():
            ranged_refs.append(ref)
            continue
        assert ref.section_ref() is section_ref
        if i + 1 == len_list:
            new_range = ref.to(last_ref)
        else:
            next_ref = refs[i+1]
            if next_ref.sections[-1] == ref.sections[-1]:
                ranged_refs.append(ref)
                continue
            else:
                d = next_ref._core_dict()
                d['sections'][-1] -= 1
                d['toSections'][-1] -= 1
                new_range = ref.to(Ref(_obj=d))
        ranged_refs.append(new_range)
    return ranged_refs

def prep_for_json(dict):
    for k, v in dict.items():
        if isinstance(v, ObjectId):
            dict[k] = str(v)
    return dict

if __name__ == "__main__":
    '''
    Iterate over sections, passing links per section to set_ranges_between_refs
    '''
    index = library.get_index("Rabbeinu Bahya")
    sefarim = index.nodes.children[1:]
    segment_links = {}
    section_links = {}
    links_to_post = {}
    for sefer in sefarim:
        sefer_ref = sefer.ref()
        ls = LinkSet(sefer_ref)
        for l in ls:
            assert l.refs[0].startswith("Rabbeinu Bahya") or l.refs[1].startswith("Rabbeinu Bahya")
            bahya, other = (l.refs[0], l.refs[1]) if l.refs[0].startswith("Rabbeinu Bahya") else (l.refs[1], l.refs[0])
            bahya = Ref(bahya)
            other = Ref(other)
            bahya_has_text = bahya.text('he').text != ""
            if not bahya_has_text:
                l.delete()
                continue
            assert len(bahya.sections) in [2,3]
            altered_ref = Ref(bahya.section_ref().normal().replace("Rabbeinu Bahya, ", ""))
            if altered_ref == other:
                which_dict = section_links if len(bahya.sections) == 2 else segment_links
                if bahya.section_ref() not in which_dict:
                    which_dict[bahya.section_ref()] = []
                which_dict[bahya.section_ref()].append((l, bahya))


    for bahya_section_ref, tuples in segment_links.items():
        links, bahya_refs = [list(x) for x in zip(*tuples)]
        new_bahya_refs = set_ranges_between_refs(bahya_refs, bahya_section_ref)
        for link, new_ref in zip(links, new_bahya_refs):
            pos = 0 if link.refs[0].startswith("Rabbeinu Bahya") else 1
            if new_ref.normal() != link.refs[pos]:
                print "found one"
                link.refs[pos] = new_ref.normal()
                link.save()




    bahya_section_refs = [ref for ref in section_links.keys() if ref not in segment_links.keys()]
    for bahya_section_ref, tuples in section_links.items():
        if ref in segment_links.keys():
            continue
        link = tuples[0][0]
        new_ref = set_ranges_between_refs([], bahya_section_ref)[0]
        pos = 0 if link.refs[0].startswith("Rabbeinu Bahya") else 1
        if new_ref.normal() != link.refs[pos]:
            link.refs[pos] = new_ref.normal()
            link.save()




