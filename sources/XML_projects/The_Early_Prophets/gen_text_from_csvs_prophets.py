from sources.functions import *
from collections import OrderedDict
from fuzzywuzzy import fuzz

def modified(x, book=None):
    if book is not None:
        x = x.replace("The Early Prophets, "+book+",", "").strip()
    x = re.sub("(Part I{1,})([a-z]{1})", r"\1 \2", x)
    return x.replace(':', ';').replace("\u2019", "'").replace("-", " ").replace("\u2019", "'").replace('"', '').replace("\u201D", '').replace("\u201C", '').replace("-", " ").replace(':', ';').strip()

def update_dict(title, new_keys, new_val):
    new_dict = {}
    for k in new_keys:
        if k in subessays[title][k]:
            new_dict[k] = subessays[title][k]
        else:
            new_dict[k] = new_val
    return new_dict

def fix_subessays(subessays):
    title = 'The Early Prophets, Samuel, Part I; The Last Judges": Eli and Shemuel'
    keys = list(subessays[title])
    new_keys = keys[:2] + ['The Call of Shemuel'] + keys[2:]
    new_val = ['I Samuel 3:1-4:1', 'There are numerous other “call” scenes in the Bible, where a prophet or leader such as Moshe (Moses) or Yesha’yahu (Isaiah) is chosen, but the present story is unique in both its location and cast of characters', 'The reader will note that God’s words to Shemuel do not, as so often in biblical “call” narratives, require answer and dialogue. Young Shemuel appears in this chapter as one through whom God speaks, and is thus a prophet, but there is none of the usual tension between the one called and the burden he is asked to carry—at least for the moment—that we find elsewhere in the Bible.']
    subessays[title] = update_dict(title, new_keys, new_val)

    keys = list(subessays[title])
    new_keys = keys[:-1] + ['The Coffer'] + keys[-1]
    new_val = ['I Samuel 6', 'The theme of the Coffer’s potency continues, with the Philistines making elaborate preparations, including sacrifices and reparations consisting (somewhat humorously, perhaps) of five golden hemorrhoids/tumors and five golden mice', 'That same hand, however, guards the Coffer from being profaned even among the Israelites, and following a peeking incident in v.19, a great plague comes upon them. This theme of what Hamilton calls “the high voltage of the supersancta,” the dangerous parameters of a divine object, will return in II Sam. 6:6–7, where it will lead to a man’s immediate death. Here, the Coffer has to move from Bet-Shemesh to Kiryat-Ye’arim, a border town some miles to the northeast, where it will be guarded by a man “hallowed” for the purpose.']
    subessays[title] = update_dict(title, new_keys, new_val)

    title = 'The Early Prophets, Samuel, Part II; The Requested King'
    keys = list(subessays[title])
    new_keys = keys[0] + ["The Choosing of Sha'ul"] + keys[1:]
    new_val = ['I Samuel 9-10', 'Israel’s first king stems from the tribe of Binyamin, whose territory straddled the north-south border region of the country but which was understood to be of northern provenance. Barely have we heard of Sha’ul’s qualifications for the job&#x2014;solid lineage and notable physical stature&#x2014;when we are introduced to him in person as, of all things, a seeker of lost she-asses. Some, such as Sweeney (2012), would see this as having a “fairy-tale” quality; others, myself included, sense something more negative: a foreshadowing of the later, “lost” Sha’ul. The meandering tale brings the young man unwittingly into the orbit of Shemuel, who, to Sha’ul’s utter surprise, hails him in v.20. Indeed, geographically, Sha’ul’s wanderings form an oval that partly intersects the circle of Shemuel’s activities in the book&#x2014;another indication of the closeness of the two characters.', 'The text plays out the selection of the new king, lingering on scenes of searching, asking, and, finally, declaring God’s will through the prophet. Whereas in the first part of the narrative Sha’ul wanders seemingly in vain, his journey ultimately bears out Shemuel’s predictions (10:2&#x2013;7) of signs from God and the leader-elect’s transformation (note that the key verb “find” occurs some thirteen times in eighteen of the chapter’s verses). Despite all of this, however, Sha’ul does not reveal the earthshaking result of his encounter with Shemuel to his family, much like Shimshon (Judg. 14) before him. That remains, for the moment, both God’s secret and a sign of Sha’ul’s modesty. Likewise, when Israel is summoned to Mitzpa, the new king, who is chosen publicly by lots, is initially nowhere to be found, and is discovered only eventually amid the gear. When he is finally acclaimed by the people in v.24, what follows is a note of doubt on their part (v.27). Sha’ul weathers this little storm, in contrast to his later capitulations, but we are left to wonder why the first Israelite monarch arises under such clouded circumstances and with such hesitation. It feels less like the classic prophetic rejection of God’s mission, where a figure such as Moshe at least argues with God, and more like a hint of flawed character. This may be symbolically indicated by Shemuel’s use of a flask of oil to anoint the new king, as opposed to the more usual horn (Miscall).', 'Sha’ul’s strange experience of behaving like a prophet, which is predicted in vv.5&#x2013;6 and recounted in 10&#x2013;11, is unique in ancient Israel’s description of its kings. The “mantic” form of prophecy referred to here, comprising extreme forms of behavior, is attested throughout the ages (see the cult of Dionysus in ancient Greece, and “speaking in tongues” still today). The experiences of “later prophets” such as Yesha’yahu (Isaiah) and Yirmeyahu (Jeremiah) tend to focus (although not exclusively) on the divine word, which is usually not obscure but, on the contrary, all too intelligible. In our chapter, one may wonder whether Sha’ul’s gift indicates chosenness, as in the earlier cases of judges who are seized by God’s spirit, or the possession of qualities that indicate a kind of instability that may not be appropriate for the sober needs of governing (Brueggemann 1990).']
    subessays[title] = update_dict(title, new_keys, new_val)

    title = 'The Early Prophets, Samuel, Part III; The Rise of David and the Fall of Sha\'ul'

    subessays[title] = update_dict(title, new_keys, new_val)


