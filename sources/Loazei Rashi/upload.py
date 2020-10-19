from sources.functions import *
import csv
f = open("comment,ref.csv", 'w')
writer = csv.writer(f)
def reformat(comment, book, curr_pos):
    comment = comment.replace("<b></b>", "")
    lines = comment.split("<br>")
    lines[0] = lines[0].strip()
    lines[1] = lines[1].strip()
    hebrew = re.search("<b>.*?</b>", lines[0]).group(0)
    lines[0] = lines[0].replace(hebrew, "").strip()
    line_zero_parts = lines[0].split()
    serial = line_zero_parts[0]
    ref = "({})".format(" ".join(line_zero_parts[1:])).strip()
    definition = re.search("<b>.*?</b>", lines[1])
    definition = definition.group(0).strip() if definition else ""
    lines[1] = lines[1].replace(definition, "").strip()
    en_french = re.search("[a-zA-Z\]\[ ]{2,}", lines[1])
    en_french = en_french.group(0).strip() if en_french else ""
    he_french = lines[1].replace(en_french, "").strip()

    first_line = "{} / {} / {}<br>".format(serial, ref, hebrew)
    second_line = ""
    if he_french:
        second_line += he_french
    else:
        print("ERROR french")
    if en_french:
        second_line += " / " + en_french
    if definition:
        second_line += " / " + definition
    second_line += "<br>"
    second_line = second_line.replace("/  /", "/")
    first_line = first_line.replace("/  /", "/")
    full_thing = first_line+second_line+lines[2]
    if re.search("\/[ ]+\/", full_thing):
        print("ERROR /  /")

    if len(full_thing.split(" / ")) < 5:
        writer.writerow(["https://ste.cauldron.sefaria.org/Otzar_Laazei_Rashi,_Talmud,_{}.{}".format(book.replace(" ", "_"), curr_pos+1), comment])
    return full_thing


def get_data(file, type):
    links = []
    books = {}
    book = ""
    for row in list(csv.reader(file))[1:]:
        comm_ref = Ref(row[0]).normal()
        if " on " in comm_ref:
            base_ref = ":".join(comm_ref.split(" on ")[-1].split(":")[:-1])
            book = Ref(base_ref).book
            if book not in books:
                books[book] = []

        otzar_ref = "Otzar Laazei Rashi, {}, {} {}".format(type, book, len(books[book])+1)
        if " on " in comm_ref:
            links.append({"generated_by": "loazei_rashi", "refs": [comm_ref, otzar_ref],
                          "type": "Commentary", "auto": True})
            base_ref = comm_ref
            while len(base_ref.split(":")) > 2:
                base_ref = ":".join(comm_ref.split(" on ")[-1].split(":")[:-1])
            links.append({"generated_by": "loazei_rashi", "refs": [base_ref, otzar_ref],
                          "type": "Commentary", "auto": True})
        else:
            #comm_ref is a base_ref
            assert len(comm_ref.split(":")) == 2
            base_ref = comm_ref
            links.append({"generated_by": "loazei_rashi", "refs": [base_ref, otzar_ref],
                          "type": "Commentary", "auto": True})

        if type == "Tanakh":
            try:
                serial, ref, hebrew, french_he, french_en, definition, comm_2 = row[1].split("@")
            except ValueError as e:
                if "not enough" in str(e) and "6" in str(e):
                    serial, ref, hebrew, french_he, french_en, definition = row[1].split("@")
                else:
                    print(row[1])
                continue
            first_line = "{} / ({}) / <b>{}</b><br>".format(serial, ref, hebrew)
            second_line = "{} / {} / <b>{}</b><br>".format(french_he, french_en, definition)
            third_line = "<small>{}</small>".format(comm_2) if comm_2 else ""
            comment = first_line + second_line + third_line
            if len(comment.split(" / ")) < 5:
                print()
        else:
            comment = reformat(row[1], book, len(books[book]))

        comment = re.sub("\$\n?", "", comment).replace("#", "")

        books[book].append(comment)
    return books, links


data = {"Talmud": [], "Tanakh": []}
with open("Laazei_complete_-_Talmud.csv") as talmud:
    data["Talmud"] = get_data(talmud, "Talmud")

with open("Laazei_complete_-_Tanakh.csv") as torah:
    data["Tanakh"] = get_data(torah, "Tanakh")


root = SchemaNode()
root.add_primary_titles("Otzar Laazei Rashi", """אוצר לעזי רש"י""")
tanakh = SchemaNode()
tanakh.add_shared_term("Tanakh")
tanakh.key = "Tanakh"
for book in library.get_indexes_in_category("Tanakh"):
    if book in data["Tanakh"][0]:
        tanakh_child = JaggedArrayNode()
        tanakh_child.add_structure(["Paragraph"])
        tanakh_child.add_primary_titles(book, library.get_index(book).get_title('he'))
        tanakh_child.key = book
        tanakh.append(tanakh_child)

talmud = JaggedArrayNode()
talmud.add_shared_term("Talmud")
talmud.add_structure(["Paragraph"])
talmud.key = "Talmud"

for book in library.get_indexes_in_category("Talmud"):
    if book in data["Talmud"][0]:
        tanakh_child = JaggedArrayNode()
        tanakh_child.add_structure(["Paragraph"])
        tanakh_child.add_primary_titles(book, library.get_index(book).get_title('he'))
        tanakh_child.key = book
        talmud.append(tanakh_child)

root.append(talmud)
root.append(tanakh)
root.validate()
# post_index({
#     "title": "Otzar Laazei Rashi",
#     "schema": root.serialize(),
#     "categories": ["Reference"]
# })
#
for type in ["Tanakh", "Talmud"]:
    for book, comments in data[type][0].items():
        send_text = {
            "versionTitle": "Otzar Laazei Rashi, Jerusalem, 1988",
            "language": "he",
            "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001066968/NLI",
            "text": comments
        }
        #post_text("Otzar Laazei Rashi, {}, {}".format(type, book), send_text)

links = data["Tanakh"][1] + data["Talmud"][1]
for l in range(0,5200,400):
    print(l)
    post_link(links[l:400+l], server="https://www.sefaria.org")

