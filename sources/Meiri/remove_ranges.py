import django
django.setup()
from sefaria.model import *
ls = LinkSet({"refs": {"$regex": "^Meiri on"}})
i = 0
for l in ls:
    i += 1
    if i % 100 == 0:
        print(i)
    talmud_digit = 0 if l.refs[1].startswith("Meiri") else 1
    talmud_ref = l.refs[talmud_digit]
    meiri_ref = l.refs[1-talmud_digit]
    talmud_ref = Ref(talmud_ref)
    talmud_index = talmud_ref.index.title
    if talmud_ref.index.get_primary_category() == "Talmud" and talmud_ref.is_range():
        this_link_set = LinkSet({"$and": [{"refs": meiri_ref}, {"refs": {"$regex": "^{}".format(talmud_index)}}]})
        if this_link_set.count() > 1:
            for i, sub_l in enumerate(this_link_set.array()):
                talmud_digit = 0 if sub_l.refs[1].startswith("Meiri") else 1
                talmud_ref = sub_l.refs[talmud_digit]
                if Ref(talmud_ref).is_range():
                    sub_l.delete()
                    break


