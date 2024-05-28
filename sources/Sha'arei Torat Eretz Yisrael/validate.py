import sefaria.system.exceptions
from sources.functions import *
from sefaria.helper.link import rebuild_links_for_title as rebuild
from sefaria.utils.hebrew import strip_cantillation, strip_nikkud

def base_tokenizer(line):
    return [strip_nikkud(x) for x in line.split()]

def dher(line):
    line = line.replace('ד"ה', '').strip()
    if "<b>" in line:
        pos = line.find("<b>")
        end_pos = line.find("</b>")
        poss_dhs = [x.strip() for x in line[pos+3:end_pos].split("וכו'")]
        longest_dh = poss_dhs[0]
        for x in poss_dhs:
            if len(x) > len(longest_dh):
                longest_dh = x
        return longest_dh
    else:
        return ""

def make_index(masechet, type):
    root = JaggedArrayNode()
    book = library.get_index(masechet)
    seder = book.categories[-1]
    print(seder)
    he_title = book.get_title('he')
    root.key = f"Sha'arei Torat Bavel on {masechet}"
    root.add_primary_titles(f"Sha'arei Torat Bavel on {masechet}", f"שערי תורת בבל על " + he_title)
    root.add_structure(["Daf", "Comment"], address_types=["Talmud", "Integer"]) if type != "Mishnah" else root.add_structure(["Chapter", "Mishnah", "Comment"])
    if type != "Mishnah" or seder == "Minor Tractates":
        category = ["Talmud", "Bavli", "Acharonim on Talmud", t.name, seder]
    else:
        category = ["Mishnah", "Acharonim on Mishnah", t.name, seder]
    if Category().load({"path": category}) is None:
        c = Category()
        c.path = category
        c.add_shared_term(seder)
        c.save()

    indx = {"title": root.key, "schema": root.serialize(), "categories": category, "collective_title": "Sha'arei Torat Bavel", "dependence": "Commentary",
            "base_text_titles": [masechet]}

    try:
        Index(indx).save()
    except:
        pass


