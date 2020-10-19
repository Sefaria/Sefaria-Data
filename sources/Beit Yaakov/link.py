from sources.functions import *
def dher(str):
    match = re.search("<b>(.*?)</b>", str)
    if match:
        return match.group(1).replace(" וגו", "").replace("'", "").replace(".", "")
    else:
        return ""

with open("beit.csv", 'r') as f:
    text = {}
    for row in csv.reader(f):
        if row[0].startswith("Beit Yaakov"):
            ref, comment = row
            section, segment = ref.split()[-1].split(":")
            book = " ".join(ref.split()[:-1]).replace("Beit Yaakov on Torah, ", "")
            section = int(section)
            segment = int(segment)
            if book not in text:
                text[book] = {}
            if section not in text[book]:
                text[book][section] = {}
            if segment not in text[book][section]:
                text[book][section][segment] = ""
            text[book][section][segment] = comment


links = []
for book in text:
    for section in text[book]:
        text[book][section] = convertDictToArray(text[book][section])
    text[book] = convertDictToArray(text[book])
    vtitle = "Tanach with Text Only"
    for i, section in enumerate(text[book]):
        base = TextChunk(Ref("Parashat "+book), lang='he', vtitle=vtitle)
        matches = match_ref(base, section, base_tokenizer=lambda x: x.split(), dh_extract_method=dher)["matches"]
        how_many = [m for m in matches if m]
        if len(how_many) == 1:
            torah_ref = how_many[0].normal()
            end = len(matches)
            section_ref = "Beit Yaakov on Torah, {} {}:1-{}".format(book, i+1, end)
            links.append({"refs": [torah_ref, section_ref], "generated_by": "{}_to_BeitYaakov".format(book),
                          "type": "Commentary", "auto": True})
        elif len(how_many) == 0:
            pass


post_link(links)