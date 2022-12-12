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
    curr_parasha = ""
    for l, line in enumerate(lines):
        start = l
        curr_parasha, dh, ref, comm, seg = lines[start]
        orig_ref = ref
        pad = 0
        while ref == "" and l+pad < len(lines) - 1:
            pad += 1
            ref = lines[pad+l][2]
        if prev_ref == ref and orig_ref == "":
            while pad != 0:
                pad -= 1
                logic_links[start+pad] = prev_ref
        if orig_ref != "":
            prev_ref = orig_ref
    return [[x[0][0], x[0][1], x[0][2], x[0][3], x[0][4], x[1]] for x in list(zip(lines, logic_links))]


if __name__ == "__main__":
    already_posted = True

    root = SchemaNode()
    base = "Torah Ohr"
    he_title = "מראי מקומות הערות וציונים לתורה אור" if base == "Torah Ohr" else "מראי מקומות הערות וציונים לקוטי תורה"
    title = f"Sources and References on {base}"
    # if not already_posted:
    #     try:
    #         library.get_index(title).delete()
    #     except:
    #         pass
    library.rebuild_toc()
    root.add_primary_titles(title, he_title)

    text = defaultdict(list)
    parshiyot = []
    with open(f"{base} Main Text2.csv", 'r') as f:
        f_lines = list(csv.reader(f))
        lines = create_logic_links(f_lines)


    prev_integer_daf = 0
    curr_para = 0
    ranged_links = []
    parasha_ranges = defaultdict(dict)
    prev_parasha = curr_ref = ""
    prev_folio_daf = None
    new_parasha = True
    for l, line in enumerate(lines):
        parasha, dh, matched_ref, comm, seg, logic_ref = line
        term = Term().load({"titles.text": parasha})
        if term is None:
            term = Topic().load({"titles.text": parasha})
        try:
            parasha = term.get_primary_title('en').replace("Shmini Atzeret", "Shemini Atzeret").replace("Song of Songs", "Shir HaShirim")
        except:
            print(f"Warning regarding {parasha}")
        seg = seg.replace(" ", "")
        #found_ref = matched_ref if len(matched_ref) != 0 else logic_ref
        found_ref = matched_ref
        parts = seg.split(",")
        integer_daf = heb_string_to_int(parts[0])
        if integer_daf - prev_integer_daf not in [0, 1]:
            print(f"Warning: {prev_integer_daf} before {integer_daf}")
        folio_daf = daf = AddressFolio(0).toStr('en', 4*(heb_string_to_int(parts[0])-1) + heb_string_to_int(parts[1]))
        if integer_daf != prev_integer_daf:
            curr_para = 0
        if prev_folio_daf:
            diff_folio = AddressFolio(0).toNumber('en', folio_daf) - AddressFolio(0).toNumber('en', prev_folio_daf)
            while diff_folio > 1:
               parasha_ranges[parasha]["refs"].append("")
               diff_folio -= 1

        if parasha != prev_parasha and len(prev_parasha) > 0 and already_posted:
            start_ref = Ref(parasha_ranges[prev_parasha]["refs"][0])
            last_ref = Ref(curr_ref)
            curr_ref = ""
            parasha_ranges[prev_parasha]["wholeRef"] = start_ref.to(last_ref).normal()

        if parasha not in text:
            node = JaggedArrayNode()
            node.add_structure(["Daf", "Paragraph"])
            try:
                he_parasha = Term().load({"titles.text": parasha}).get_primary_title('he')
            except:
                print("Problem with "+parasha)
                if base == "Torah Ohr":
                    assert parasha == "Parashat Zakhor"
                    he_parasha = "פרשת זכור"
                if base == "Likkutei Torah":
                    if parasha == "Shabbat Shuvah":
                        he_parasha = "דרושים לשבת שובה"
                    elif parasha == "Shir HaShirim":
                        he_parasha = "דרושים לשמיני עצרת"
            parshiyot.append([parasha, he_parasha])
            node.add_primary_titles(parasha, he_parasha)
            root.append(node)
            text[parasha] = {}
            curr_para = 0
            parasha_ranges[parasha]["startingAddress"] = folio_daf

            parasha_ranges[parasha]["refs"] = []
            new_parasha = True
            if already_posted:
                curr_ref = Ref(f"{title}, {parasha} {integer_daf}:1").normal()
        else:
            new_parasha = False

        curr_para += 1

        if already_posted and not new_parasha:
            curr_ref = Ref(f"{title}, {parasha} {integer_daf}:{curr_para}").normal()

        if prev_folio_daf and folio_daf != prev_folio_daf and curr_ref != "" and curr_ref not in parasha_ranges[parasha]["refs"]:
            parasha_ranges[parasha]["refs"].append(curr_ref)





        if new_parasha and curr_ref != "" and curr_ref not in parasha_ranges[parasha]["refs"]:
            parasha_ranges[parasha]["refs"].append(curr_ref)

        prev_folio_daf = folio_daf


        if integer_daf not in text[parasha]:
            text[parasha][integer_daf] = []


        text[parasha][integer_daf].append(f"<b>{dh}</b> {comm}")
        if len(found_ref) > 0:
            ranged_links.append({"refs": [curr_ref, found_ref], "type": "Commentary",
                    "generated_by": "likkutei_torah_torah_ohr_script", "auto": True})
        prev_integer_daf = integer_daf
        prev_parasha = parasha

    if already_posted:
        start_ref = Ref(parasha_ranges[prev_parasha]["refs"][0])
        last_ref = Ref(curr_ref)
        parasha_ranges[prev_parasha]["wholeRef"] = start_ref.to(last_ref).normal()

    curr_alt_struct = {}
    nodes = []
    duplicates = set()

    root.validate()
    index_dict = {"title": title, "schema": root.serialize(), "categories": ["Chasidut", "Early Works"], "base_text_titles": [base],
                  "dependence": "Commentary"}

    if already_posted:
        for link in tqdm(ranged_links):
            try:
                Link(link).save()
            except Exception as e:
                print(e)

    if already_posted:
        for en, he in parshiyot:
            node = ArrayMapNode()
            node.add_primary_titles(en, he)
            node.add_structure(["Daf", "Paragraph"], address_types=["Folio", "Integer"])
            node.depth = 2
            node.wholeRef = parasha_ranges[en]["wholeRef"]
            node.refs = parasha_ranges[en]["refs"]
            node.startingAddress = parasha_ranges[en]["startingAddress"]
            nodes.append(node.serialize())
        curr_alt_struct["Daf"] = {"nodes": nodes}
        index_dict.update({'alt_structs': curr_alt_struct,
                      "default_struct": "Daf"})

    # library.get_index(title).delete()
    try:
        Index(index_dict).save()
    except Exception as e:
        post_index(index_dict, server="http://localhost:8000")

    if not already_posted:
        for parasha in text:
            for ref in text[parasha]:
                curr_ref = f"{title}, {parasha} {ref}"
                send_text = {
                    "versionTitle": "NLI",
                    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002082151",
                    "language": "he",
                    "text": text[parasha][ref]
                }
                tc = TextChunk(Ref(curr_ref), lang='he', vtitle="NLI")
                tc.text = text[parasha][ref]
                tc.save(force_save=True)

    total = len(lines)
    bad = 0
    with open("Torah Ohr Main Text with Logic Links2.csv", 'w') as f:
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
from sefaria.helper.schema import *
for title in ["Likkutei Torah", "Torah Ohr"]:
    comm_title = f"Sources and References on {title}"
    parent_node = library.get_index(comm_title).nodes
    last_node = library.get_index(title).nodes.children[-1]
    insert_last_child(last_node, parent_node)