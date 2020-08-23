from sources.functions import *
from bs4 import BeautifulSoup

def move_footnotes(old_ref, new_ref, old_ftnotes_dict, i_tags):
    ftnote_vol, ftnote_section, ftnote_segment = old_ref.split()[-1].split(":")
    old_ftnotes_list = old_ftnotes_dict["Footnotes and Annotations on Ohr Chadash {}:{}".format(ftnote_vol, ftnote_section)]
    i_tags = [BeautifulSoup(i_tag).find("i").attrs["data-label"] for i_tag in i_tags]
    old_ftnotes_list = [ftnote for ftnote in old_ftnotes_list if re.search("\((\d+)\)", ftnote).group(1) in i_tags]
    new_ref_section = new_ref.rsplit(":", 1)[0]
    assert ":" in new_ref_section
    ftnote_new_section = "Footnotes and Annotations on {}".format(new_ref_section)
    vol, section = [int(x) for x in new_ref_section.split()[-1].split(":")]
    if vol not in new_ftnotes:
        new_ftnotes[vol] = {}
    if section not in new_ftnotes[vol]:
        new_ftnotes[vol][section] = []
    new_ftnotes[vol][section] += old_ftnotes_list

old_ftnotes = {}
with open("Ohr Chadash/Footnotes.csv") as ftnote_f:
    for row in csv.reader(ftnote_f):
        if row[0].startswith("Footnotes and Annotations on Ohr Chadash,"):
            old_ftnotes[row[0]] = row[1]
        elif row[0].startswith("Footnotes and Annotations on Ohr Chadash "):
            ref = row[0].rsplit(":", 1)[0]
            if ref not in old_ftnotes:
                old_ftnotes[ref] = []
            old_ftnotes[ref].append(row[1])

with open("Ohr Chadash/Ohr Chadash.csv") as f:
    vol = perek = pasuk = 0
    using_col_c = False
    col_c_vol = col_c_perek = col_c_pasuk = 0
    text = {}
    new_ftnotes = {}

    with open("Ohr Chadash/Ohr Chadash New.csv", 'w') as new_f:
        writer = csv.writer(new_f)
        for row in csv.reader(f):
            if row[0].startswith("Ohr Chadash "):
                ref, comment, col_c = row
                default = [int(x) for x in ref.split()[-1].split(":")]
                if default[0] > col_c_vol or default[1] > col_c_perek:
                    col_c_vol = col_c_perek = col_c_pasuk = 0
                    using_col_c = False

                if col_c:
                    col_c_vol, col_c_perek = [int(x) for x in col_c.split(":")]
                    col_c_pasuk = 1
                    this_vol, this_perek, this_pasuk = col_c_vol, col_c_perek, col_c_pasuk
                    using_col_c = True
                elif using_col_c:
                    this_pasuk += 1
                else:
                    this_vol, this_perek, this_pasuk = default

                new_ref = "Ohr Chadash {}:{}:{}".format(this_vol, this_perek, this_pasuk)
                i_tags = re.findall("<i .*?></i>", comment)
                    # data = BeautifulSoup(i_tag).find("i")
                    # data = data.attrs
                    # comm = data["data-commentator"].replace("Index: ", "")
                    # order = data["data-label"]
                move_footnotes(ref, new_ref, old_ftnotes, i_tags)

                writer.writerow([new_ref, comment])

            else:
                writer.writerow(row)
with open("Ohr Chadash/New Footnotes.csv", 'w') as fp:
    writer = csv.writer(fp)
    for vol in sorted(new_ftnotes.keys()):
        for section in sorted(new_ftnotes[vol].keys()):
            for i, ftnote in enumerate(new_ftnotes[vol][section]):
                writer.writerow(["Footnotes and Annotations on Ohr Chadash {}:{}:{}".format(vol, section, i+1), ftnote])