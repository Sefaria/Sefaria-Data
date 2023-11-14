from sources.functions import *
from bs4 import BeautifulSoup

def check_all_sections(links):
    sections = set()
    for l in links:
        sec = l.refs[1].split(" ")[-1].split(":")[0]
        sections.add(sec)
    assert len(sections) == 1

def link_sorter(x):
    x = x.refs
    return int(x[1].split(" ")[-1].split(":")[-1])

for b in ["Derush Al HaTorah", "Derashat Shabbat HaGadol"]:
    comm = library.get_index(f"Notes by Rabbi Yehoshua Hartman on {b}")
    comm.collective_title = "Notes by Rabbi Yehoshua Hartman"
    comm.dependence = "Commentary"
    comm.base_text_titles = [b]
    comm.save()
    b = library.get_index(b)
    b.versionState().refresh()
    for r in b.all_segment_refs():
        links = LinkSet({"$and": [{"refs": {"$regex": f"Notes by Rabbi Yehoshua Hartman on {b.title}"}},
                                  {"refs": r.normal()}]})
        tags = re.findall("<i.*?</i>", r.text('he').text)
        try:
            assert len(links) == len(tags)
        except:
            print(r)
            continue
        if len(links) == 0:
            continue
        labels = []
        for i_tag in tags:
            i = BeautifulSoup(i_tag)
            labels.append(int(i.find('i').attrs['data-label']))
        assert labels == sorted(labels)
        check_all_sections(links)
        links = sorted(list(links), key=link_sorter)
        prev_ref = 0
        for l, label in zip(links, labels):
            ref = int([x for x in l.refs if x.startswith("Notes")][0].split(" ")[-1].split(":")[-1])
            assert ref > prev_ref
            prev_ref = ref
            l.inline_reference = {"data-commentator": "Notes by Rabbi Yehoshua Hartman", "data-order": label}
            print(l.inline_reference)
            l.save()


#
# inline_reference: {
# data-commentator: "Turei Zahav",
# data-label: 1
# },