def save_text(masechet, refs):

    # tc = TextChunk(Ref(f"Sha'arei Torat Bavel on {masechet}"), lang='he', vtitle="Jerusalem, 1961")
    # tc.text = text
    # tc.save()
    probs = []
    text = defaultdict(list)
    text_type = defaultdict(list)
    orig = defaultdict(list)
    for l, ref in enumerate(refs):
        if ref.type == "Mishnah":
            first_bold = ref.row[2].find("<b>")
            if first_bold > -1 and "@22" in ref.row[2]:
                assert ref.row[2].startswith("@22")
                line = "("+ref.row[2][3:first_bold].strip() + ") " + ref.row[2][first_bold:].strip()
                ref.row[2] = line
            if ref.reference.sections[0] not in text:
                text[ref.reference.sections[0]] = defaultdict(list)
            if len(ref.reference.sections) == 1:
                result = match_ref(ref.reference.text('he'), [line], base_tokenizer=base_tokenizer, dh_extract_method=dher)
                if result['matches'] == [None]:
                    ref.reference.sections.append(1)
                else:
                    ref.reference.sections.append(result["matches"][0].sections[1])

            if ref.reference.sections[1] not in text[ref.reference.sections[0]]:
                text[ref.reference.sections[0]][ref.reference.sections[1]].append(line)

        else:
            first_bold = ref.row[2].find("<b>")
            if first_bold > -1 and "@22" in ref.row[2]:
                assert ref.row[2].startswith("@22")
                line = "("+ref.row[2][3:first_bold].strip() + ") " + ref.row[2][first_bold:].strip()
                ref.row[2] = line
            else:
                line = ref.row[2]
            text[ref.reference.sections[0]].append(line)
            text_type[ref.reference.sections[0]].append(ref.type)
            orig[ref.reference.sections[0]].append(ref.row[1])
    tc = TextChunk(Ref(f"Sha'arei Torat Bavel on {masechet}"), lang='he', vtitle='Jerusalem, 1961')
    if refs[0].type == "Mishnah":
        for k in text:
            text[k] = convertDictToArray(text[k])

    text = convertDictToArray(text)
    text_type = convertDictToArray(text_type)
    orig = convertDictToArray(orig)
    tc.text = text
    tc.save()
    found = Counter()
    if refs[0].type == "Mishnah":
        rebuild(f"Sha'arei Torat Bavel on {masechet}", 1)
    else:
        links = []
        go_two_back = False
        for ref in refs:
            base_ref = ref.reference.normal()
            shaarei_ref = base_ref.replace(" on ", "").replace(ref.type, "").strip()
            found[shaarei_ref] += 1
            if ref.prev_sham and found[shaarei_ref] > 1:
                if shaarei_ref in links[-1]['refs'][1]:
                    this_ref = Ref(f"Sha'arei Torat Bavel on {shaarei_ref}:{found[shaarei_ref]}")
                    links[-1]['refs'][0] = Ref(links[-1]['refs'][0])
                    links[-1]['refs'][0] = links[-1]['refs'][0].to(this_ref).normal()
                    if go_two_back:
                        links[-2]['refs'][0] = Ref(links[-2]['refs'][0])
                        links[-2]['refs'][0] = links[-2]['refs'][0].to(this_ref).normal()
            else:
                new_links = match_ref_interface(base_ref, f"Sha'arei Torat Bavel on {shaarei_ref}:{found[shaarei_ref]}",
                                            [ref.row[2]], base_tokenizer=base_tokenizer, dh_extract_method=dher)
                links += new_links
                if len(new_links) > 0:
                    if ref.type != "Talmud":
                        talmud_ref = Ref(new_links[0]['refs'][1]).section_ref().normal().replace(ref.type, "").replace(" on ", "").strip()
                        generated_by = new_links[0]["generated_by"].replace(ref.type, "").replace(" on ", "").strip()
                        talmud_link = {"refs": [new_links[0]['refs'][0], talmud_ref], "generated_by": generated_by, "type": "Commentary", "auto": True}
                        links.append(talmud_link)
                        go_two_back = True
                    else:
                        go_two_back = False
        # for d, daf in enumerate(text_type):
        #     if daf == []:
        #         continue
        #     for t, type in enumerate(text_type[d]):
        #         if type == "Talmud":
        #             base_ref = f"{masechet} {AddressTalmud(0).toStr('en', d+1)}"
        #         elif type == "Rif":
        #             base_ref = f"Rif {masechet} {AddressTalmud(0).toStr('en', d+1)}"
        #         else:
        #             base_ref = f"{type} on {masechet} {AddressTalmud(0).toStr('en', d+1)}"
        #
        #         try:
        #             new_links = match_ref_interface(base_ref,f"Sha'arei Torat Bavel on {masechet} {AddressTalmud(0).toStr('en', d+1)}:{t+1}",[text[d][t]], base_tokenizer=base_tokenizer, dh_extract_method=dher)
        #             if len(new_links) == 0:
        #                 probs.append(["NO MATCH", base_ref, text[d][t], orig[d]])
        #             else:
        #                 if type == "Talmud":
        #                     probs.append([new_links[0]['refs'][1], base_ref, text[d][t], orig[d]])
        #                 else:
        #                     probs.append([new_links[0]['refs'][1], base_ref, text[d][t], orig[d]])
        #                     talmud_ref = Ref(new_links[0]['refs'][1]).section_ref().normal().replace(type, "").replace(" on ", "").strip()
        #                     generated_by = new_links[0]["generated_by"].replace(type, "").replace(" on ", "").strip()
        #                     talmud_link = {"refs": [new_links[0]['refs'][0], talmud_ref], "generated_by": generated_by, "type": "Commentary", "auto": True}
        #                     links.append(talmud_link)
        #                 links += new_links
        #         except:
        #             probs.append(["NO MATCH", base_ref, text[d][t], orig[d]])

        for l in links:
            try:
                Link(l).save()
            except:
                pass
    return probs



def get_daf_amud(daf, amud):
    amud = amud.replace('ע"', '')
    amud = ord(amud)
    if amud == ord('ב'):
        amud = 'b'
    elif amud - ord('ב') == -1:
        amud = "a"
    else:
        raise Exception
    daf = getGematria(daf)
    return (daf, amud)