def get_he_book(book):
    try:
        return library.get_index(book).get_title('he')
    except:
        if book == "Samuel":
            return "שמואל"
        elif book == "Kings":
            return "מלכים"

linking = True
essays = defaultdict(list)
subessays = OrderedDict()
order_essays = []
with open("essays.csv") as f:
    rows = list(csv.reader(f))
    for row in rows:
        book, num, comm = row
        book = book.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "")
        essays[book].append(comm)
        if book not in order_essays:
            order_essays.append(book)
#subessays = fix_subessays(json.load(open("./subessays_full_prophets.json", 'r')))
subessays = json.load(open("./subessays_full_prophets.json", 'r'))
key = 'The Early Prophets, Kings, Part II; The Split; Kings North and South'
subessays[key]['Northern Kings'] = subessays['Northern Kings']['Northern Kings']
subessays.pop('Northern Kings')

order = {"Joshua": order_essays[0:4], "Judges": order_essays[4:10], "Samuel": order_essays[10:17], "Kings": order_essays[17:26]}

new_sub_essays = {}
for k in subessays.keys():
    new_k = k#.replace("Iv: ", "").replace("Iii: ", "").replace("Ii: ", "").replace("Vi: ", "").replace("V: ", "")
    new_sub_essays[new_k] = subessays[k]
subessays = new_sub_essays
root = SchemaNode()
essay_heb = "מאמר"
comment_heb = "הערה"
root.add_primary_titles("The Early Prophets, by Everett Fox", "נביאים ראשונים, מהדורת אברט פוקס")
for book in ["Joshua", "Judges", "Samuel", "Kings"]:
    book_node = SchemaNode()
    book_node.add_primary_titles(book, get_he_book(book))
    for i, essay in enumerate(order[book]):
        if essay in subessays:
            schemanode = SchemaNode()
            schemanode.add_primary_titles(modified(essay, book=book), f"{get_he_book(book)} {essay_heb} {encode_hebrew_numeral(i + 1)}")
            default = JaggedArrayNode()
            default.default = True
            default.key = "default"
            default.add_structure(["Paragraph"])
            schemanode.append(default)
            for j, subessay in enumerate(subessays[essay]):
                node = JaggedArrayNode()
                node.add_structure(["Paragraph"])
                node.depth = 1
                node.add_primary_titles(modified(subessay), f"{get_he_book(book)} {comment_heb} {encode_hebrew_numeral(j+1)}")
                schemanode.append(node)
            schemanode.validate()
            book_node.append(schemanode)
            book_node.validate()
        else:
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.depth = 1
            node.add_primary_titles(modified(essay, book=book), f"{get_he_book(book)} {essay_heb} {encode_hebrew_numeral(i+1)}")
            book_node.append(node)
            node.validate()
            book_node.validate()
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
indx = {"title": "The Early Prophets, by Everett Fox", "schema": root.serialize(), "categories": ["Tanakh", "Modern Commentary on Tanakh"], "dependence": "Commentary",
        "collective_title": "Everett Fox", "base_text_titles": ["Joshua", "Judges", "I Samuel", "I Kings", "II Samuel", "II Kings"]}
try:
    Index(indx).save()
except Exception as e:
    pass
    # Index().load({"title": indx["title"]}).delete()
    # Index(indx).save()

