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
subessays["Part I; The Primeval History"] = other_subessays["I: the Primeval History"]
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
    book_text[book][perek][pasuk] = text[ref].replace("<small>YHWH</small>", "Y<small>HWH</small>").replace("•", "⦿")
for book in book_text:
    for perek in book_text[book]:
        book_text[book][perek] = convertDictToArray(book_text[book][perek])
    book_text[book] = convertDictToArray(book_text[book])



del subessays["The Patriarchal Narratives"]
new_sub_essays = {}
for k in subessays.keys():
    new_k = k#.replace("Iv: ", "").replace("Iii: ", "").replace("Ii: ", "").replace("Vi: ", "").replace("V: ", "")
    new_sub_essays[new_k] = subessays[k]
subessays = new_sub_essays
root = SchemaNode()
essay_heb = "מאמר"
comment_heb = "הערה"
root.add_primary_titles("The Five Books of Moses, by Everett Fox", "חמשה חומשי תורה, מהדורת אברט פוקס")
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_node = SchemaNode()
    book_node.add_primary_titles(book, library.get_index(book).get_title('he'))
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
try:
    t.save()
except:
    pass
t = Term().load({"name": "Everett Fox"})
post_term(t.contents(), server="http://localhost:8000")
indx = {"title": "The Five Books of Moses, by Everett Fox", "schema": root.serialize(), "categories": ["Tanakh", "Modern Commentary on Tanakh"], "dependence": "Commentary",
        "collective_title": "Everett Fox", "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]}
#post_index(indx, server="http://localhost:8000")
vtitle = "The Five Books of Moses, by Everett Fox"
subessay_links = []
calls = {}
essay_refs = {}

essays["Part II; Avraham"][0] = "Genesis 12:1-25:18"
essays["Part III; Yaakov"][0] = "Genesis 25:19-36:43"
essays['Part I; Historical Overview'][0] = 'Deuteronomy 1:1–4:43'
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
    send_text["text"] = book_text[book]
    assert len(book_text[book]) == len(library.get_index(book).all_section_refs())
    for p, perek in enumerate(book_text[book]):
        assert len(Ref(f"{book} {p+1}").all_segment_refs()) == len(book_text[book][p])
    post_text(book, send_text, server="http://localhost:8000")
    for i, essay in enumerate(order[book]):
        essay = essay #.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "").replace("Vi: ", "").replace("V: ", "")
        if essay in subessays:
            for j, subessay in enumerate(subessays[essay]):
                Ref(subessays[essay][subessay][0])
                everett = f"The Five Books of Moses, by Everett Fox, {book}, {essay}, {subessay.replace(':', ';')}"
                range = len(Ref(everett).text('en').text)
                everett = "{} 2-{}".format(everett, range) if range != 2 else "{} 2".format(everett)
                print(Ref(everett).text('en').text[0])
                he_display = f"{library.get_index(book).get_title('he')} {comment_heb} {encode_hebrew_numeral(j+1)}"
                he_tanakh = Ref(subessays[essay][subessay][0]).he_normal()
                subessay_links.append({"refs": [subessays[essay][subessay][0], everett],
                                       "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links",
                                       "versions": [{"title": vtitle,
                                                     "language": "en"},
                                                    {"title": vtitle,
                                                     "language": "en"}],
                                       "displayedText": [{"en": subessays[essay][subessay][0], "he": he_tanakh},
                                                         {"en": subessay.replace(':', ';'), "he": he_display}]})
                link_ref = subessays[essay][subessay][0].replace(" ", ".").replace(":", ".")
                subessays[essay][subessay][0] = subessays[essay][subessay][0] #f'<a href="/{link_ref}?ven=Everett_Fox">{subessays[essay][subessay][0]}</a>'
                send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
                send_text["text"] = subessays[essay][subessay]

                #Link(subessay_links[-1]).save()

                calls[f"The Five Books of Moses, by Everett Fox, {book}, {essay}, {subessay.replace(':', ';')}"] = (send_text, "http://localhost:8000")

        if re.search("^\([0-9:]{1,5}[-–]{1}[0-9:]{1,5}\)$", essays[essay][0]):
            send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
            link_ref = book + " " + essays[essay][0][1:-1]
            link_ref = link_ref.replace(" ", ".").replace(":", ".")
            essay_refs[essay] = book + " " + essays[essay][0][1:-1]
            essays[essay][0] = essay_refs[essay] #f'<a href="/{link_ref}?ven=Everett_Fox">{essay_refs[essay]}</a>'
            send_text["text"] = essays[essay]
        else:
            send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
            send_text["text"] = essays[essay]
            essays[essay] = ""

        calls[f"The Five Books of Moses, by Everett Fox, {book}, {essay}"] = (send_text, "http://localhost:8000")

post_first = False
if post_first:
    for ref in calls:
        post_text(ref, calls[ref][0], server=calls[ref][1])


essay_links = []


del essays["Torah, Introduction, To Aid the Reader of Genesis and Exodus"]
del essays["Suggestions For Further Reading"]
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    for i, essay in enumerate(order[book]):
        if essay in essays:
            if essays[essay] == "":
                print(f"No link for {essay} in {book}")
            else:
                he_display = f"{library.get_index(book).get_title('he')} {essay_heb} {encode_hebrew_numeral(i + 1)}"
                tanakh_ref = Ref(essay_refs[essay]).as_ranged_segment_ref().normal()
                ref = Ref(f"The Five Books of Moses, by Everett Fox, {book}, {essay}")
                everett_ref = ref.normal() + " 2-" + str(len(ref.text('en').text))
                print(ref.text('en').text[0])
                he_tanakh_ref = Ref(tanakh_ref).he_normal()
                essay_links.append(({"refs": [tanakh_ref, everett_ref],
                                       "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links",
                                     "versions": [{"title": vtitle, "language": "en"}, {"title": vtitle, "language": "en"}],
                                       "displayedText": [{"en": tanakh_ref, "he": he_tanakh_ref}, {"en": essay, "he": he_display}]}))
# #
# post_link(essay_links, server="https://ste.cauldron.sefaria.org")
# post_link(subessay_links, server="https://ste.cauldron.sefaria.org")

#
#
# for ref in calls:
#     post_text(ref, calls[ref][0], server=calls[ref][1])
