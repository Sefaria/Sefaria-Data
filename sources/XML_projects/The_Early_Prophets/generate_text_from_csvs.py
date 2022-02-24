from sources.functions import *
from collections import OrderedDict
essays = defaultdict(list)
subessays = OrderedDict()
order_essays = []
with open("essay contents/essays.csv") as f:
    for row in csv.reader(f):
        book, num, comm = row
        book = book.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "")
        essays[book].append(comm)
        if book not in order_essays:
            order_essays.append(book)
subessays = json.load(open("essay contents/subessays_full.json", 'r'))
# del subessays['Torah, Numbers On Bil’am']
# del subessays["Part II; The Rebellion Narratives"]['Bil’am the Prophet']
# del subessays["Part II; The Rebellion Narratives"]['Bil’am’s First Visions']
subessays["An Appended Chapter"] = {"Appendix: Support for the Sanctuary": ["Leviticus 27", "Clearly a later addition to Leviticus, Chap. 27 provides for the upkeep of the sanctuary through a variety of means: donations of silver; pledging animals or property which is later redeemed for silver; confiscated property; and tithes. The nature of the text as appendix is obvious, given the finality of tone in the previous chapter, but it could also be said that 27 provides an appropriate ending to Leviticus, since it talks about dedication of property to God, as the book does in regard to all areas of life."]}

essays["Part I; The Cult and the Priesthood"].append("O<small>N</small> A<small>NIMAL</small> S<small>ACRIFICE</small>")
for line in essays["On Animal Sacrifice"]:
    essays["Part I; The Cult and the Priesthood"].append(line)


essays["Part II; Ritual Pollution and Purification"].append("O<small>N</small> T<small>HE</small> D<small>IETARY</small> R<small>ULES</small>")
for line in essays["On the Dietary Rules"]:
    essays["Part II; Ritual Pollution and Purification"].append(line)


essays["Part II; Ritual Pollution and Purification"].append("O<small>N</small> T<small>HE</small> R<small>ITUAL</small> P<small>OLLUTION</small> O<small>F</small> T<small>HE</small> B<small>ODY</small>")
for line in essays["On the Ritual Pollution of the Body"]:
    essays["Part II; Ritual Pollution and Purification"].append(line)

del essays["On Animal Sacrifice"]
del essays["On the Dietary Rules"]
del essays["On the Ritual Pollution of the Body"]
order_essays.pop(1)
order_essays.pop(19)
order_essays.pop(20)
order_essays.pop(20)
order_essays.insert(21, "An Appended Chapter")
order = {"Genesis": order_essays[1:7], "Exodus": order_essays[7:15], "Leviticus": order_essays[15:22], "Numbers": order_essays[22:26], "Deuteronomy": order_essays[26:-1]}
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
                node.add_primary_titles(subessay.replace("\u2019", "'").replace("-", " ").replace(':', ';'), f"{library.get_index(book).get_title('he')} {comment_heb} {encode_hebrew_numeral(j+1)}")
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
#post_index(indx, server="https://germantalmud.cauldron.sefaria.org")
vtitle = "The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995"
subessay_links = []
calls = {}
essay_refs = {}
everett = ""
essays["Part II; Avraham"][0] = "Genesis 12:1-25:18"
essays["Part III; Yaakov"][0] = "Genesis 25:19-36:43"
essays['Part I; Historical Overview'][0] = 'Deuteronomy 1:1–4:43'
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org",
                 "shortVersionTitle": "The Schocken Bible, Everett Fox, 1995",
                 "purchaseInformationURL": "https://www.amazon.com/Five-Books-Moses-Leviticus-Deuteronomy/dp/0805211195",
                 "purchaseInformationImage": "https://images-na.ssl-images-amazon.com/images/I/41mR7aOmNyL._SX350_BO1,204,203,200_.jpg"}
    send_text["text"] = book_text[book]
    assert len(book_text[book]) == len(library.get_index(book).all_section_refs())
    for p, perek in enumerate(book_text[book]):
        assert len(Ref(f"{book} {p+1}").all_segment_refs()) == len(book_text[book][p])
    for i, essay in enumerate(order[book]):
        essay = essay #.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "").replace("Vi: ", "").replace("V: ", "")
        if essay in subessays:
            for j, subessay in enumerate(subessays[essay]):
                Ref(subessays[essay][subessay][0])
                everett = f"The Five Books of Moses, by Everett Fox, {book}, {essay}, "+ subessay.replace(':', ';').replace("\u2019", "'").replace("-", " ")
                try:
                    range = len(Ref(everett).text('en').text)
                    everett = "{} 2-{}".format(everett, range) if range != 2 else "{} 2".format(everett)
                    print(Ref(everett).text('en').text[0])
                except:
                    pass

                he_display = f"{library.get_index(book).get_title('he')} {comment_heb} {encode_hebrew_numeral(j+1)}"
                he_tanakh = Ref(subessays[essay][subessay][0]).he_normal()
                if "-" in subessays[essay][subessay][0]:
                    sec, toSec = subessays[essay][subessay][0].split("-") #4:1-16 is OK, 4:1-5:1 is OK, 4-5:1 is not OK, 4-5 is OK
                    first_colon = sec.find(":") > 0
                    second_colon = toSec.find(":") > 0
                    assert not(not first_colon and second_colon)

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

                calls[f"""The Five Books of Moses, by Everett Fox, {book}, {essay}, """+subessay.replace("\u2019", "'").replace("-", " ").replace(":", ";")] = (send_text, "http://localhost:8000")
        else:
            print(essay)

        if len(essays[essay]) == 0:
            continue

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
essays["Part II; Avraham"] = "Genesis 12:1-25:18"
essay_refs["Part II; Avraham"] = "Genesis 12:1-25:18"
essays["Part III; Yaakov"] = "Genesis 25:19-36:43"
essay_refs["Part III; Yaakov"] = "Genesis 25:19-36:43"
essays["Part III; The Meeting and Covenant At Sinai"] = "Exodus 19:1-24:18"
essay_refs["Part III; The Meeting and Covenant At Sinai"] = "Exodus 19:1-24:18"
essays["Part I; Historical Overview"] = "Deuteronomy 1:1-4:43"
essay_refs["Part I; Historical Overview"] = "Deuteronomy 1:1-4:43"
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    for i, essay in enumerate(order[book]):
        if essay in essays:
            if essays[essay] == "":
                print(f"No link for {essay} in {book}")
            else:
                assert essay_refs[essay].find(":") == -1 or (essay_refs[essay].find(":") != essay_refs[essay].rfind(":"))
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

post_link(essay_links, server="https://germantalmud.cauldron.sefaria.org")
post_link(subessay_links, server="https://germantalmud.cauldron.sefaria.org")

#
#
# for ref in calls:
#     post_text(ref, calls[ref][0], server=calls[ref][1])
