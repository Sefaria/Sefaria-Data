from sources.functions import *
from sefaria.model.schema import AddressFolio

def base_tokenizer(x):
    x = strip_nikkud(bleach.clean(x, strip=True, tags=[]))
    return x.split()

def dher(x):
    dh = x.split("#")[0].split('כו׳')[0].split("כו'")[0]
    if dh.endswith("."):
        dh = dh[:-1]
    return dh.strip().replace("@", "")

prev_row = []
probs = []
map_probs = []
def getVeniceMapping(halacha, curr_mapping, r, flag=False):
    match = re.findall("\((.*?)\)", halacha)
    if "פיסקא" in halacha:
        return curr_mapping
    if "בשורה" in halacha:
        return curr_mapping
    if "בסוף העמוד" in halacha:
        return curr_mapping
    if len(match) == 1:
        match = match[0]
        match = match.replace('״', '"')
        match = match.replace('דף', "").replace('יו"ד סוף', 'יו"ד').strip().split()
        if len(match) >= 2:
            daf = match[0]
            amud = match[1]
            if daf == 'יו״ד':
                daf = 10
            elif daf == 'סמ״ך':
                daf = 60
            else:
               daf = getGematria(daf)
            amud = getGematria(amud.split('"')[-1])
            assert amud < 10
            address = f"{daf}{chr(96 + amud)}"
            try:
               if not flag and AddressFolio(1).toNumber('en', address) < AddressFolio(1).toNumber('en', curr_mapping):
                   probs.append([f"Row # {r+1}", halacha, f"Previous # {prev_row[-1][1]+1}", prev_row[-1][0]])
            except:
                probs.append([f"Row # {r + 1}", halacha, f"Previous # {prev_row[-1][1]+1}", prev_row[-1][0]])
            prev_row.append((halacha, r))
            return address
    return curr_mapping

def merge_lists(list_A, list_B):
    result = []
    for a, b in zip(list_A, list_B):
        if a is not None:
            result.append(a)
        elif b is not None:
            result.append(b)
        else:
            result.append(None)
    return result

didnt_find = 0
found = 0
def update_masechet_and_perek(masechet, perek, curr_masechet, curr_perek, curr_halacha):
    if len(masechet) > 0:
        masechet = masechet.replace("$", "").replace('פיאה', 'פאה').replace('בכורים', "ביכורים")
        masechet = f"Jerusalem Talmud {Ref(masechet).index.title}"
        masechet = masechet.replace("Mishnah ", "")
        assert Ref(masechet).normal()
        texts[masechet][1] = defaultdict(defaultdict)
        return (masechet, 1, 1)
    elif len(perek) > 0:
        perek = perek.replace('פ', '')
        assert getGematria(perek) > curr_perek
        curr_perek = getGematria(perek)
        curr_halacha = 1
        texts[curr_masechet][curr_perek] = defaultdict(defaultdict)
    return (curr_masechet, curr_perek, curr_halacha)


def update_halacha(halacha, curr_halacha):
    matches = re.findall('ה״(.{1})', halacha)
    assert len(matches) in [0, 1]
    if len(matches) == 1:
        assert getGematria(matches[0]) >= curr_halacha
        curr_halacha = getGematria(matches[0])
    return curr_halacha
texts = defaultdict(defaultdict)
with open("sha'arei torat eretz yisrael - Sheet1 (1).csv", 'r') as f: #open("sha'arei torat eretz yisrael - Sheet1 (1).csv", 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)
    curr_perek = 1
    curr_masechet = ""
    curr_halacha = 0
    curr_mapping = "2a"
    for r, row in enumerate(rows):
        prev_halacha = curr_halacha
        masechet, perek, halacha, text = row[0], row[1], row[2], row[3] #, found_match, found_text = row
        curr_masechet, curr_perek, curr_halacha = update_masechet_and_perek(masechet, perek, curr_masechet, curr_perek, curr_halacha)
        curr_halacha = update_halacha(halacha, curr_halacha)
        curr_mapping = getVeniceMapping(halacha, curr_mapping, r, flag=prev_halacha > curr_halacha)
        if curr_mapping not in texts[curr_masechet][curr_perek][curr_halacha]:
            texts[curr_masechet][curr_perek][curr_halacha][curr_mapping] = []
        texts[curr_masechet][curr_perek][curr_halacha][curr_mapping].append(text)

