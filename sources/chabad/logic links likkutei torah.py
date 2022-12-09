import csv
from sources.functions import *
from collections import Counter
from sefaria.model.schema import AddressFolio
from sefaria.utils.hebrew import *
from sefaria.system.database import db
from django.contrib.auth.models import User

def create_logic_links(lines):
    prev_ref = None
    logic_links = []
    pad = 0
    logic_links = [""]*len(lines)
    for l, line in enumerate(lines):
        start = l
        dh, ref, comm, seg = lines[start]
        orig_ref = ref
        pad = 0
        while ref == "":
            pad += 1
            ref = lines[pad+l][1]
        if prev_ref == ref and orig_ref == "":
            while pad != 0:
                pad -= 1
                logic_links[start+pad] = prev_ref
        if orig_ref != "":
            prev_ref = orig_ref
    return [[x[0][0], x[0][1], x[0][2], x[0][3], x[1]] for x in list(zip(lines, logic_links))]

def get_ranged_links(lines, title):
    found_ref = None
    parasha = None
    # every consecutive match, we extend the range
    prev_parasha = None
    start_ref = end_ref = None
    links = []
    ref = ""
    segment_count = Counter()
    prev_matched_ref = ""
    for l, line in enumerate(lines):
        dh, matched_ref, comm, seg = line
        seg = seg.replace(" ", "")
        if len(matched_ref) == 0 or matched_ref != prev_matched_ref:
            if start_ref and end_ref:
                if already_posted:
                    links.append({"refs": [Ref(start_ref).to(Ref(end_ref)).normal(), prev_matched_ref], "type": "Commentary",
                              "generated_by": "likkutei_torah_torah_ohr_script", "auto": True, })
            start_ref = None
            segment_count[ref] += 1
        elif len(matched_ref) > 0:
            parasha = Ref(matched_ref).index_node.get_primary_title('en')
            parts = seg.split(",")
            daf = 4 * (heb_string_to_int(parts[0]) - 1) + heb_string_to_int(parts[1])
            ref = f"{title}, {parasha} {daf}"
            segment_count[ref] += 1
            end_ref = f"{ref}:{segment_count[ref]}"
            if start_ref is None:
                start_ref = end_ref
        prev_parasha = parasha
        prev_matched_ref = matched_ref
    return links


if __name__ == "__main__":
    already_posted = True
    root = SchemaNode()
    title = "Sources and References on Likkutei Torah"
    root.add_primary_titles(title, "מראי מקומות הערות וציונים לליקוטי תורה")

    text = defaultdict(list)
    parshiyot = []
    with open("Likkutei Torah Main Text.csv", 'r') as f:
        f_lines = list(csv.reader(f))
        ranged_links = get_ranged_links(f_lines, title)
        lines = create_logic_links(f_lines)

    if already_posted:
        for link in ranged_links:
            Link(link).save()
    for l, line in enumerate(lines):
        dh, matched_ref, comm, seg, logic_ref = line
        seg = seg.replace(" ", "")
        found_ref = matched_ref if len(matched_ref) != 0 else logic_ref
        if len(found_ref) > 0:
            parasha = Ref(found_ref).index_node.get_primary_title('en')
        if parasha not in text:
            node = JaggedArrayNode()
            node.add_structure(["Daf", "Paragraph"])
            he_parasha = Term().load({"titles.text": parasha}).get_primary_title('he')
            parshiyot.append([parasha, he_parasha])
            node.add_primary_titles(parasha, he_parasha)
            root.append(node)
            text[parasha] = {}
        if seg not in text[parasha]:
            text[parasha][seg] = []
        text[parasha][seg].append(f"<b>{dh}</b> {comm}")

    curr_alt_struct = {}
    nodes = []
    duplicates = set()
    parasha_ranges = defaultdict(list)
    send_text_dict = {}
    for parasha in text:
        for seg in text[parasha]: # 1,1 = 1; 1,2 = 2; 2,1 = 5
            parts = seg.split(",")
            daf = 4*(heb_string_to_int(parts[0])-1) + heb_string_to_int(parts[1])
            print(daf)
            ref = f"{title}, {parasha} {daf}"
            parasha_ranges[parasha].append(ref)
            assert ref not in duplicates
            duplicates.add(ref)
            print(ref)
            send_text = {
                "versionTitle": "NLI",
                "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002082151",
                "language": "he",
                "text": text[parasha][seg]
            }
            send_text_dict[ref] = send_text
            prev_seg = seg

    if already_posted:
        for en, he in parshiyot:
            node = ArrayMapNode()
            node.add_primary_titles(en, he)
            node.add_structure(["Daf", "Paragraph"], address_types=["Folio", "Integer"])
            node.depth = 2
            node.wholeRef = Ref(parasha_ranges[en][0]).to(Ref(parasha_ranges[en][-1])).normal()
            node.refs = parasha_ranges[en]
            nodes.append(node.serialize())
        curr_alt_struct["Daf"] = {"nodes": nodes}
        index_dict = {"title": title, "schema": root.serialize(), "categories": ["Chasidut", "Early Works"], 'alt_structs': curr_alt_struct,
                      "default_struct": "Daf"}
    else:
        index_dict = {"title": title, "schema": root.serialize(), "categories": ["Chasidut", "Early Works"], "default_struct": "Daf"}

    # library.get_index(title).delete()
    post_index(index_dict, server="http://localhost:8000")
    for ref in send_text_dict:
        if not already_posted:
            post_text(ref, send_text_dict[ref])
    total = len(lines)
    bad = 0
    with open("Likkutei Torah Main Text with Logic Links.csv", 'w') as f:
        writer = csv.writer(f)
        for line in lines:
            if line[1] == line[2] == "":
                bad += 1
            writer.writerow(line)
    print(bad)
    print(total)
    #
    # with open("Likkutei Torah Main Text.csv", 'r') as f:
    #     create_logic_links(f)
