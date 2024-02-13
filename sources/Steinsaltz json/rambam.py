from sources.functions import *
import string
from sefaria.helper.link import rebuild_links_for_title

content = {}
notes = {}
perek = {}
section = {}
with open('steinsaltz_rambam - content.csv') as f:
    content = list(csv.DictReader(f))

with open('steinsaltz_rambam - note.csv') as f:
    notes = list(csv.DictReader(f))
with open('steinsaltz_rambam - perek.csv') as f:
    perek = list(csv.DictReader(f))
with open('steinsaltz_rambam - section.csv') as f:
    section = list(csv.DictReader(f))
note_dict = {}
links = []
names = {}
for note in notes:
    this_perek = [x for x in perek if x['id'] == note['perek_id']]
    if len(this_perek) == 0:
        print("PEREK!")
        print(note)
        continue
    assert len(this_perek) == 1
    this_perek = this_perek[0]
    this_section = [x for x in section if x['id'] == this_perek['section_id']]
    if len(this_section) == 0:
        print("SECTION!")
        print(note)
        continue
    assert len(this_section) == 1
    this_section = this_section[0]
    try:
        this_perek['num'] = int(this_perek['num'])
        note['halacha_num'] = int(note['halacha_num'])
    except ValueError as e:
        continue
    for x, y in [("Yesodei HaTorah", "Foundations of the Torah"),
                 ('Second Tithes and Fourth Years Fruit', "Second Tithes and Fourth Year's Fruit")]:
        this_section['name_eng'] = this_section['name_eng'].replace(x, y)
    if this_section['name_eng'] not in note_dict:
        note_dict[this_section['name_eng']] = {}
    names[this_section['name_eng']] = this_section['name']
    if this_perek['num'] not in note_dict[this_section['name_eng']]:
        note_dict[this_section['name_eng']][this_perek['num']] = defaultdict(list)
    if f"<b>{note['title'].strip()}</b>. {note['text'].strip()}" not in note_dict[this_section['name_eng']][this_perek['num']][note['halacha_num']]:
        note_dict[this_section['name_eng']][this_perek['num']][note['halacha_num']].append(f"<b>{note['title'].strip()}</b>. {note['text'].strip()}")
    MT_ref = f"Mishneh Torah, {this_section['name_eng']} {this_perek['num']}:{note['halacha_num']}"
    comments = len(note_dict[this_section['name_eng']][this_perek['num']][note['halacha_num']])
    stein = f"Steinsaltz on Mishneh Torah, {this_section['name_eng']} {this_perek['num']}:{note['halacha_num']}:{comments}"
    links.append([MT_ref, stein])
steinsaltz = 'ביאור שטיינזלץ'

cats = ["Halakhah", "Mishneh Torah", "Commentary", "Steinsaltz"]
c = Category()
c.path = cats
c.add_shared_term("Steinsaltz")

try:
    c.save()
except:
    pass

names["De'ot"] = "הלכות דעות"
names["Foundations of the Torah"] = "הלכות יסודי התורה"
for book in note_dict:
    root = JaggedArrayNode()
    root.add_structure(["Chapter", "Halacha", "Paragraph"])
    root.add_primary_titles(f"Steinsaltz on Mishneh Torah, {book}", f"{steinsaltz}" + " על משנה תורה, " +f"{names[book]}")
    root.key = f"Steinsaltz on Mishneh Torah, {book}"
    root.validate()
    print(root.key)
    try:
        subcat = library.get_index(f"Mishneh Torah, {book}").categories[-1]
    except Exception as e:
        continue
    cats = ["Halakhah", "Mishneh Torah", "Commentary", "Steinsaltz", subcat]
    if Category().load({"path": cats}) is None:
        c = Category()
        c.path = cats
        c.add_shared_term(cats[-1])
        c.save()
    indx = {'title': root.key, 'categories': cats, "schema": root.serialize(), "dependence": "Commentary",
                        "base_text_titles": [f"Mishneh Torah, {book}"], 'collective_title': "Steinsaltz",
                        "base_text_mapping": "many_to_one"}
    try:
        library.get_index(root.key)
    except:
        Index(indx).save()

    for perek in note_dict[book]:
        note_dict[book][perek] = convertDictToArray(note_dict[book][perek])
    note_dict[book] = convertDictToArray(note_dict[book])
    try:
        tc = TextChunk(Ref(root.key), lang='he', vtitle="Steinsaltz Mishneh Torah")
        tc.text = note_dict[book]
        tc.save()
    except:
        pass
    rebuild_links_for_title(root.key, user=1)
