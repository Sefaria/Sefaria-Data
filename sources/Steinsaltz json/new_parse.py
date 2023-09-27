from sources.functions import *
import string

punctuation_regex = re.compile('[%s]' % re.escape(string.punctuation))


def create_intros(book):
    node = JaggedArrayNode()
    node.add_primary_titles(book, library.get_index(book).get_title('he'))
    node.add_structure(["Paragraph"])
    node.key = book
    return node


intro_links = defaultdict(list)
intro_text = defaultdict(list)
he_intro_text = defaultdict(list)

def save_text_and_links():
    for ref in intro_text.keys():
        tc = TextChunk(Ref(ref), vtitle='Steinsaltz en', lang='en')
        tc.text = intro_text[ref]
        tc.save(force_save=True)
        tc = TextChunk(Ref(ref), vtitle='Steinsaltz he', lang='he')
        tc.text = he_intro_text[ref]
        tc.save(force_save=True)
        for l, link in enumerate(intro_links[ref]):
            obj = {"generated_by": "steinsaltz intro", "type": "Commentary", "auto": True,
              "refs": [f"{ref} {l+1}", link]}
            try:
                Link(obj).save()
                obj = {"generated_by": "steinsaltz intro", "type": "Commentary", "auto": True,
                       "refs": [f"{ref} {l + 1}", f"Steinsaltz Commentary on {link}"]}
                Link(obj).save()
            except:
                pass


def parse_book_sections(node, sections):
    for sec in sections:
        if sec.book == node.get_primary_title('en'):
            if node.get_primary_title('en') == "Psalms":
                sec.title_en = Ref(sec.title_en.replace("PSALM", "Psalms")).normal()
                sec.title_he = Ref(sec.title_en).he_normal()

            ref = f"Introduction to Tanakh, {node.get_primary_title('en')}"
            intro_links[ref].append(sec.ref)
            for p in ["<footnote.*?>", "<notes.*?>"]:
                for m in re.findall(p, sec.comm_en):
                    sec.comm_en = sec.comm_en.replace(m, "")
                for m in re.findall(p, sec.comm_he):
                    sec.comm_he = sec.comm_he.replace(m, "")
            if sec.comm_en != "":
                intro_text[ref].append(f"<b>{sec.title_en}</b><br/>{sec.comm_en}")
            else:
                intro_text[ref].append(f"<b>{sec.title_en}</b>")
            if sec.comm_he != "":
                he_intro_text[ref].append(sec.comm_he)
            else:
                he_intro_text[ref].append(f"<b>{sec.title_en}</b>")

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
            print(row)
            continue
        range_eng = range_eng.replace("chaps. ", "").replace("The Song of", "Song of")
        book = Ref(range_eng).index.title
        if book not in books:
            books.append(book)
        sections.append(Section(book, range_eng, sec, title_en, title_he, comm_en, comm_he))
creating_intro = True
if creating_intro:
    intro = SchemaNode()
    intro.add_primary_titles("Introduction to Tanakh", 'הקדמה לתנ״ך')
    intro.key = "Introduction to Tanakh"
    for b in books:
        node = create_intros(b)
        parse_book_sections(node, sections)
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
perakim = [len(library.get_index(b).all_section_refs()) for b in books]
cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz"]
c = Category()
c.path = cats
c.add_shared_term("Steinsaltz")
base_heb = 0
base_en = 0
heb_words = 0
en_words = 0
try:
    c.save()
except:
    pass
#
# for b in library.get_indexes_in_category("Steinsaltz", include_dependant=True):
#     b = library.get_index(b)
#     if "Tanakh" not in b.categories:
#         continue
#     if "I Samuel" not in b.title:
#         continue
#     b.versionState().refresh()
#     base = library.get_index(b.title.replace("Steinsaltz Commentary on ", "")).all_section_refs()
#     comm = b.all_section_refs()
#     #assert len(comm) == len(base), f"{len(comm)} vs {len(base)}"
#     for r in b.all_section_refs():
#         base = Ref(r.normal().replace("Steinsaltz Commentary on ", "")).all_segment_refs()
#         comm = r.all_segment_refs()
#         if len(comm) != len(base):
#             print(r)
#             print(f"{len(comm)} vs {len(base)}")
# print()
def get_substrings(input_string, length=5):
    return [input_string[i: i + length] for i in range(len(input_string) - length + 1)]

