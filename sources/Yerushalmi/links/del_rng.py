import django
django.setup()
from sefaria.model import *

def yerushalmi(ref):
    return ref.book.startswith('Jerusalem Talmud')

def rnged(ref):
    return ref.is_range() or not ref.is_segment_level()

def halakhot(ref):
    return ref.context_ref().is_range()

def big(ref):
    return len(ref.all_segment_refs()) > 3

def long(ref):
    return len(' '.join(ref.text('he', vtitle='Mechon-Mamre').text).split()) > 300 or any(len(t) > 100 for t in ref.text('he', vtitle='Mechon-Mamre').text)

x=0
for link in LinkSet({'generated_by': 'yerushalmi tables'}):
    refs = [Ref(ref) for ref in link.refs]
    if all(yerushalmi(ref) for ref in refs):
        if all(rnged(ref) for ref in refs):
            print(1, refs)
            link.delete()
            x+=1
        elif all(not rnged(ref) for ref in refs):
            continue
        else:
            ref = [ref for ref in refs if rnged(ref)][0]
            if halakhot(ref):
                print(2, refs)
                link.delete()
                x += 1
            elif big(ref):
                print(3, refs)
                link.delete()
                x += 1
            elif long(ref):
                link.delete()
                print(4, refs)
                x+=1
print(x)