class ShaareiRef:
    def __init__(self, masechet, type, reference, prev_one, r, prev_sham):
        self.masechet = masechet
        self.type = type  # Rashi, Tosafot, Talmud, Mishnah
        self.reference = reference
        self.prev_one = prev_one
        self.row = r
        self.prev_sham = prev_sham

def get_type(masechet, ref, prev_one, r):
    orig_ref = ref
    ref = ref.replace("""סופ""", 'פ"').replace('ספ"', 'פ"').replace('רפ"', 'פ"').replace('ספי"א', 'פי"א').replace('רפכ"ה', 'פכ"ה')
    ref = ref.replace("""משנה רפ"ד""", '').replace('משנה שהמלך', '').replace('משנה', '').replace('פי ברמב"ם', '').replace("""פי' ברמב"ם""", '')
    ref = ref.replace('סוף', '').replace('ישנים', '').replace('ר"ש', '').replace('פירוש', '')
    ref = ref.replace('פרק ', 'פ"').replace('“', '"').replace('יו"ד', 'י')
    ref = ref.replace("  ", " ").strip()
    ref = ref.replace('\'', '').strip()
    if (ref.startswith('פ') and ref.find('דף') == -1 and ref.split()[0].find('"') > 0): #or (ref.startswith('פ') and ref.count(" ") <= 1 and len(ref.split()[0]) > 1):
        type = "Mishnah"
        if ref.find(' מ') > 0:
            mishnah_pos = ref.find(' מ')
            ref = f"{ref[:mishnah_pos]} {ref[mishnah_pos:].strip().split()[0]}"
        elif ref.count(" ") > 1:
            ref
    elif ref.startswith('מ"'):
        type = "Mishnah"
        ref = prev_one.reference + " " + ref
    elif 'רש"י' in ref or 'המיוחס לרש"י' in ref or 'בפירש"י' in ref:
        type = "Rashi"
        ref = re.sub('.{0,1}פי.{0,1}', '', ref)
        ref = ref.replace('המיוחס לרש"י', '').replace('בפירש"י', '').replace('רש"י', '').strip()
    elif 'רשב"ם' in ref:
        type = "Rashbam"
        ref = ref.replace('רשב"ם', '').strip()
    elif 'תוס' in ref:
        type = "Tosafot"
        ref = ref.replace('תוספות', '').replace("תוס", '').strip()
    elif 'רי"ף' in ref:
        type = "Rif"
        ref = ref.replace('רי"ף', '').replace('ברי"ף', '')
    elif 'ר"נ' in ref:
        type = "Ran"
        ref = ref.replace('ר"נ', '')
    else:
        type = "Talmud"

    if re.search('דף' + ' \S{1,} \S{1,}', orig_ref):
        ref = re.search('דף' + ' \S{1,} \S{1,}', orig_ref).group(0).replace('דף', '').strip()
    if prev_one and ('שם' in ref or ref.strip() == ""):
        ref = prev_one.reference
        type = prev_one.type
        return (type, ref, True)
    ref = ref.strip()
    ref = ref.replace('סע"', 'ע"').replace('רע"', 'ע"')
    if ref.count(' ') > 1:
        ref = prev_one.reference
        type = prev_one.type
    return (type, ref, False)
all_refs = []
refs_by_masechet = defaultdict(list)
bad_rows = []
# with open("Sha'are Torath Babel _ Mishnah and Talmud - Mishnah and Talmud.csv", 'r') as f:
t = Term()
t.name = "Sha'arei Torat Bavel"
t.add_primary_titles(t.name, f"שערי תורת בבל")
try:
    t.save()
except:
    pass
c = Category()
c.path = ["Talmud", "Bavli", "Acharonim on Talmud", t.name]
c.add_shared_term(t.name)
try:
    c.save()
except:
    pass
c = Category()
c.path = ["Mishnah", "Acharonim on Mishnah", t.name]
c.add_shared_term(t.name)
try:
    c.save()
except:
    pass
