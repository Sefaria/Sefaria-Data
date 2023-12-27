from sources.functions import *
import string
tanakh_books = """Steinsaltz on Joshua
                Steinsaltz on Judges
                Steinsaltz on I Samuel
                Steinsaltz on II Samuel
                Steinsaltz on I Kings
                Steinsaltz on II Kings
                Steinsaltz on Isaiah
                Steinsaltz on Jeremiah
                Steinsaltz on Ezekiel
                Steinsaltz on Hosea
                Steinsaltz on Joel
                Steinsaltz on Amos
                Steinsaltz on Obadiah
                Steinsaltz on Jonah
                Steinsaltz on Micah
                Steinsaltz on Nahum
                Steinsaltz on Habakkuk
                Steinsaltz on Zephaniah
                Steinsaltz on Haggai
                Steinsaltz on Zechariah
                Steinsaltz on Malachi
                Steinsaltz on Psalms
                Steinsaltz on Proverbs
                Steinsaltz on Job
                Steinsaltz on Song of Songs
                Steinsaltz on Ruth
                Steinsaltz on Lamentations
                Steinsaltz on Ecclesiastes
                Steinsaltz on Esther
                Steinsaltz on Daniel
                Steinsaltz on Ezra
                Steinsaltz on Nehemiah
                Steinsaltz on I Chronicles
                Steinsaltz on II Chronicles"""
tanakh_books = "Steinsaltz on Joshua"
punctuation_regex = re.compile('[%s]' % re.escape(string.punctuation))
steinsaltz = 'ביאור שטיינזלץ'
t = Term().load({"titles.text": steinsaltz})
t.add_title("Steinsaltz Commentary", 'en')
t.save()


def create_intros(book):
    node = JaggedArrayNode()
    node.add_primary_titles(book, library.get_index(book).get_title('he'))
    node.add_structure(["Paragraph"])
    node.key = book
    return node


intro_links = defaultdict(list)
intro_text = defaultdict(list)
he_intro_text = defaultdict(list)
para_intro_text = defaultdict(list)
para_he_intro_text = defaultdict(list)
def save_text_and_links():
    for ref in intro_text.keys():
        diff = len(intro_text[ref]) - len(he_intro_text[ref])
        if diff != 0:
            print(f"{ref} diff {diff}")
        tc = TextChunk(Ref(ref+", Section Preface"), vtitle='The Steinsaltz Tanakh - English', lang='en')
        tc.text = intro_text[ref]
        tc.save(force_save=True)
        tc = TextChunk(Ref(ref + ", Book Introduction"), vtitle='The Steinsaltz Tanakh - English', lang='en')
        tc.text = para_intro_text[ref]
        tc.save(force_save=True)
        for l, line in enumerate(he_intro_text[ref]):
            for f in re.findall('(([א-ת])\.([א-ת]))', line):
                he_intro_text[ref][l] = he_intro_text[ref][l].replace(f[0], f"{f[1]}. {f[2]}")
            for f in re.findall('(([א-ת]):([א-ת]))', line):
                he_intro_text[ref][l] = he_intro_text[ref][l].replace(f[0], f"{f[1]}: {f[2]}")

        tc = TextChunk(Ref(ref+", Book Introduction"), vtitle='The Koren Steinsaltz Tanakh HaMevoar - Hebrew', lang='he')
        tc.text = para_he_intro_text[ref]
        tc.save(force_save=True)

        tc = TextChunk(Ref(ref+", Section Preface"), vtitle='The Koren Steinsaltz Tanakh HaMevoar - Hebrew', lang='he')
        tc.text = he_intro_text[ref]
        tc.save(force_save=True)