# for l in links:
#     Link({"refs": l, "generated_by": "steinsaltz_MT", "auto": True, "type": "Commentary"}).save()
# class Section:
#     def __init__(self, book, range_eng, sec, title_en, title_he, comm_en, comm_he):
#         self.book = book
#         self.ref = range_eng
#         self.id = sec
#         if '–' in title_en or '-' in title_en:
#             title_en = title_en.replace('–', '(').replace('-', '(') + ")"
#         self.title_en = title_en.replace('’', "'").replace('”', "'").replace('“', "'")
#         self.title_he = title_he
#         self.comm_en = comm_en
#         self.comm_he = comm_he
#
#
# books = []
# sections = []
# with open("nach_section_export - nach_section_export.csv", 'r') as f:
#     rows = csv.reader(f)
#     rows = list(rows)
#     for row in rows[1:]:
#         sec, sefer, title_en, title_he, comm_en, comm_he, range_eng, range_heb,	range_start,	range_end,	parent_id = row
#         if range_eng == 'NULL':
#             continue
#         range_eng = range_eng.replace("chaps. ", "").replace("The Song of", "Song of")
#         book = Ref(range_eng).index.title
#         if book not in books:
#             books.append(book)
#         sections.append(Section(book, range_eng, sec, title_en, title_he, comm_en, comm_he))
#
#
# if parsing:
#     for b in tanakh_books.splitlines():
#         try:
#             library.get_index(b).delete()
#         except:
#             pass
#     with open("nach_content_export - nach_content_export (4).csv", 'r') as f:
#         rows = csv.reader(f)
#         rows = list(rows)
#         curr_book = prev_book = ""
#         ref_in_section = Counter()
#         for r, row in enumerate(rows[1:]):
#             id,	perek_id,	section_id,	posuk_num, text_orig, text_ftnote, text_en = row
#             for s, sec in enumerate(sections):
#                 if sec.id == section_id:
#                     if Ref(sec.ref).index.title != curr_book:
#                         prev_book = curr_book
#                         curr_book = Ref(sec.ref).index.title
#                     curr_range = Ref(sec.ref).normal()
#                     ref_in_section[curr_range] += 1
#                     seg_refs = Ref(curr_range).all_segment_refs()
#                     if ref_in_section[curr_range] > len(seg_refs):
#                         section_id = str(int(sec.id) + 1)
#                         continue
#                     curr_ref = seg_refs[ref_in_section[curr_range]-1]
#                     #if curr_ref.normal() == "Joshua 21:36":
#                     #    curr_ref = curr_ref.next_segment_ref().next_segment_ref()
#                     while curr_ref.sections[1] < int(posuk_num):
#                         curr_ref = curr_ref.next_segment_ref()
#                         ref_in_section[curr_range] += 1
#                     while curr_ref.sections[1] > int(posuk_num):
#                         curr_ref = Ref(curr_ref.prev_segment_ref().normal().replace(":" + prev_posuk_num, ":" + posuk_num))
#                         ref_in_section[curr_range] -= 1
#                     prev_posuk_num = posuk_num
#                     break
#
#             if prev_book != curr_book:
#                 root = JaggedArrayNode()
#                 root.add_primary_titles(f"Steinsaltz on {curr_book}",
#                                         f"{steinsaltz} על {library.get_index(curr_book).get_title('he')}")
#                 root.add_structure(["Chapter", "Verse"])
#                 root.key = f"Steinsaltz on {curr_book}"
#                 root.validate()
#                 print(f"Steinsaltz on {curr_book}")
#
#                 cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz", library.get_index(curr_book).categories[1]]
#                 if Category().load({"path": cats}) is None:
#                     c = Category()
#                     c .path = cats
#                     c.add_shared_term(cats[-1])
#                     c.save()
#                 indx = {'title': root.key, 'categories': cats, "schema": root.serialize(), "dependence": "Commentary",
#                         "base_text_titles": [curr_book], 'collective_title': "Steinsaltz",
#                         "base_text_mapping": "one_to_one"}
#                 prev_book = curr_book
#                 try:
#                     Index(indx).save()
#                 except:
#                     pass
#             if curr_ref.normal() in corrected:
#                 text_ftnote = corrected[curr_ref.normal()]
#             else:
#                 for x in re.findall(":[א-ת]{1}", text_ftnote):
#                     text_ftnote = text_ftnote.replace(x, f": {x[1]}")
#                 for p in ["<footnote.*?>", "<notes.*?>"]:
#                     for m in re.findall(p, text_ftnote):
#                         text_ftnote = text_ftnote.replace(m, "")
#                     for m in re.findall(p, text_en):
#                         text_en = text_en.replace(m, "")
#
#             tc = TextChunk(Ref(f"Steinsaltz on {curr_ref.normal()}"), lang='he', vtitle="The Koren Steinsaltz Tanakh HaMevoar - Hebrew")
#             for f in re.findall('(([א-ת])\.([א-ת]))', text_ftnote):
#                 text_ftnote = text_ftnote.replace(f[0], f"{f[1]}. {f[2]}")
#             for f in re.findall('(([א-ת]):([א-ת]))', text_ftnote):
#                 text_ftnote = text_ftnote.replace(f[0], f"{f[1]}: {f[2]}")
#             tc.text = text_ftnote
#             heb_words += text_ftnote.count(" ")
#             base_heb += curr_ref.text('he').text.count(" ")
#             tc.save(force_save=True)
#             tc = TextChunk(Ref(f"Steinsaltz on {curr_ref.normal()}"), lang='en', vtitle="The Steinsaltz Tanakh - English")
#             tc.text = text_en
#             tc.save(force_save=True)
#         for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array():
#             library.get_index(v.title).versionState().refresh()
#             v.versionSource = "https://korenpub.com/collections/the-steinsaltz-tanakh/products/steinsaltz-tanakh"
#             v.save()
#         for v in VersionSet({"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
#             library.get_index(v.title).versionState().refresh()
#             v.versionSource = "https://korenpub.com/collections/tanakh/products/the-koren-steinsaltz-tanakh-hamevoar-sethardcoverlarge"
#             v.save()