vtitle = "The Early Prophets, by Everett Fox. New York, Schocken Books, 1995"
subessay_links = []
calls = {}
essay_refs = {}
everett = ""
for book in ["Joshua", "Judges", "Samuel", "Kings"]:
    send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
    # assert len(book_text[book]) == len(library.get_index(book).all_section_refs())
    # for p, perek in enumerate(book_text[book]):
    #     assert len(Ref(f"{book} {p+1}").all_segment_refs()) == len(book_text[book][p])
    for i, essay in enumerate(order[book]):
        essay = essay #.replace("IV: ", "").replace("III: ", "").replace("II: ", "").replace("I: ", "").replace("Vi: ", "").replace("V: ", "")
        if essay in subessays:
            for j, subessay in enumerate(subessays[essay]):
                Ref(subessays[essay][subessay][0])
                everett = f"""The Early Prophets, by Everett Fox, {book}, {modified(essay, book=book)}, """ + modified(subessay)
                try:
                    range = len(Ref(everett).text('en').text)
                    everett = "{} 2-{}".format(everett, range) if range != 2 else "{} 2".format(everett)
                    #print(Ref(everett).text('en').text[0])
                    linking = True
                except:
                    pass

                he_display = f"{get_he_book(book)} {comment_heb} {encode_hebrew_numeral(j+1)}"
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

                calls[f"""The Early Prophets, by Everett Fox, {book}, {modified(essay, book=book)}, """+modified(subessay).replace("\u2019", "'").replace("-", " ").replace(":", ";")] = (send_text, "http://localhost:8000")
        else:
            print(f"{essay} not in subessays")

        if len(essays[essay]) == 0:
            continue

        book_num = ""
        if book == "Samuel" or book == "Kings":
            if "(II " in essays[essay][0]:
                book_num = "II "
            elif "(I " in essays[essay][0]:
                book_num = "I "
            essays[essay][0] = essays[essay][0].replace("(II ", "(").replace("(I ", "(")

        if re.search("^\([0-9:]{1,5}[-–]{1}[0-9:]{1,5}\)$", essays[essay][0]):
            send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
            link_ref = book_num+book + " " + essays[essay][0][1:-1]
            link_ref = link_ref.replace(" ", ".").replace(":", ".")
            essay_refs[essay] = book_num+book + " " + essays[essay][0][1:-1]
            essays[essay][0] = essay_refs[essay] #f'<a href="/{link_ref}?ven=Everett_Fox">{essay_refs[essay]}</a>'
            send_text["text"] = essays[essay]
        else:
            send_text = {"language": "en", "versionTitle": vtitle, "versionSource": "http://www.sefaria.org"}
            send_text["text"] = essays[essay]
            essays[essay] = ""

        calls[f"""The Early Prophets, by Everett Fox, {book}, {modified(essay, book=book)}"""] = (send_text, "http://localhost:8000")



post_first = True
if post_first:
    for ref in calls:
        tc = TextChunk(Ref(ref), lang='en', vtitle=calls[ref][0]['versionTitle'])
        tc.text = calls[ref][0]['text']
        tc.save(force_save=True)

for v in VersionSet({"versionTitle": list(calls.values())[0][0]['versionTitle']}):
    v.versionSource = "https://www.penguinrandomhouse.com/books/55159/the-early-prophets-joshua-judges-samuel-and-kings-by-everett-fox/"
    v.save()
    VersionState(index=v.title).refresh()

essay_links = []

for book in ["Joshua", "Judges", "Samuel", "Kings"]:
    for i, essay in enumerate(order[book]):
        if essay in essays:
            if essays[essay] == "":
                print(f"No link for {essay} in {book}")
            else:
                assert essay_refs[essay].find(":") == -1 or (essay_refs[essay].find(":") != essay_refs[essay].rfind(":"))
                he_display = f"{get_he_book(book)} {essay_heb} {encode_hebrew_numeral(i + 1)}"
                tanakh_ref = Ref(essay_refs[essay]).as_ranged_segment_ref().normal()
                ref = Ref(f"The Early Prophets, by Everett Fox, {book}, {modified(essay, book=book)}")
                everett_ref = ref.normal() + " 2-" + str(len(ref.text('en').text))
                he_tanakh_ref = Ref(tanakh_ref).he_normal()
                essay_links.append(({"refs": [tanakh_ref, everett_ref],
                                     "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links",
                                     "versions": [{"title": vtitle, "language": "en"},
                                                  {"title": vtitle, "language": "en"}],
                                     "displayedText": [{"en": tanakh_ref, "he": he_tanakh_ref},
                                                       {"en": modified(essay, book=book), "he": he_display}]}))

if linking:
    for x in tqdm(essay_links+subessay_links):
        try:
            Link(x).save()
        except:
            pass
else:
    ls = LinkSet({"generated_by": "everett_fox_essay_links"})
    if ls.count() > 0:
        ls.delete()
#
# post_link(essay_links, server="http://localhost:8000")
# post_link(subessay_links, server="http://localhost:8000")

#
#
# for ref in calls:
#     post_text(ref, calls[ref][0], server=calls[ref][1])
# missing_lines = defaultdict(list)
# found_lines = []
# for t in order_essays[26:]:
#     for line in essays[t]:
#         try:
#             if line.startswith("Chapter"):
#                 line = line.split(".")[1].split(":")[1]
#             assert " ".join(line.strip().split()) in str(subessays.values())
#             found_lines.append(line)
#         except:
#             found = None
#             for subessay_title, contents in subessays.items():
#                 if found is None:
#                     for subchapter, subessay_contents in contents.items():
#                         if found is None:
#                             for subessay_line in subessay_contents:
#                                 if fuzz.ratio(subessay_line, line) > 75:
#                                     found = subessay_line
#                                     break
#             if found:
#                 found_lines.append(found)
#             else:
#                 missing_lines[t].append(line)