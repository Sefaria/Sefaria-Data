import django
django.setup()
from sefaria.model import *
if __name__ == "__main__":
    i = library.get_index("Minchat Chinukh")
    i.dependence = "Commentary"
    i.base_text_titles = ["Sefer HaChinukh"]
    i.categories = ["Halakhah", "Commentary"]
    i.save()
    minchat_ls = LinkSet({"$and": [{"refs": {"$regex": "^Minchat Chinukh"}}, {"refs": {"$regex": "^Sefer HaChinukh"}}]})
    for l in minchat_ls:
        minchat_ref = 0 if l.refs[0].startswith("Minch") else 1
        sefer_ref = l.refs[0] if l.refs[0].startswith("Sefer") else l.refs[1]
        is_seg = Ref(sefer_ref).is_segment_level()
        if is_seg:
            minchat_ref = Ref(l.refs[minchat_ref]).as_ranged_segment_ref().normal()
            l.refs = [sefer_ref, minchat_ref]
            l.save()
