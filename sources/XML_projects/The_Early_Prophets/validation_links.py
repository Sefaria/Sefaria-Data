from sources.functions import *

i = library.get_index("The Five Books of Moses, by Everett Fox")
for j, sec_ref in enumerate(i.all_section_refs()):

    first = sec_ref.all_segment_refs()[0]
    second = sec_ref.all_segment_refs()[1]
    first_has = LinkSet({"refs": first.normal()}).count() > 0
    second_has = LinkSet({"refs": {"$regex": "^"+second.normal()}}).count() > 0
    l = Link().load({"refs": first.normal()})
    if first_has and second_has:
        tanakh_ref = l.refs[0] if l.refs[1].startswith("The Five") else l.refs[1]
        five_ref = l.refs[1] if l.refs[1].startswith("The Five") else l.refs[0]
        ls = LinkSet({"refs": {"$regex": "^" + second.normal()}, "type": 'essay'})
        other_ref = ls[0].refs[0] if ls[0].refs[0].startswith("The Five") else ls[0].refs[1]
        if " ".join(Ref(other_ref).as_ranged_segment_ref().normal().split()[:-1]) != " ".join(Ref(five_ref).as_ranged_segment_ref().normal().split()[:-1]):
            print(Ref(other_ref).as_ranged_segment_ref().normal())
            print(Ref(five_ref).as_ranged_segment_ref().normal())
    else:
        print("Missing link in {}".format(sec_ref))