from sources.functions import *
essays = defaultdict(list)
subessays = defaultdict(dict)
order_essays = []
with open("essay contents/essays.csv") as f:
    for row in csv.reader(f):
        book, num, comm = row
        book = book.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "")
        essays[book].append(comm)
        if book not in order_essays:
            order_essays.append(book)
subessays = json.load(open("essay contents/subessays.json", 'r'))
other_subessays = json.load(open("essay contents/subessays_full.json", 'r'))
subessays["The Primeval History"] = other_subessays["I: the Primeval History"]
order = {"Genesis": order_essays[1:7], "Exodus": order_essays[7:15], "Leviticus": order_essays[15:23], "Numbers": order_essays[23:28], "Deuteronomy": order_essays[28:-1]}
text = json.load(open("text.json", 'r'))
book_text = defaultdict(dict)
for b in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_text[b] = defaultdict(dict)
for ref in text:
    book, perek, pasuk = ref.split()
    perek = int(perek)
    pasuk = int(pasuk)
    if perek not in book_text[book]:
        book_text[book][perek] = defaultdict(str)
    book_text[book][perek][pasuk] = text[ref]
for book in book_text:
    for perek in book_text[book]:
        book_text[book][perek] = convertDictToArray(book_text[book][perek])
    book_text[book] = convertDictToArray(book_text[book])

del subessays["The Patriarchal Narratives"]
new_sub_essays = {}
for k in subessays.keys():
    new_k = k.replace("Iv: ", "").replace("Iii: ", "").replace("Ii: ", "").replace("Vi: ", "").replace("V: ", "")
    new_sub_essays[new_k] = subessays[k]
subessays = new_sub_essays
root = SchemaNode()
essay_heb = "מאמר"
comment_heb = "הערה"
root.add_primary_titles("Everett Fox on Torah", "אברט פוקס על תורה")
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_node = SchemaNode()
    book_node.add_primary_titles(book, library.get_index(book).get_title('he'))
    default = JaggedArrayNode()
    default.key = "default"
    default.default = True
    default.add_structure(["Chapter", "Verse"])
    book_node.append(default)
    for i, essay in enumerate(order[book]):
        if essay in subessays:
            schemanode = SchemaNode()
            schemanode.add_primary_titles(essay, f"{library.get_index(book).get_title('he')} {essay_heb} {encode_hebrew_numeral(i + 1)}")
            default = JaggedArrayNode()
            default.default = True
            default.key = "default"
            default.add_structure(["Paragraph"])
            schemanode.append(default)
            for j, subessay in enumerate(subessays[essay]):
                node = JaggedArrayNode()
                node.add_structure(["Paragraph"])
                node.depth = 1
                node.add_primary_titles(subessay.replace("On Bil\u2019am", "On Bil'am").replace(':', ';'), f"{library.get_index(book).get_title('he')} {comment_heb} {encode_hebrew_numeral(j+1)}")
                schemanode.append(node)
            schemanode.validate()
            book_node.append(schemanode)
        else:
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.depth = 1
            node.add_primary_titles(essay.replace(':', ';'), f"{library.get_index(book).get_title('he')} {essay_heb} {encode_hebrew_numeral(i+1)}")
            book_node.append(node)
            node.validate()
    root.append(book_node)

root.validate()
t = Term()
t.name = "Everett Fox"
t.add_primary_titles(t.name, "אברט פוקס")
#t.save()
t = Term().load({"name": "Everett Fox"})
post_term(t.contents(), server="http://localhost:8000")
indx = {"title": "Everett Fox on Torah", "schema": root.serialize(), "categories": ["Tanakh", "Modern Commentary on Tanakh"], "dependence": "Commentary",
        "collective_title": "Everett Fox", "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]}
post_index(indx, server="http://localhost:8000")
vtitle = "Everett Fox"
send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
subessay_links = []
calls = {}
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    send_text["text"] = book_text[book]
    calls[f"Everett Fox on Torah, {book}"] = send_text
    post_text(book, send_text, server="http://localhost:8000")
    for i, essay in enumerate(order[book]):
        essay = essay.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "").replace("Vi: ", "").replace("V: ", "")
        if essay in subessays:
            for j, subessay in enumerate(subessays[essay]):
                Ref(subessays[essay][subessay][0])

                send_text["text"] = subessays[essay][subessay][1:]
                he_display = f"{library.get_index(book).get_title('he')} {comment_heb} {encode_hebrew_numeral(j+1)}"
                subessay_links.append({"refs": [f"Everett Fox on Torah, {book}, {essay}, {subessay.replace(':', ';')}", subessays[essay][subessay][0]],
                                       "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links", "versions": [{"title": "NONE"},
                                                                                                                              {"title": vtitle,
                                                                                                                               "language": "en"}],
                                       "displayedText": {"en": subessay.replace(':', ';'), "he": he_display}})
                #Link(subessay_links[-1]).save()

                calls[f"Everett Fox on Torah, {book}, {essay}, {subessay.replace(':', ';')}"] = send_text

        if re.search("^\([0-9:]{1,5}[-–]{1}[0-9:]{1,5}\)$", essays[essay][0]):
            send_text["text"] = essays[essay][1:]
            essays[essay] = essays[essay][0].replace("(", "("+book+" ")
        else:
            send_text["text"] = essays[essay]
            essays[essay] = ""

        calls[f"Everett Fox on Torah, {book}, {essay}"] = send_text

# post_first = True
# if post_first:
#     for ref in calls:
#         post_text(ref, calls[ref], server="http://localhost:8000")
#
essay_links = []
essays["Avraham"] = "(Genesis 12:1-25:18)"
essays["Yaakov"] = "(Genesis 25:19-36:43)"
del essays["Torah, Introduction, To Aid the Reader of Genesis and Exodus"]
del essays["Suggestions For Further Reading"]
essays['Historical Overview'] = '(Deuteronomy 1:1–4:43)'
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    for i, essay in enumerate(order[book]):
        if essay in essays:
            if essays[essay] == "":
                print(f"No link for {essay} in {book}")
            else:
                he_display = f"{library.get_index(book).get_title('he')} {essay_heb} {encode_hebrew_numeral(i + 1)}"
                tanakh_ref = Ref(essays[essay][1:-1]).as_ranged_segment_ref().normal()
                try:
                    everett_ref = Ref(f"Everett Fox on Torah, {book}, {essay}").as_ranged_segment_ref().normal()
                except:
                    ref = Ref(f"Everett Fox on Torah, {book}, {essay}")
                    everett_ref = ref.normal() + " 1-" + str(len(ref.text('en').text))
                print(everett_ref)
                essay_links.append(({"refs": [tanakh_ref, everett_ref],
                                       "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links", "versions": [{"title": vtitle,
                                                                                                                               "language": "en"},
                                                                                                                              {"title": "NONE"}],
                                       "displayedText": {"en": essay, "he": he_display}}))
links = get_links("Genesis 1:1", server="http://localhost:8000")
post_link(essay_links, server="http://localhost:8000")
post_link(subessay_links, server="http://localhost:8000")



for ref in calls:
    post_text(ref, calls[ref], server="http://localhost:8000")