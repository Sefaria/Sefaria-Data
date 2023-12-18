from sources.functions import *
from tqdm import tqdm
from sefaria.helper.link import rebuild_links_for_title

def fix(x):
    x = re.sub("<notes.*?>", "", x)
    x = re.sub("<foot.*?>", "", x)
    x = x.replace("</b><b>", "").replace("<b></b>", "")
    for b in re.findall("\S{2,}</b>\S{2,}", x):
        new_b = b.replace("</b>", "</b> ")
        x = x.replace(b, new_b)
    return x


cats = ["Tanakh", "Modern Commentary on Tanakh", "Steinsaltz"]
c = Category()
c.path = cats
c.add_shared_term("Steinsaltz")

try:
    c.save()
except:
    pass

torah_books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
perakim_count = [50, 90, 117, 153, 187]
def getBookByPerek(perek):
    perek = int(perek)
    # perakim_count = [Ref(x).as_ranged_segment_ref().toSections[0] for x in torah_books]
    # curr = 0
    # for i, p in enumerate(perakim_count):
    #     curr += p
    #     if i > 0:
    #         perakim_count[i] = curr
    for i, x in enumerate(perakim_count):
        if perek <= x:
            if i == 0:
                return (0, perek)
            else:
                return (i, perek-perakim_count[i-1])

books_dict = defaultdict()
en_text = defaultdict(defaultdict)
he_text = defaultdict(defaultdict)
books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
curr_book = 0
with open("chumash_content (1).csv", 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        _, _, perek, pasuk, heb_base, heb_comm, eng_comm = row
        eng_comm = fix(eng_comm)
        heb_comm = fix(heb_comm)
        book, perek = getBookByPerek(perek)
        if curr_book != book and book > 0:
            for p in en_text:
                en_text[p] = convertDictToArray(en_text[p])
                he_text[p] = convertDictToArray(he_text[p])
            he_text = convertDictToArray(he_text)
            en_text = convertDictToArray(en_text)
            books_dict[books[book-1]] = (en_text, he_text)
            en_text = defaultdict(defaultdict)
            he_text = defaultdict(defaultdict)
            curr_book = book
        perek = int(perek)
        pasuk = int(pasuk)
        en_text[perek][pasuk] = eng_comm
        he_text[perek][pasuk] = heb_comm

for p in en_text:
    en_text[p] = convertDictToArray(en_text[p])
    he_text[p] = convertDictToArray(he_text[p])
he_text = convertDictToArray(he_text)
en_text = convertDictToArray(en_text)
books_dict["Deuteronomy"] = (en_text, he_text)
en_text = defaultdict(defaultdict)
he_text = defaultdict(defaultdict)
steinsaltz = 'ביאור שטיינזלץ'

for curr_book in books_dict:
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
    try:
        Index(indx).save()
    except:
        pass
    en = TextChunk(Ref(f"Steinsaltz on {curr_book}"), vtitle="The Steinsaltz Tanakh - English", lang='en')
    he = TextChunk(Ref(f"Steinsaltz on {curr_book}"), vtitle="The Koren Steinsaltz Tanakh HaMevoar - Hebrew", lang='he')
    en.text = books_dict[curr_book][0]
    en.save(force_save=True)
    he.text = books_dict[curr_book][1]
    he.save(force_save=True)
    library.get_index(f"Steinsaltz on {curr_book}").versionState().refresh()
    rebuild_links_for_title(root.key, user=1)
    # for r in tqdm(library.get_index(f"Steinsaltz on {curr_book}").all_segment_refs()):
    #     # for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array() + VersionSet(
    #     #         {"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
    #     r = r.normal()
    #     en_stein = " ".join(r.split()[:-1])
    #     he_stein = library.get_index(en_stein).get_title('he')
    #     en_tanakh = " ".join(r.replace("Steinsaltz on ", "").split()[:-1])
    #     he_tanakh = library.get_index(en_tanakh).get_title('he')
    #     l = {"refs": [r.replace("Steinsaltz on ", ""), r],
    #          "auto": True, "type": "commentary", "generated_by": "steinsaltz_to_torah"}
    #     try:
    #         print(l['refs'])
    #         Link(l).save()
    #     except:
    #         print(l)
