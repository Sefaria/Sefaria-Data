from sources.functions import *
import threading
import time

#delete Genesis links, post Genesis links
def process_links(links, generated_by="", auto=True, type="Commentary"):
    db_format_links = {0: []}
    counter = 0
    buckets = 4
    for link in links:
        counter += 1
        bucket = counter % buckets
        if bucket not in db_format_links:
            db_format_links[bucket] = []
        refs = [link["sourceRef"], link["anchorRef"]]
        db_format_links[bucket].append({"refs": refs, "generated_by": generated_by, "auto": auto, "type": type})
    db_format_links = convertDictToArray(db_format_links)
    return db_format_links


class Eliyah(threading.Thread):
    def __init__(self, name, links, server):
        threading.Thread.__init__(self)
        self.name = name
        self.links = links
        self.server = server

    def run(self):
        curr = 0
        inc = 200
        while curr < len(self.links):
            curr_links = self.links[curr:inc+curr]
            curr += inc
            print(self.name)
            result = post_link(curr_links, self.server)
            time.sleep(curr)

get_server = "https://eliyah-rabbah.cauldron.sefaria.org"
post_server = "https://www.sefaria.org"

orig_links = get_links("Minchat Chinukh", server=get_server)
print(len(orig_links))
link_groups = process_links(orig_links, generated_by="eliyah_rabbah")
link_posters = []
for link_group in link_groups:
    link_posters.append(Eliyah(link_group[0]["refs"][1], link_group, post_server))
for lp in link_posters:
    lp.start()
print("DONE")
