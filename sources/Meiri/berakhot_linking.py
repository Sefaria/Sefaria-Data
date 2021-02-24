from sources.functions import *
from sources.Meiri.parse_RP import ScoreManager, PM_regular, dher

en_title = "Eruvin"
full_title = "Meiri on {}".format(en_title)

lines_in_title = {}
eruvin_file = "Chidushei HaMeiri on Eruvin - he - Chidushei HaMeiri on Eruvin, Warsaw 1914.csv"
berakhot_file = "Meiri on Berakhot - he - Wikisource.csv"
with open(eruvin_file, 'r') as f:
    for row in csv.reader(f):
        if full_title in row[0] and "Introduction" not in row[0]:
            daf = row[0].split()[-1].split(":")[0]
            if daf not in lines_in_title:
                lines_in_title[daf] = []
            lines_in_title[daf].append(row[1])

mishnah = "משנה"
found_refs = []
links = []
score_manager = ScoreManager("RP/word_count.json")

for actual_daf in lines_in_title:
    comm_title = "{} {}".format(full_title, actual_daf)
    base_ref = "{} {}".format(en_title, actual_daf)
    found = -1
    leave = False
    #get positions of base and comm that are Mishnah
    positions_comm = [l for l, line in enumerate(lines_in_title[actual_daf]) if mishnah in line.split()[0]]
    base = Ref("{} {}".format(en_title, actual_daf)).text('he')
    positions_base = [l for l, line in enumerate(base.text) if
                      "מַתְנִי׳" in line.split()[0] or "מתני׳" in line.split()[0] or "המשנה" in line.split()[0]]
    # base = Ref("{} {}".format(en_title, actual_daf)).text('en')
    # positions_base = [l for l, line in enumerate(base.text) if
    #                   "MISHNA:" in line]
    for base, comm in zip(positions_base, positions_comm):
        print("Mishnah")
        found_refs.append("Meiri on {} {}:{}".format(en_title, actual_daf, comm + 1))
        links.append({"generated_by": "mishnah_to_meiri", "auto": True, "type": "Commentary",
                      "refs": ["Meiri on {} {}:{}".format(en_title, actual_daf, comm + 1),
                               "{} {}:{}".format(en_title, actual_daf, base + 1)]})
    if len(positions_base) != len(positions_comm) > 0:
        print("Meiri on {} {}".format(en_title, actual_daf))

    with open("{}.csv".format(en_title), 'w') as f:
        writer = csv.writer(f)
        links += PM_regular(lines_in_title[daf], comm_title, base_ref, writer, score_manager)
        links += match_ref_interface(base_ref, comm_title, lines_in_title[daf], lambda x: x.split(), dher,
                                    generated_by="meiri_to_daf")

with open("{}_links_he.json".format(en_title), 'w') as f:
    json.dump(links, f)