probs = []
with open("new.csv", 'r') as f:
    rows = list(csv.reader(f))
    prev_one = None
    first_one = None
    curr_masechet = ""
    for r, row in enumerate(rows[1:]):
        masechet, ref, text, _ = row
        masechet = masechet.replace('בכורים', 'ביכורים')
        if masechet != '':
            curr_masechet = masechet
            try:
                curr_masechet_ref = Ref(masechet).index
                curr_masechet_ref = curr_masechet_ref.title
            except:
                print(masechet)
                curr_masechet_ref = None
        if curr_masechet_ref:
            if prev_one and curr_masechet_ref != prev_one.masechet:
                prev_one = None
            type, reference, prev_sham = get_type(curr_masechet_ref, ref, prev_one, r)
            this_one = ShaareiRef(curr_masechet_ref, type, reference, prev_one, row, prev_sham)
            if prev_one:
                prev_one.next_one = this_one
            prev_one = this_one
            if first_one is None:
                first_one = this_one
            all_refs.append(this_one)
            refs_by_masechet[curr_masechet_ref].append(this_one)

    for r, each_ref in enumerate(all_refs):
        ref = each_ref.reference
        type = each_ref.type
        try:
            if type == "Mishnah":
                if ref.count(' ') == 0:
                    ref = ref.replace('פ', '')
                    perek = getGematria(ref)
                    each_ref.reference = Ref(f"{each_ref.masechet} {perek}")
                else:
                    perek, mishnah = ref.split()[0], ref.split()[1]
                    perek = perek.replace('פ', '')
                    mishnah = mishnah.replace('מ', '')
                    mishnah = getGematria(mishnah)
                    perek = getGematria(perek)
                    each_ref.reference = Ref(f"{each_ref.masechet} {perek}:{mishnah}")
            else:
                ref = ref.replace('דע"', '').replace('ע"', '')
                daf, amud = ref.split()[0], ref.split()[1]
                daf, amud = get_daf_amud(daf, amud)
                if type == "Talmud":
                    each_ref.reference = Ref(f"{each_ref.masechet} {daf}{amud}")
                else:
                    try:
                        each_ref.reference = Ref(f"{type} on {each_ref.masechet} {daf}{amud}")
                    except:
                        each_ref.reference = Ref(f"{type} {each_ref.masechet} {daf}{amud}")
        except (sefaria.system.exceptions.InputError, IndexError) as e:
            print(e)
            print(type, each_ref.masechet, each_ref.row)

    for masechet in refs_by_masechet:
        print("Parsing ", masechet)
        for each_ref in refs_by_masechet[masechet][:-1]:
            try:
                assert each_ref.reference.sections
            except:
                print(f"Not a ref: {each_ref.row[1]}")
                continue
            try:
                assert each_ref.next_one.reference.sections
            except:
                print(f"Not a ref: {each_ref.next_one.row[1]}")
                continue
            if len(each_ref.reference.sections) == 1:
                curr_sections = each_ref.reference.sections[0]
                next_sections = each_ref.next_one.reference.sections[0]
            else:
                curr_sections = each_ref.reference.sections[0]*100
                next_sections = each_ref.next_one.reference.sections[0]*100
                curr_sections += each_ref.reference.sections[1] if len(each_ref.reference.sections) > 1 else 1
                next_sections += each_ref.next_one.reference.sections[1] if len(each_ref.next_one.reference.sections) > 1 else 1
            try:
                assert next_sections >= curr_sections
            except AssertionError:
                bad_rows.append([masechet, each_ref.row[1], each_ref.next_one.row[1]])
        make_index(masechet, refs_by_masechet[masechet][0].type)
        probs += save_text(masechet, refs_by_masechet[masechet])

with open("matches for sha'arei torat bavel.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(probs)
with open("validation problems.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(bad_rows)

for b in IndexSet({"collective_title": "Sha'arei Torat Bavel"}):
    for v in b.versionSet():
        v.versionSource = "https://www.nli.org.il/he/books/NNL_ALEPH990020673150205171/NLI"
        v.save()
    VersionState(index=b).refresh()