def parse_book_sections(node, sections, book_data):
    for sec in sections:
        if sec.book == node.get_primary_title('en'):
            if node.get_primary_title('en') == "Psalms":
                sec.title_en = Ref(sec.title_en.replace("PSALM", "Psalms")).normal()
                sec.title_he = Ref(sec.title_en).he_normal()

            ref = f"Steinsaltz Introductions to Tanakh, {node.get_primary_title('en')}"

            for p in ["<footnote.*?>", "<notes.*?>"]:
                for m in re.findall(p, sec.comm_en):
                    sec.comm_en = sec.comm_en.replace(m, "")
                for m in re.findall(p, sec.comm_he):
                    sec.comm_he = sec.comm_he.replace(m, "")
            if len(intro_text[ref]) == 0 and len(book_data) > 0:
                for p in ["<footnote.*?>", "<notes.*?>"]:
                    book_data = list(book_data)
                    for i, d in enumerate(book_data):
                        for m in re.findall(p, book_data[i]):
                            book_data[i] = book_data[i].replace(m, "")
                para_intro_text[ref].append(book_data[0])
                para_he_intro_text[ref].append(book_data[1])
            intro_links[ref].append(sec.ref)
            intro_text[ref].append(f'({sec.ref})')
            he_intro_text[ref].append(f'({Ref(sec.ref).he_normal()})')
            if sec.comm_en != "":
                intro_text[ref][-1] += f"<br><b>{sec.title_en}</b><br/>{sec.comm_en}"
            else:
                intro_text[ref][-1] += f"<br><b>{sec.title_en}</b>"
            if sec.comm_he != "":
                he_intro_text[ref][-1] += f"<br><b>{sec.title_he}</b><br/>{sec.comm_he}"
            else:
                he_intro_text[ref][-1] += f"<br><b>{sec.title_he}</b>"

class Section:
    def __init__(self, book, range_eng, sec, title_en, title_he, comm_en, comm_he):
        self.book = book
        self.ref = range_eng
        self.id = sec
        if '–' in title_en or '-' in title_en:
            title_en = title_en.replace('–', '(').replace('-', '(') + ")"
        self.title_en = title_en.replace('’', "'").replace('”', "'").replace('“', "'")
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
            continue
        range_eng = range_eng.replace("chaps. ", "").replace("The Song of", "Song of")
        book = Ref(range_eng).index.title
        if book not in books:
            books.append(book)
        sections.append(Section(book, range_eng, sec, title_en, title_he, comm_en, comm_he))

_all = True
creating_intro = True
linking = True
parsing = False
if _all:
    linking = parsing = creating_intro = True

cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz"]
c = Category()
c.path = cats
c.add_shared_term("Steinsaltz")

try:
    c.save()
except:
    pass
base_heb = 0
base_en = 0
heb_words = 0
en_words = 0
perakim = [len(library.get_index(b).all_section_refs()) for b in books]

def get_substrings(input_string, length=5):
    return [input_string[i: i + length] for i in range(len(input_string) - length + 1)]

def get_corrected():
    corrected = {}
    with open("actual issues - corrected (1).csv", 'r') as f:
        rows = csv.reader(f)
        for r in rows:
            ref, t1, t2 = r[0], r[1], r[2]

            corrected[ref] = t1
    return corrected

