from sources.functions import *
import json
import time
#links = get_links("Midrash Lekach Tov", "https://www.sefaria.org")
with open('../../../Downloads/links_midrash_lekach_tov', 'r') as f:
    links_f = json.load(f)
books = set()
links_to_post = []
data_comms = set()
#post_link("Midrash Lekach Tov", server="http://rosh.sandbox.sefaria.org/", method="DELETE")
for link in links_f:
    book = Ref(link["ref"]).index.title
    # anchor_book = link["anchorRef"].split(", ")[-1].split()[0]
    # if anchor_book == book:
    links_to_post.append({"refs": [link["ref"], link["anchorRef"]],
                      "generated_by": "post_rosh_midrash_lekach_links",
                      "auto": True, "type": "Commentary"})
    if book == 'Notes and Corrections on Midrash Lekach Tov' or book == "Beur HaRe'em on Midrash Lekach Tov":
        link["inline_reference"]["data-commentator"] = link["inline_reference"]["data-commentator"].split(" on ")[0]
        links_to_post[-1]["inline_reference"] = link["inline_reference"]
    if link["inline_reference"]:
        data_comms.add(link["inline_reference"]["data-commentator"])
print(data_comms)
counter = 1900
print(len(links_to_post))
while counter < len(links_to_post):
    amt = 400
    post_link(links_to_post[counter:counter+amt], server="https://www.sefaria.org")
    counter += amt
    print(counter)
    time.sleep(30)