steinsaltz_longer = []
steinsaltz_shorter = []
with open("nach_content_export - nach_content_export (2).csv", 'r') as f:
    rows = csv.reader(f)
    rows = list(rows)
    steinsaltz = 'ביאור שטיינזלץ'
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
                    print(f"{curr_book} => {r}")
                    section_id = str(int(sec.id) + 1)
                    continue
                curr_ref = seg_refs[ref_in_section[curr_range]-1]
                #if curr_ref.normal() == "Joshua 21:36":
                #    curr_ref = curr_ref.next_segment_ref().next_segment_ref()
                while curr_ref.sections[1] < int(posuk_num):
                    print(f'Difference in length: {curr_ref}')
                    curr_ref = curr_ref.next_segment_ref()
                    ref_in_section[curr_range] += 1
                while curr_ref.sections[1] > int(posuk_num):
                    print(f'Difference in length: {curr_ref}')
                    curr_ref = Ref(curr_ref.prev_segment_ref().normal().replace(":" + prev_posuk_num, ":" + posuk_num))
                    ref_in_section[curr_range] -= 1
                prev_posuk_num = posuk_num
                break
        if prev_book != curr_book:
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
            prev_book = curr_book
            try:
                Index(indx).save()
            except:
                pass

        for x in re.findall(":[א-ת]{1}", text_ftnote):
            text_ftnote = text_ftnote.replace(x, f": {x[1]}")
        for p in ["<footnote.*?>", "<notes.*?>"]:
            for m in re.findall(p, text_ftnote):
                text_ftnote = text_ftnote.replace(m, "")
            for m in re.findall(p, text_en):
                text_en = text_en.replace(m, "")

        tc = TextChunk(Ref(f"Steinsaltz Commentary on {curr_ref.normal()}"), lang='he', vtitle="Steinsaltz he")
        tc.text = text_ftnote
        heb_words += text_ftnote.count(" ")
        base_heb += curr_ref.text('he').text.count(" ")
        #tc.save(force_save=True)
        tc = TextChunk(Ref(f"Steinsaltz Commentary on {curr_ref.normal()}"), lang='en', vtitle="Steinsaltz en")
        tc.text = text_en
        for lang, k in [('he', text_ftnote)]:  # , ('en', text_en)]:
            # for word in k.split():
            #     if word.find("<b>") > 0 and word[3+word.find("<b>"):] != "":
            #         print(word)
            from sefaria.utils.hebrew import strip_nikkud

            real_words_list = re.findall("<b>(.*?)</b>", k)
            outside_words = [x for x in re.findall("</b>(.*?)<b>", k) if x != strip_nikkud(strip_cantillation(x))]
            more_than_one_letter = 0
            streaks = False
            for words in outside_words:
                if not streaks:
                    substrings = get_substrings(words, length=7)
                    for s in substrings:
                        if len(s) == 7 and punctuation_regex.sub('', s) in str(real_words_list):
                            streaks = True
                            break
                for char in words:
                    if strip_nikkud(strip_cantillation(char)) != char:
                        more_than_one_letter += 1

            if streaks:
                steinsaltz_shorter.append([curr_ref.normal(), k, curr_ref.text(lang).text])
            if more_than_one_letter > 2: steinsaltz_longer.append([curr_ref.normal(), k, curr_ref.text(lang).text])
        #tc.save(force_save=True)
    for v in VersionSet({"versionTitle": "Steinsaltz en"}).array()+VersionSet({"versionTitle": "Steinsaltz he"}).array():
        library.get_index(v.title).versionState().refresh()
        v.versionSource = "https://www.sefaria.org"
        v.save()

with open("issues.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(steinsaltz_longer)


print(steinsaltz_longer)
with open("streaks.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(steinsaltz_shorter)
