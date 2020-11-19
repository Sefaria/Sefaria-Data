from sources.functions import *
links = []
with open("find_query.csv", 'r') as f:
    for row in csv.reader(f):
        refs = sorted(row)
        if refs[0].startswith("Footnotes") and refs[1].startswith("Gevurot"):
            links.append({"refs": refs, "generated_by": "Footnotes_to_Gevurot", "auto": True, "type": "Commentary"})
print(len(links))
print(links[0:10])
post_link(links, server="https://www.sefaria.org")