from sources.functions import *

prev_ref = ""
prev_comm = ""
ftnotes_text = {}
base_text = {}
links = []
with open("Ahavat Chesed.csv", 'r') as f:
    for row in csv.reader(f):
        ref, comment, ftnotes = row
        if len(ftnotes) > 0:
            ref = prev_ref
            comment = prev_comm
            match = re.search("^\((.{1,6})\) (.*?)$", ftnotes)
            indicator, ftnote = match.group(1), match.group(2)
            if indicator.startswith("*"):
                ftnote = "<sup>{}</sup><i class='footnote'>{}</i>".format(indicator, ftnote)
                comment = comment.replace("~({})".format(indicator), ftnote, 1)
            else:
                placeholder = "~({})".format(indicator)
                data_order = str(getGematria(indicator))
                i_tag = "<i data-commentator='Netiv Chesed' data-order='{}'></i>".format(data_order)
                assert len(comment.split(placeholder)) == 2
                comment = comment.replace(placeholder, i_tag)
                if ":" in ref:
                    comm_ref = "Netiv Chesed on {}".format(ref.split(":")[0])
                else:
                    comm_ref = "Netiv Chesed on {}".format(" ".join(ref.split()[:-1]))
                if comm_ref not in ftnotes_text:
                    ftnotes_text[comm_ref] = []
                assert getGematria(indicator) == len(ftnotes_text[comm_ref]) + 1
                ftnotes_text[comm_ref].append(ftnote)
                joiner = ":" if comm_ref[-1].isdigit() else " "
                comm_seg_ref = "{}{}{}".format(comm_ref, joiner, len(ftnotes_text[comm_ref]))
                links.append({"generated_by": "Netiv_to_Ahavat", "type": "Commentary", "auto": True,
                              "refs": [ref, comm_seg_ref], "inline_reference": {"data-order": data_order,
                                                                                "data-commentator": "Netiv Chesed"}})
        prev_ref = ref
        prev_comm = comment
        base_text[ref] = comment

post_link(links)
with open("ahavat_chesed_modified.csv", 'w') as f:
    writer = csv.writer(f)
    for ref, comment in base_text.items():
        send_text = {
            "language": "he",
            "versionTitle": "Ahavat Chesed -- Torat Emet",
            "versionSource": "http://toratemetfreeware.com/online/f_01815.html",
            "text": comment
        }
        post_text(ref, send_text)



with open("netiv_chesed_modified.csv", 'w') as f:
    writer = csv.writer(f)
    for ref, comments in ftnotes_text.items():
        for c, comment in enumerate(comments):
            segment = "{}:{}".format(ref, c+1) if "Introduction" not in ref else "{} {}".format(ref, c+1)
            writer.writerow([segment, comment])