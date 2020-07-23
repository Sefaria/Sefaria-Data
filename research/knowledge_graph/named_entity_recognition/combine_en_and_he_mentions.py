import srsly, json, django, re, csv
django.setup()
from collections import defaultdict
from sefaria.model import *
from tqdm import tqdm

DATA_LOC = "/home/nss/sefaria/datasets/ner/michael-sperling"

def combine():
    total_he = 0
    total_combined = 0
    he_data = srsly.read_jsonl(f"{DATA_LOC}/he_mentions.jsonl")
    en_data = srsly.read_jsonl(f"{DATA_LOC}/en_mentions.jsonl")
    he_ref_map = defaultdict(list)
    en_ref_map = defaultdict(list)
    for he_row in he_data:
        he_ref_map[he_row["Ref"]] += [he_row]
    for en_row in en_data:
        en_ref_map[en_row["Ref"]] += [en_row]
    combined_data = []
    missing_data = []
    for tref, he_rows in he_ref_map.items():
        en_rows = en_ref_map[he_rows[0]["Ref"]]
        he_ids = {int(he_row["Bonayich ID"]) for he_row in he_rows}
        new_row = {
            "Book": he_rows[0]["Book"], "Ref": he_rows[0]["Ref"],
            "He Mentions": [{"Start": he_row["Start"], "End": he_row["End"], "Bonayich ID": int(he_row["Bonayich ID"]), "Mention": he_row["Mention"]} for he_row in he_rows],
            "En Mentions": [{"Start": en_row["Start"], "End": en_row["End"], "Bonayich ID": int(en_row["Bonayich ID"]) if en_row["Bonayich ID"] is not None else None, "Mention": en_row["Mention"]} for en_row in en_rows],
        }
        new_row["En Mentions Filtered"] = list(filter(lambda x: x["Bonayich ID"] in he_ids, new_row["En Mentions"]))
        en_filtered_ids = {int(he_row["Bonayich ID"]) for he_row in new_row["En Mentions Filtered"]}
        new_row["He Mentions Filtered"] = list(filter(lambda x: x["Bonayich ID"] in en_filtered_ids, new_row["He Mentions"]))
        total_he += len(new_row["He Mentions"])
        total_combined += len(new_row["En Mentions Filtered"])
        if len(new_row["He Mentions"]) > len(new_row["En Mentions Filtered"]):
            missing_data += [new_row]
        combined_data += [new_row]
    srsly.write_jsonl(f"{DATA_LOC}/combined_mentions.jsonl", combined_data)
    with open(f"{DATA_LOC}/missing_mentions.jsonl", "w") as fout:
        json.dump(missing_data, fout, ensure_ascii=False, indent=2)
    print(total_he, total_combined)

def add_links(mentions, text, bon2sef):
    linked_text = ""
    mentions.sort(key=lambda x: x["Start"])
    dummy_char = "$"
    char_list = list(text)
    rabbi_dict = {}
    for m in mentions:
        rabbi_dict[m["Start"]] = (text[m["Start"]:m["End"]], bon2sef.get(m["Bonayich ID"], None))
        char_list[m["Start"]:m["End"]] = list(dummy_char*(m["End"]-m["Start"]))
    dummy_text = "".join(char_list)
    
    # assert len(dummy_text) == len(text), f"DUMMY {dummy_text}\nREAL {text}"

    def repl(match):
        mention, slug = rabbi_dict[match.start()]
        return f"""<a href="https://www.sefaria.org/topics/{slug}" class="{"missing" if slug is None else "found"}">{mention}</a>"""
    linked_text = re.sub(r"\$+", repl, dummy_text)
    return linked_text

def make_html_output(mas, rows, bon2sef):
    html = """
    <html>
        <head>
            <style>
                body {
                    width: 700px;
                    margin-right: auto;
                    margin-bottom: 50px;
                    margin-top: 50px;
                    margin-left: auto;
                }
                .he {
                    direction: rtl;
                }
                .missing {
                    color: red;
                }
                .found {
                    color: green;
                }
            </style>
        </head>
        <body>
    """
    for row in tqdm(rows):
        oref = Ref(row["Ref"])
        he_text = oref.text("he", vtitle="William Davidson Edition - Aramaic").text
        en_text = oref.text("en", vtitle="William Davidson Edition - English").text
        he_linked = add_links(row["He Mentions Filtered"], he_text, bon2sef)
        en_linked = add_links(row["En Mentions Filtered"], en_text, bon2sef)
        html += f"""
            <p class="he">{he_linked}</p>
            <p>{en_linked}</p>
        """
    html += """
        </body>
    </html>
    """
    with open(f"{DATA_LOC}/html/{mas}_combined_mentions.html", "w") as fout:
        fout.write(html)

if __name__ == "__main__":
    combine()
    with open("research/knowledge_graph/named_entity_recognition/sefaria_bonayich_reconciliation - Sheet2.csv", "r") as fin:
        rows = list(csv.DictReader(fin))
        bon2sef = {
            int(r["bonayich"]): r["Slug"] for r in rows if r["bonayich"] != "null"
        }
    combined_data = srsly.read_jsonl(f"{DATA_LOC}/combined_mentions.jsonl")
    by_mas = defaultdict(list)
    for row in combined_data:
        oref = Ref(row["Ref"])
        by_mas[oref.index.title] += [row]
    mas = "Berakhot"
    make_html_output(mas, by_mas[mas], bon2sef)
    
# Add Beit Hillel and Beit Shammai
