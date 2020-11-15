from sources.functions import *
ls = LinkSet({"refs": {"$regex": "^Netivot Olam"}})
print(ls.count())
links = []
for l in ls:
    if l.generated_by != "add_links_from_text":
        links.append(l.contents())
print(len(links))
post_link(links, server="https://www.sefaria.org")