from sources.functions import *
class Section:
    def __init__(self, book, range_eng, sec, title_en, title_he, comm_en, comm_he):
        self.book = book
        self.ref = range_eng
        self.id = sec
        self.title_en = title_en
        self.title_he = title_he
        self.comm_en = comm_en
        self.comm_he = comm_he

books = []
sections = []
with open("nach_section_export - nach_section_export.csv", 'r') as f:
    rows = csv.reader(f)
    rows = list(rows)
    for row in rows[1:]:
        sec, sefer, title_en, title_he, comm_en, comm_he, range_eng, range_heb,	range_start,	range_end,	parent_id = row
        if range_eng == 'NULL':
            print(row)
            continue
        range_eng = range_eng.replace("chaps. ", "").replace("The Song of", "Song of")
        book = Ref(range_eng).index.title
        if book not in books:
            books.append(book)
        sections.append(Section(book, range_eng, sec, title_en, title_he, comm_en, comm_he))

perakim = [len(library.get_index(b).all_section_refs()) for b in books]
cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz"]
c = Category()
c.path = cats
c.add_shared_term("Steinsaltz")
#c.save()
with open("nach_content_export - nach_content_export.csv", 'r') as f:
    rows = csv.reader(f)
    rows = list(rows)
    curr_book = books[0]
    steinsaltz = 'ביאור שטיינזלץ'


    for row in rows[1:]:
        id,	perek_id,	section_id,	posuk_num, text_orig, text_ftnote, text_en = row
        for sec in sections:
            if sec.id == section_id:
                curr_book = Ref(sec.ref).index.title
                curr_perek = Ref(sec.ref).sections[0]
                break
        print(curr_book)
        root = JaggedArrayNode()
        root.add_primary_titles(f"Steinsaltz Commentary on {curr_book}",
                                f"{steinsaltz} על {library.get_index(curr_book).get_title('he')}")
        root.add_structure(["Chapter", "Verse"])
        root.key = f"Steinsaltz Commentary on {curr_book}"
        root.validate()

        cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz", library.get_index(curr_book).categories[1]]
        if Category().load({"path": cats}) is None:
            c = Category()
            c.path = cats
            c.add_shared_term(cats[-1])
            c.save()
        indx = {'title': root.key, 'categories': cats, "schema": root.serialize(), "dependence": "Commentary",
                "base_text_titles": [curr_book],
                "base_text_mapping": "one_to_one"}
        try:
            Index(indx).save()
        except:
            pass
        print(curr_perek)
        for p in ["<footnote.*?>", "<notes.*?>"]:
            for m in re.findall(p, text_ftnote):
                text_ftnote = text_ftnote.replace(m, "")
            for m in re.findall(p, text_en):
                text_en = text_en.replace(m, "")
        tc = TextChunk(Ref(f"Steinsaltz Commentary on {curr_book} {curr_perek}:{posuk_num}"), lang='he', vtitle="Steinsaltz he")
        tc.text = text_ftnote
        tc.save(force_save=True)
        tc = TextChunk(Ref(f"Steinsaltz Commentary on {curr_book} {curr_perek}:{posuk_num}"), lang='en', vtitle="Steinsaltz en")
        tc.text = text_en
        tc.save(force_save=True)
    for v in VersionSet({"versionTitle": "Steinsaltz en"}).array()+VersionSet({"versionTitle": "Steinsaltz he"}).array():
        v.versionSource = "https://www.sefaria.org"
        v.save()

In [10]:     from sefaria.helper.link import rebuild_links_for_title as rebuild
    ...:     rebuild(title, request.user.id)

books = [x for x in library.get_indexes_in_category("Steinsaltz", include_dependant=True) if "Steinsaltz Commentary" in x]
In [10]: for b in books:
    ...:     rebuild(b, 1)