corrected = get_corrected()
steinsaltz_longer = []
steinsaltz_shorter = []
if parsing:
    for b in tanakh_books.splitlines():
        try:
            library.get_index(b).delete()
        except:
            pass
    with open("nach_content_export - nach_content_export (4).csv", 'r') as f:
        rows = csv.reader(f)
        rows = list(rows)
        curr_book = prev_book = ""
        ref_in_section = Counter()
        for r, row in enumerate(rows[1:]):
            id,	perek_id,	section_id,	posuk_num, text_orig, text_ftnote, text_en = row
            for s, sec in enumerate(sections):
                if sec.id == section_id:
                    if Ref(sec.ref).index.title != curr_book:
                        prev_book = curr_book
                        curr_book = Ref(sec.ref).index.title
                    curr_range = Ref(sec.ref).normal()
                    ref_in_section[curr_range] += 1
                    seg_refs = Ref(curr_range).all_segment_refs()
                    if ref_in_section[curr_range] > len(seg_refs):
                        section_id = str(int(sec.id) + 1)
                        continue
                    curr_ref = seg_refs[ref_in_section[curr_range]-1]
                    #if curr_ref.normal() == "Joshua 21:36":
                    #    curr_ref = curr_ref.next_segment_ref().next_segment_ref()
                    while curr_ref.sections[1] < int(posuk_num):
                        curr_ref = curr_ref.next_segment_ref()
                        ref_in_section[curr_range] += 1
                    while curr_ref.sections[1] > int(posuk_num):
                        curr_ref = Ref(curr_ref.prev_segment_ref().normal().replace(":" + prev_posuk_num, ":" + posuk_num))
                        ref_in_section[curr_range] -= 1
                    prev_posuk_num = posuk_num
                    break

            if prev_book != curr_book:
                root = JaggedArrayNode()
                root.add_primary_titles(f"Steinsaltz on {curr_book}",
                                        f"{steinsaltz} על {library.get_index(curr_book).get_title('he')}")
                root.add_structure(["Chapter", "Verse"])
                root.key = f"Steinsaltz on {curr_book}"
                root.validate()
                print(f"Steinsaltz on {curr_book}")

                cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz", library.get_index(curr_book).categories[1]]
                if Category().load({"path": cats}) is None:
                    c = Category()
                    c.path = cats
                    c.add_shared_term(cats[-1])
                    c.save()
                indx = {'title': root.key, 'categories': cats, "schema": root.serialize(), "dependence": "Commentary",
                        "base_text_titles": [curr_book], 'collective_title': "Steinsaltz",
                        "base_text_mapping": "one_to_one"}
                prev_book = curr_book
                try:
                    Index(indx).save()
                except:
                    pass
            if curr_ref.normal() in corrected:
                text_ftnote = corrected[curr_ref.normal()]
            else:
                for x in re.findall(":[א-ת]{1}", text_ftnote):
                    text_ftnote = text_ftnote.replace(x, f": {x[1]}")
                for p in ["<footnote.*?>", "<notes.*?>"]:
                    for m in re.findall(p, text_ftnote):
                        text_ftnote = text_ftnote.replace(m, "")
                    for m in re.findall(p, text_en):
                        text_en = text_en.replace(m, "")

            tc = TextChunk(Ref(f"Steinsaltz on {curr_ref.normal()}"), lang='he', vtitle="The Koren Steinsaltz Tanakh HaMevoar - Hebrew")
            for f in re.findall('(([א-ת])\.([א-ת]))', text_ftnote):
                text_ftnote = text_ftnote.replace(f[0], f"{f[1]}. {f[2]}")
            for f in re.findall('(([א-ת]):([א-ת]))', text_ftnote):
                text_ftnote = text_ftnote.replace(f[0], f"{f[1]}: {f[2]}")
            tc.text = text_ftnote
            heb_words += text_ftnote.count(" ")
            base_heb += curr_ref.text('he').text.count(" ")
            tc.save(force_save=True)
            tc = TextChunk(Ref(f"Steinsaltz on {curr_ref.normal()}"), lang='en', vtitle="The Steinsaltz Tanakh - English")
            tc.text = text_en
            tc.save(force_save=True)
        for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array():
            library.get_index(v.title).versionState().refresh()
            v.versionSource = "https://korenpub.com/collections/the-steinsaltz-tanakh/products/steinsaltz-tanakh"
            v.save()
        for v in VersionSet({"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
            library.get_index(v.title).versionState().refresh()
            v.versionSource = "https://korenpub.com/collections/tanakh/products/the-koren-steinsaltz-tanakh-hamevoar-sethardcoverlarge"
            v.save()

if creating_intro:
    try:
        library.get_index("Steinsaltz Introductions to Tanakh").delete()
    except:
        pass
    sefer = {}
    with open("nach_sefer_export - nach_sefer_export.csv", 'r') as f:
        rows = list(csv.reader(f))
        for row in rows:
            r_id,  name_eng,  name_heb,  intro_eng,  intro_heb, pereks = row
            if name_eng.endswith(" II"):
                continue
            elif name_eng.endswith(" I"):
                name_eng = name_eng.replace(" I", "")
            sefer[name_eng] = (intro_eng, intro_heb)
    intro = SchemaNode()
    intro.add_primary_titles("Steinsaltz Introductions to Tanakh", 'ביאור שטיינזלץ, הקדמות לתנ"ך')
    intro.key = "Steinsaltz Introductions to Tanakh"

    for b in books:
        node = create_intros(b)
        m = re.search("I{1,2} ", b)
        if b.startswith("I "):
            b = b.replace("I ", "", 1)
        if "II " in b:
            sefer[b] = []
        parse_book_sections(node, sections, sefer[b])
        one_para = JaggedArrayNode()
        one_para.add_primary_titles("Book Introduction", "הקדמה לספר")
        one_para.add_structure(["Paragraph"])
        node.append(one_para)
        content = JaggedArrayNode()
        content.add_primary_titles("Section Preface", "מבוא לקטע")
        content.add_structure(["Paragraph"])
        node.append(content)
        intro.append(node)
    intro.validate()
    intro = {"schema": intro.serialize(),
           "title": intro.key,
           "categories": ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz"]}
    try:
        library.get_index(intro['title'])
    except:
        Index(intro).save()
    save_text_and_links()

if linking:
    try:
        LinkSet({"generated_by": "steinsaltz intro"}).delete()
    except:
        pass
    try:
        LinkSet({"generated_by": "steinsaltz_essay_links"}).delete()
    except:
        pass
    try:
        LinkSet({"generated_by": "steinsaltz_commentary"}).delete()
    except:
        pass
    try:
        LinkSet({"generated_by": "steinsaltz_to_nakh"}).delete()
    except:
        pass
    for ref in intro_text.keys():
        amt = 0 if ref.startswith("II ") else 1
        for l, link in enumerate(intro_links[ref]): # Steinsaltz Introductions to Tanakh, Joshua, Section Preface
            link = link[0].capitalize()+link[1:]
            en_stein = "Steinsaltz Introductions to Tanakh, "+ref.split(",")[-1].strip()+", Section Preface"
            he_stein = Ref("Steinsaltz Introductions to Tanakh, "+ref.split(",")[-1].strip()+", Section Preface").he_normal()
            obj = {"refs": [link, f"{ref}, Section Preface {l+amt}"],
                 "auto": True, "type": "essay", "generated_by": "steinsaltz_to_nakh",
                 "versions": [{"title": "ALL",
                               "language": "en"},
                              {"title": "ALL",
                               "language": "en"}],
                 "displayedText": [{"en": Ref(link).book,
                                    "he": Ref(link).he_book()},
                                   {"en": en_stein, "he": he_stein}]}
            try:
                Link(obj).save()
            except:
                pass
            obj = {"type": "essay", "generated_by": "steinsaltz_to_nakh",
                 "versions": [{"title": "ALL",
                               "language": "en"},
                              {"title": "ALL",
                               "language": "en"}], "auto": True,
                   "displayedText": [{"en": en_stein, "he": he_stein},
                                       {"en": "Steinsaltz Commentary",
                                         "he": steinsaltz}],
                   "refs": [f"{ref}, Section Preface {l + amt}", f"Steinsaltz on {link}"]}
            try:
                Link(obj).save()
            except:
                pass

    for x in ["Prophets", "Writings"]:
        books = library.get_indexes_in_category(["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz", x], include_dependant=True)
        for b in books:
            print(b)
            if b.startswith("Int"):
                continue
            for r in library.get_index(b).all_segment_refs():
                # for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array() + VersionSet(
                #         {"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
                r = r.normal()
                en_stein = " ".join(r.split()[:-1])
                he_stein = library.get_index(en_stein).get_title('he')
                en_tanakh = " ".join(r.replace("Steinsaltz on ", "").split()[:-1])
                he_tanakh = library.get_index(en_tanakh).get_title('he')
                l = {"refs": [r.replace("Steinsaltz on ", ""), r],
                     "auto": True, "type": "commentary", "generated_by": "steinsaltz_to_nakh"}
                try:
                    Link(l).save()
                except:
                    print(l)
            for r in library.get_index(b).all_section_refs():
                # for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array() + VersionSet(
                #         {"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
                r = r.normal()
                en_stein = " ".join(r.split()[:-1])
                he_stein = library.get_index(en_stein).get_title('he')
                en_tanakh = " ".join(r.replace("Steinsaltz on ", "").split()[:-1])
                he_tanakh = library.get_index(en_tanakh).get_title('he')
                actual_book = " ".join(r.replace("Steinsaltz on ", "").split()[:-1])
                he_actual_book = library.get_index(actual_book).get_title('he')
                stein_node = f"Steinsaltz Introductions to Tanakh, {actual_book}, Book Introduction"
                he_stein_node = Ref(stein_node).he_normal()
                l2 = {"refs": [Ref(r.replace("Steinsaltz on ", "")).as_ranged_segment_ref().normal(),
                               f"{stein_node}"],
                     "auto": True, "type": "essay", "generated_by": "steinsaltz_to_nakh",
                     "versions": [{"title": "ALL",
                                     "language": "en"},
                                    {"title": "ALL",
                                     "language": "en"}],
                     "displayedText": [{"en": actual_book, "he": he_actual_book},
                                       {"en": stein_node, "he": he_stein_node}]
                     }
                try:
                    Link(l2).save()
                except:
                    print(l2)
                r = Ref(r)
                l2 = {"refs": [r.as_ranged_segment_ref().normal(),
                               f"{stein_node}"],
                      "auto": True, "type": "essay", "generated_by": "steinsaltz_to_nakh",
                      "versions": [{"title": "ALL",
                                    "language": "en"},
                                   {"title": "ALL",
                                    "language": "en"}],
                      "displayedText": [{"en": r.book, "he": r.he_book()},
                                        {"en": stein_node, "he": he_stein_node}]
                      }
                try:
                    Link(l2).save()
                except:
                    print(l2)
    "steinsaltz_commentary", "steinsaltz intro", "steinsaltz_essay_links"

for v in VersionSet({"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
    books.append((library.get_index(v.title), v.versionTitle))
books = books[::-1]
for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array():
    books.append((library.get_index(v.title), v.versionTitle))
for bt in tqdm(books):
    b, v = bt
    # if not b.title == "Steinsaltz on Judges":
    #     continue
    if len(b.all_segment_refs()) < 10:
        b.versionState().refresh()
        assert len(b.all_segment_refs()) > 10
    for r in b.all_segment_refs():
        lang = 'en'
        if "Hebrew" in v:
            lang = 'he'
        orig = text = r.text(lang).text
        both = True
        for c in ['.', ':']:
            c_bool = False
            text_ftnotes = text.split(c)
            for i, l in enumerate(text_ftnotes[1:]):
                text_wout_html = bleach.clean(text_ftnotes[i+1], strip=True, tags=[])
                if len(text_wout_html) > 0 and not text_wout_html.startswith(" "):
                    m = re.findall('^[א-ת]{1}', text_wout_html)
                    if len(m) > 0:
                        text_ftnotes[1+i] = " " + text_ftnotes[i+1]
                        c_bool = True
            both = c_bool and both
            text = f"{c}".join(text_ftnotes)

        for p in ["&lt;footnote.*?&gt;", "&lt;notes.*?&gt;"]:
            for m in re.findall(p, text):
                print(r)
                text = text.replace(m, "")
        if orig != text:
            tc = TextChunk(r, lang=lang, vtitle=v)
            tc.text = text
            tc.save(force_save=True)