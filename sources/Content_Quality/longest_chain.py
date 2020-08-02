import django
django.setup()
from sefaria.model import *
def travel(start_ref, times=0, already_hit_refs=[], already_hit_cats=[]):
    finds = []
    if len(already_hit_refs) > 3:
        print(already_hit_refs)
        return already_hit_refs
    for l in LinkSet(start_ref):
        other_ref = l.refs[0] if l.refs[0] != start_ref else l.refs[1]
        other_ref = Ref(other_ref)
        other_index = other_ref.index
        segments = other_index.all_segment_refs()
        if len(segments) > 0 and other_ref == segments[0]:
            continue
        if other_index.title not in already_hit_cats:
            try:
                finds += travel(other_ref, times+1, already_hit_refs+[other_ref], already_hit_cats+[other_index.title])
            except:
                pass
        if len(finds) > 10:
            print(already_hit_refs)
            return finds
    return already_hit_refs


start_ref = "United States Constitution"
finds = travel(Ref(start_ref))
print(finds)
