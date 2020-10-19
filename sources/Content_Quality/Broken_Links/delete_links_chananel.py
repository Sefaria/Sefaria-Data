import django
django.setup()
from sefaria.model import *
chananel = LinkSet({"refs": {"$regex": "^Rabbeinu Chananel on"}, "generated_by": {"$regex": "sterling"}})
nissim = LinkSet({"refs": {"$regex": "^Rav Nissim Gaon on"}, "generated_by": {"$regex": "sterling"}})
full_set = list(nissim)+list(chananel)
print(len(full_set))
for l in full_set:
    ghost = Ref(l.refs[0]).is_empty() or Ref(l.refs[1]).is_empty()
    if ghost:
        print(l.refs)
        l.delete()
chananel = LinkSet({"refs": {"$regex": "^Rabbeinu Chananel on"}, "generated_by": {"$regex": "sterling"}})
nissim = LinkSet({"refs": {"$regex": "^Rav Nissim Gaon on"}, "generated_by": {"$regex": "sterling"}})
print(len(full_set))
