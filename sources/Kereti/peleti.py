import csv
import django
django.setup()
import re
dhs_dict = {}
dhs_dict_2d = {}
from sefaria.model import *
from i_tags import *
from kereti import *
with open("Peleti.csv") as csv_f:
    for row in csv.reader(csv_f):
        if row[0].startswith("Shulchan Arukh, Yoreh De'ah"):
            ref, text = row
            ref = Ref(ref)
            text = text.decode('utf-8')
            if not re.search(u"~\[[\u05d0-\u05EA]+\]", text):
                continue
            mod_text = re.sub(u"~\[[\u05d0-\u05EA]+\]", u"$", text)
            mod_text = mod_text[mod_text.find("$"):]
            dhs = mod_text.split("$")[1:]
            dhs = [u" ".join(dh.strip().split()[:3]) for dh in dhs]
            if ref.sections[0] not in dhs_dict:
                dhs_dict[ref.sections[0]] = []
                dhs_dict_2d[ref.sections[0]] = {}
            dhs_dict[ref.sections[0]] += dhs
            dhs_dict_2d[ref.sections[0]][ref.sections[1]] = dhs

def create_links(post=False):
    links = []
    title = "Peleti"
    for siman in dhs_dict_2d.keys():
        running_total_per_siman = 0
        for seif in dhs_dict_2d[siman].keys():
            for n in range(len(dhs_dict_2d[siman][seif])):
                kereti_ref = "{} on Shulchan Arukh, Yoreh De'ah {}:{}".format(title, siman, n + 1 + running_total_per_siman)
                base_ref = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
                inline_info = {
                    "data-order": n + 1 + running_total_per_siman,
                    "data-commentator": title
                }
                links.append({"inline_reference": inline_info, "refs": [base_ref, kereti_ref], "type": "Commentary", "auto": True,
                          "generated_by": "mechaber_kereti"})
            running_total_per_siman += len(dhs_dict_2d[siman][seif])
    if post:
        post_link(links)

running_tests = eval(sys.argv[1])

if not running_tests:
    create_links(True)
    get_comm_text("Peleti", True)
    comm_dhs = get_kereti_tags("Peleti", dhs_dict_2d)
    default = "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888"
    create_new_tags("Dec 22 Peleti",  default, comm_dhs, change_nothing=False)
else:
    peleti_text = get_comm_text("Peleti")
    print "Siman #,Number of Peleti Tags,Number of Peleti Comments"
    for siman in dhs_dict.keys():
        num_tags_base = len(dhs_dict[siman])
        num_peleti_comments = len(peleti_text[siman-1])

        if abs(num_tags_base-num_peleti_comments) > 0:
            print "{},{},{}".format(siman,num_tags_base,num_peleti_comments)