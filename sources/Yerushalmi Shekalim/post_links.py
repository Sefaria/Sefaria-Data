from sources.functions import *

files = [open("yerushalmi_comms_-_Korban_HaEidah_links.csv", 'r'), open("yerushalmi_comms_-_Pnei_Moshe_links.csv", 'r')]
links = []
for i, f in enumerate(files):
    reader = csv.reader(f)
    for row in reader:
        comm_ref, base_ref = row
        comm_ref = comm_ref.replace("Pnei", "Penei")
        links.append({"refs": [comm_ref, base_ref], "generated_by": "korban_pnei_moshe_to_yerushalmi",
                      "auto": True, "type": "Commentary"})

post_link_in_steps(links, server="https://yonitest.cauldron.sefaria.org")

