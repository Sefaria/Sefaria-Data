from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import match_text

def dher(x):
    result = re.sub("<b>(.*?)</b>.*", "\g<1>", x).replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
    return bleach.clean(result, tags=[], strip=True)

def dher2(s):
    s = s.replace("… :", "").strip()
    poss = dher(s).split("…")[-1].strip()
    if poss == "":
        return dher(s).split("…")[0].strip()
    return poss


def dher3(s):
    return dher(s).split("…")[-1].strip()

new_rows = []
with open("The Early Prophets with Essays.csv", 'r') as f:
    curr_ref = ""
    for row in csv.reader(f):
        if re.search("^\d+:?\d* ", row[1]):# and row[0].rsplit(".")[0] in refs:
            curr_ref = row[0].rsplit(".")[0]
        elif row[0].rsplit(".")[0] != curr_ref and len(curr_ref) > 0:
            #print(curr_ref)
            curr_ref = ""
        if len(curr_ref) == 0:
            new_rows.append(row)

ftnotes_counter = {x: 1 for x in ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings"]}
new_text = defaultdict(list)
for r, row in enumerate(new_rows):
    ref = row[0].rsplit(".")[0]
    new_text[ref].append(row[1])

invalid_refs = []
short_refs = {}
essay_refs = {}
with open("essays.csv", 'w') as essay_f:
    essay_writer = csv.writer(essay_f)
    for k in new_text:
        for book in ["Joshua", "Judges", "Samuel", "Kings"]:
            if book in k and not re.search(f"The Early Prophets, {book}, \d+", k):
                for l, line in enumerate(new_text[k]):
                    essay_writer.writerow([k, l+1, line])
                poss_ref = new_text[k][0]
                if book in ["Samuel", "Kings"]:
                    m = re.search("\((.{,2}) (.*?)\)", poss_ref)
                    if m and len(poss_ref) < 50:
                        poss_ref = f"{m.group(1)} {book} {m.group(2)}".replace('–', "-")
                else:
                    m = re.search("\((.*?)\)", poss_ref)
                    if m and len(poss_ref) < 50:
                        poss_ref = f"{book} {m.group(1)}".replace('–', "-")
                if m and len(poss_ref) < 50:
                    assert poss_ref.find(":") == -1 or poss_ref.find(":") != poss_ref.rfind(":")
                    try:
                        norm_ref = Ref(poss_ref).as_ranged_segment_ref()
                        essay_refs[(norm_ref, k)] = []
                    except Exception as e:
                        print(poss_ref)

ftnotes = defaultdict(dict)
for b in ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings"]:
    ftnotes[b] = defaultdict(dict)
    for perek in library.get_index(b).all_section_refs():
        ftnotes[b][perek.sections[0]] = []

ftnote_perek = 1
found_essay = None
actual_text = {}
for k in new_text:
    for book in ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings"]:
        if re.search(f"The Early Prophets, {book}, \d+", k):
            actual_text[book] = []
            start_ftnotes = False
            # parse mini essays and footnotes
            for l, line in enumerate(new_text[k]):
                if line.find("____") == 0:
                    assert " " not in line
                    continue
                line = line.replace('–', '-')
                m = re.search("^Chapter ([\d:-]{1,6})\. (.{,50}):", line)
                if m:
                    ch = Ref(f"{book} {m.group(1)}")
                    title = m.group(2)
                # m = re.search("^<i>(.*?)</i>\s?(\(.*?\)): ", line)
                # ftnote_perek_match = re.search("^(\d+):.{,10} <b>(.*?)</b>", line)
                # second_word_bold = re.search("^<b>.*?</b>", " ".join(line.split()[1:])) if " " in line else False
                # text_match = re.search("^(\d+)", line)
                # if ftnote_perek_match:
                #     ftnote_perek = int(ftnote_perek_match.group(1))
                #     ftnotes[book][ftnote_perek].append(line)
                #     found_essay = None
                # elif line[0].isdigit() and second_word_bold:
                #     ftnotes[book][ftnote_perek].append(line)
                #     found_essay = None
                # elif text_match:
                #     actual_text[book].append(line)
                #     found_essay = None
                # elif m:
                #     title, ref = m.group(1), m.group(2)
                #     ref = ref.replace("(", "("+book+" ")
                #     ref = ref.replace('–', "-")

                if m:
                    try:
                        not_found = True
                        for essay in essay_refs.keys():
                            essay_ref, essay_title = essay
                            if essay_ref.contains(ch):
                                essay_refs[(essay_ref, essay_title)].append((ch.as_ranged_segment_ref(), title))
                                essay_refs[(essay_ref, essay_title)].append(line.replace(m.group(0), ""))
                                found_essay = (essay_ref, essay_title)
                                not_found = False
                        assert not_found is False
                    except Exception as e:
                        invalid_refs.append((title, ch))
                elif found_essay:
                    essay_refs[found_essay].append(line)
                else:
                    actual_text[book].append(line)

node = None
root = SchemaNode()
root.add_primary_titles("Everett Fox", "")

torah_books = [x for x in ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings"]]
subessays = defaultdict(dict)
with open("titles for translation prophets.csv", 'w') as translation_f:
    translation_writer = csv.writer(translation_f)
    for ref_title in essay_refs:
        ref, title = ref_title

        if node:
             root.append(node)
        node = SchemaNode()
        node.add_primary_titles(title, "")
        translation_writer.writerow([title, ""])
        ref = ref.normal()
        title = title.strip()
        i = 0
        for subpart in essay_refs[ref_title]:
            if isinstance(subpart, tuple):
                subref, subtitle = subpart
                subtitle = subtitle.strip()
                subessays[title][subtitle] = [subref.normal()]
                subref = subref.normal()
                subnode = JaggedArrayNode()
                subnode.depth = 1
                subnode.add_primary_titles(subtitle, "")
                subnode.add_structure(["Paragraph"])
                node.append(subnode)
                translation_writer.writerow([subtitle, ""])
                i = 0
            else:
                i += 1
                subpart = subpart.strip()
                subessays[title][subtitle].append(subpart)

json.dump(subessays, open("subessays_full_prophets.json", 'w'))
vtitle = ""
for invalid_ref in invalid_refs:
    title, ref = invalid_ref
    print(f"!!! {title} -> {ref}")

new_ftnotes = {}
ranged_ftnotes = []
for book in ftnotes:
    new_ftnotes[book] = defaultdict(list)
    for perek in ftnotes[book]:
        for line in ftnotes[book][perek]:
            if line[0].isdigit():
                ref = line.split()[0]
                if ":" not in ref:
                    ref = f"{perek}:{line.split()[0]}"
                ref = ref.replace("2:4b", "2:4").replace("/", "-").replace("ff.", "")
                ref = re.sub("(^\d+:\d+),(\d+)", "\g<1>-\g<2>", ref)
                if ref.endswith(",") or ref.endswith(":"):
                    ref = ref[:-1]
                try:
                    Ref(f"{book} {ref}")
                except:
                    print(f"{book} {ref}")
                if "-" in ref:
                    ranged_ftnotes.append(ref)
                line = ref + " " + " ".join(line.split()[1:])
                new_ftnotes[book][perek].append(line)
            else:
                new_ftnotes[book][perek][-1] += "<br/>"+line
print(ranged_ftnotes)
print(len(ranged_ftnotes))
with open("prophets_ftnotes_from_XML.csv", 'w') as f:
    writer = csv.writer(f)
    for book in new_ftnotes:
        for perek in new_ftnotes[book]:
            for line in new_ftnotes[book][perek]:
                writer.writerow([f"{book} {line}"])

