from sources.functions import *
ref = "Ohev Ger, Part II, Variants in Targum Onkelos"
parshiyot = {}
def dher(str):
    str = str.replace("<b></b><br>", "")
    return " ".join(str.split()[:3])

with open("ohev_ger.csv", 'r') as f:
    found_parasha = ""
    for row in csv.reader(f):
        if row[0].startswith(ref):
            parasha = re.search("<b>(פרשת .*?)</b><br>", row[1])
            if parasha:
                try:
                    found_parasha = Ref(parasha.group(1))
                except:
                    found_parasha = parasha.group(1).replace("זאת הברכה", "וזאת הברכה").replace("ואתה תצוה", "תצוה").replace("בחקותי", "בחוקתי")
                    found_parasha = Ref(found_parasha)
                print(found_parasha)
                parshiyot[found_parasha] = [row[1].replace(parasha.group(1), "")]
            else:
                parshiyot[found_parasha].append(row[1])

def replace_torah_with_targum(l):
    i = 1 if l["refs"][0].startswith("Ohev Ger") else 0
    comm_title = Ref(l["refs"][i]).index.title
    l["refs"][i] = l["refs"][i].replace(comm_title, "Targum Onkelos {}".format(comm_title))
    return l

links = []
how_many_comments = 0
for i, parasha in enumerate(parshiyot):
    base = TextChunk(parasha, vtitle="Tanach with Text Only", lang='he')
    comments = parshiyot[parasha]
    matches = match_ref(base, comments, base_tokenizer=lambda x: x.split(), dh_extract_method=dher)
    for n, match in enumerate(matches["matches"]):
        len_match_text = len(matches["match_text"][n][0]) + len(matches["match_text"][n][1])
        if match and len_match_text > 4:
            curr_base_ref = match.normal()
            curr_comm_ref = "{} {}:1".format(ref, n+how_many_comments+1)
            new_link = {"refs": [curr_comm_ref, curr_base_ref], "generated_by": "Ohev_Ger_to_Torah",
                        "type": "Commentary", "auto": True}
            links.append(new_link)
    how_many_comments += len(comments)

# post_link(links)
targum_links = [replace_torah_with_targum(l) for l in links]
post_link(targum_links, server="https://www.sefaria.org")