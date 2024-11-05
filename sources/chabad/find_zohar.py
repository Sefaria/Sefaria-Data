from sources.functions import *
import difflib
def add_mapping(node, mapping, node_title):
    start = addresser.toNumber('en', node['startingAddress'])
    for r, ref in enumerate(node['refs']):
        this_number = start + r + 1
        this_page = addresser.toStr('he', this_number)
        mapping[node_title][this_page] = ref

url = "http://127.0.0.1:5000/predict"

headers = {
    'Content-Type': 'application/json',
}
vols = library.get_index("Zohar").alt_structs["Daf"]["nodes"]
addresser = AddressTalmud(0)
mapping = defaultdict(dict)
whole_mapping = defaultdict(list)
for vol in vols:
    for node in vol["nodes"]:
        node_title = [x['text'] for x in node['titles'] if x['lang'] == 'he'][0]
        if node.get('startingAddress') is not None:
            add_mapping(node, mapping, node_title)
            whole_mapping[node_title].append(node["wholeRef"])
        else:
            for subnode in node["nodes"]:
                add_mapping(subnode, mapping, node_title)
                whole_mapping[node_title].append(subnode["wholeRef"])

he_zohar_parshiot = [x.get_primary_title('he') for x in library.get_index("Zohar").nodes.children]
found_refs_daf = []
found_refs_parasha = []
existing = []
try:
    existing = list(open('results.csv', 'r'))
except FileNotFoundError:
    pass

with open("results.csv", "a") as csvfile:
    writer = csv.writer(csvfile)
    for title in tqdm(["Likkutei Torah", "Torah Ohr", "Derekh Mitzvotekha"]):
        for r, ref in enumerate(library.get_index(title).all_segment_refs()):
            # if ref.normal() != "Torah Ohr, Lech Lecha 4:1":
            #     continue
            if ref.normal() in str(existing):
                continue
            if r % 50 == 0:
                print(ref)
                writer.writerows(found_refs_daf)
                writer.writerows(found_refs_parasha)
                found_refs_daf = []
                found_refs_parasha = []
            text = bleach.clean(ref.text('he').text, strip=True, tags=[])
            data = {"text": text}
            if "בזהר " not in text and "בזוהר " not in text:
                found_refs_daf.append((ref.normal(), "", ""))
            else:
                response = requests.post(url, json=data, headers=headers)
                response = json.loads(response.content)
                if 'error' in response:
                    print(response)
                    found_refs_daf.append((ref.normal(), "", ""))
                elif response.get('result', {}) == []:
                    found_refs_daf.append((ref.normal(), "", ""))
                else:
                    print(response)
                    found_something = False
                    for citation, result in response['result'].items():
                        this_parasha = result.get('parasha')
                        found_parasha = ""
                        if this_parasha in he_zohar_parshiot:
                            found_parasha = this_parasha
                        else:
                            closest_match = difflib.get_close_matches(this_parasha, he_zohar_parshiot, n=1)
                            if closest_match:
                                found_parasha = closest_match[0]
                        this_daf = result.get('daf')
                        if len(found_parasha) > 0:
                            if this_daf:
                                matches = difflib.get_close_matches(this_daf, list(mapping[found_parasha].keys()), n=1)
                                if len(matches) > 0:
                                    this_daf = matches[0]
                                    zohar_ref = mapping[found_parasha][this_daf]
                                    found_refs_daf.append((ref.normal(), zohar_ref, result.get('dh'), citation))
                                    found_something = True
                            else:
                                for zohar_ref in whole_mapping[found_parasha]:
                                    found_refs_parasha.append((ref.normal(), zohar_ref, result.get('dh'), citation))
                                    found_something = True
                    if not found_something:
                        found_refs_daf.append((ref.normal(), "", ""))

    writer.writerows(found_refs_daf)
    writer.writerows(found_refs_parasha)