full_info = []
text_based_on_link = {}
with open("out of order venice mapping.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(probs)

other_versions = ["Venice Edition", "The Jerusalem Talmud, edition by Heinrich W. Guggenheimer. Berlin, De Gruyter, 1999-2015", "Mechon-Mamre"]
for masechet in texts:
    for perek in texts[masechet]:
        for halacha in texts[masechet][perek]:
            """
             1. grab all text for masechet, perek, halacha
             2. divide it into  
            """
            tc = TextChunk(Ref(f"{masechet} {perek}:{halacha}"), lang='he', vtitle='Venice Edition')
            new_dict = {}
            for mapping in texts[masechet][perek][halacha]:
                our_num = AddressFolio(1).toNumber('en', mapping)
                nodes = library.get_index(masechet).alt_structs["Venice"]["nodes"]
                found = None
                for n, node in enumerate(nodes):
                    node_num = AddressFolio(1).toNumber('en', node['startingAddress'])
                    if our_num == node_num:
                        found = n
                        break
                    if our_num < node_num:
                        found = n - 1
                        break
                if found is None:
                    found = len(nodes) - 1
                index_to_use = our_num - AddressFolio(1).toNumber('en', nodes[found]['startingAddress'])
                try:
                    assert index_to_use >= 0
                    range = nodes[found]['refs'][index_to_use]
                except:
                    final_address = AddressFolio(1).toNumber('en', nodes[-1]['startingAddress'])+len(nodes[-1]['refs'])-1
                    final_address = AddressFolio.toStr('en', final_address)
                    map_probs.append([f"{masechet} {perek}:{halacha}", mapping, nodes[0]['startingAddress'], final_address,
                                      texts[masechet][perek][halacha][mapping]])
                new_dict[mapping] = range
            for mapping in texts[masechet][perek][halacha]:
                comms = texts[masechet][perek][halacha][mapping]
                final_results = []
                each_result = []
                for version in other_versions:
                    tc = TextChunk(Ref(new_dict[mapping]), lang='he', vtitle=version)
                    results = match_ref(tc, comms, base_tokenizer=base_tokenizer,
                              dh_extract_method=dher)
                    print(results['matches'])
                    each_result.append(results['matches'])
                    if None not in results['matches']:
                        break
                if None in results["matches"]:
                    print()
                temp = each_result[0]
                for x in each_result[1:]:
                    temp = merge_lists(temp, x)
                final = len([x for x in temp if x != None])
                orig = len([x for x in each_result[0] if x != None])
                texts[masechet][perek][halacha][mapping] = []
                for match, comment in zip(temp, comms):
                    if match:
                        masechet = match.book
                        first, second, third = match.sections
                        if masechet not in text_based_on_link:
                            text_based_on_link[masechet] = {}
                        if first not in text_based_on_link[masechet]:
                            text_based_on_link[masechet][first] = {}
                        if second not in text_based_on_link[masechet][first]:
                            text_based_on_link[masechet][first][second] = {}
                        if third not in text_based_on_link[masechet][first][second]:
                            text_based_on_link[masechet][first][second][third] = []
                        text_based_on_link[masechet][first][second][third].append(comment)
                        full_info.append([masechet, perek, halacha, mapping, comment, match.normal(), match.text('he').text])
                    else:
                        full_info.append([masechet, perek, halacha, mapping, comment])
                        texts[masechet][perek][halacha][mapping].append(comment)

with open("linked + unlinked hashlamot.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(full_info)
with open("unlinked texts hashlamot.json", 'w') as f:
    json.dump(texts, f)

with open("linked texts hashlamot.json", 'w') as f:
    json.dump(text_based_on_link, f)

with open("venice mapping not in text hashlamot.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Ref", "Expected Tag", "Start Tag", "End Tag", "CSV Text"])
    writer.writerows(map_probs)
