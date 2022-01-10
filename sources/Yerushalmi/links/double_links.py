import django
django.setup()
from sefaria.model import *
from itertools import combinations

def del_self(ref):
    for link in ref.linkset():
        if all(Ref(r).contains(ref) for r in link.refs):
            print(f'del self link: {link.refs}')
            link.delete()

def link_other_ref(trefs, ref):
    tref = [r for r in trefs if not set(ref.all_segment_refs()) & set(Ref(r).all_segment_refs())]
    if len(tref) != 1:
        print(f'problem in finding other ref for {ref} while link refs     are {trefs}')
        return
    return tref[0]

def self_ref(refs, ref):
    return (set(refs) - {link_other_ref(refs, ref)}).pop()

def get_links(ref):
    links = ref.linkset()
    return [l for l in links if l.generated_by in ['add_links_from_text', 'yerushalmi_refs_inline', 'yerushalmi tables', 'yerushalmi-mishnah linker']]

def section(ref):
    if Ref(ref).is_segment_level():
        return False
    return Ref(ref).is_section_level() or Ref(ref).all_subrefs()[0].is_section_level()

def handle(ref):
    del_self(ref)
    changed = True
    while changed:
        links = get_links(ref)
        if len(links) < 2:
            return
        for copule in combinations(links, 2):
            l1, l2 = copule
            if set(l1.refs) == set(l2.refs):
                if l1.generated_by == 'yerushalmi_refs_inline':
                    l2.delete()
                else:
                    l1.delete()
                changed = True
                break
            linked1, linked2 = (link_other_ref(link.refs, ref) for link in copule)
            if not (linked1 and linked2): #self links
                changed = False
                continue
            if Ref(linked1).overlaps(Ref(linked2)):
                noah = [l for l in copule if l.generated_by == 'yerushalmi_refs_inline']
                other = [l for l in copule if l.generated_by != 'yerushalmi_refs_inline']
                if len(noah) == 2:
                    if Ref(linked1).contains(Ref(linked2)):
                        l1.delete()
                    else:
                        l2.delete()
                    changed = True
                    break
                if noah and other:
                    noah = noah[0]
                    other = other[0]
                    if all(Ref(r).is_segment_level() for r in noah.refs):
                        if other.generated_by == 'yerushalmi tables':
                            other.delete()
                            changed = True
                            break
                l1_here, l2_here = self_ref(l1.refs, ref), self_ref(l2.refs, ref)
                l1_other, l2_other = link_other_ref(l1.refs, ref), link_other_ref(l2.refs, ref)
                if any(section(l) for l in [l1_here, l2_here]) and any(Ref(l).is_segment_level() for l in [l1_here, l2_here]):
                    new_here = [l for l in [l1_here, l2_here] if Ref(l).is_segment_level()][0]
                elif l1_here == l2_here:
                    new_here = l1_here
                elif all(section(l) for l in [l1_here, l2_here]):
                    if Ref(l1_here).contains(Ref(l2_here)):
                        new_here = l2_here
                    elif Ref(l2_here).contains(Ref(l1_here)):
                        new_here = l1_here
                elif Ref(l1_here).contains(Ref(l2_here)) and l1.generated_by == 'yerushalmi tables':
                    new_here = l2_here
                elif Ref(l2_here).contains(Ref(l1_here)) and l2.generated_by == 'yerushalmi tables':
                    new_here = l1_here
                else:
                    new_here = False
                if any(section(l) for l in [l1_other, l2_other]) and any(Ref(l).is_segment_level() for l in [l1_other, l2_other]):
                    new_other = [l for l in [l1_other, l2_other] if Ref(l).is_segment_level()][0]
                elif l1_other == l2_other:
                    new_other = l1_other
                elif all(section(l) for l in [l1_other, l2_other]):
                    if Ref(l1_other).contains(Ref(l2_other)):
                        new_other = l2_other
                    elif Ref(l2_other).contains(Ref(l1_other)):
                        new_other = l1_other
                elif Ref(l1_other).contains(Ref(l2_other)) and l1.generated_by == 'yerushalmi tables':
                    new_other = l2_other
                elif Ref(l2_other).contains(Ref(l1_other)) and l2.generated_by == 'yerushalmi tables':
                    new_other = l1_other
                else:
                    new_other = False
                if new_other and new_here:
                    if l1.generated_by == 'yerushalmi_refs_inline':
                        remain = l1
                        l2.delete()
                    else:
                        remain = l2
                        l1.delete()
                    remain.refs = [new_here, new_other]
                    remain.save()
                    #update and del
                    changed = True
                    break
                print(linked1, l1.refs, l1.generated_by, linked2, l2.refs, l2.generated_by, l1_here, l2_here, new_here, new_other)
            changed = False

if __name__ == '__main__':
    LinkSet({'generated_by': 'add_links_from_text', 'refs': {'$regex': '^Jerusalem Talmud '}}).delete()
    indexes = [ind for ind in library.get_indexes_in_category('Yerushalmi')]
    for ind in indexes:
        print(ind)
        for ref in Ref(ind).all_segment_refs():
            handle(ref)
