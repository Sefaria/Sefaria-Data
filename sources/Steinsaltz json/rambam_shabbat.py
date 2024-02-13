from sources.functions import *
import string
from sefaria.helper.link import rebuild_links_for_title

content = {}
notes = {}
perek = {}
section = {}
with open('shabbat_content.csv') as f:
    content = list(csv.DictReader(f))

with open('shabbat_note.csv') as f:
    notes = list(csv.DictReader(f))
# with open('steinsaltz_rambam - content.csv') as f:
#     content = list(csv.DictReader(f))
#
# with open('steinsaltz_rambam - note.csv') as f:
#     notes = list(csv.DictReader(f))
with open('steinsaltz_rambam - perek.csv') as f:
    perek = list(csv.DictReader(f))
with open('steinsaltz_rambam - section.csv') as f:
    section = list(csv.DictReader(f))
note_dict = {}
links = []
names = {}
for note in notes:
    this_perek = [x for x in perek if x['id'] == note['perek_id']]
    if note['type'] != '15':
        continue
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

for book in note_dict:
    root = JaggedArrayNode()
    root.add_structure(["Chapter", "Halacha", "Paragraph"])
    root.add_primary_titles(f"Steinsaltz on Mishneh Torah, {book}", f"{steinsaltz}, על משנה תורה {names[book]}")
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