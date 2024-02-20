from sources.functions import *
from tqdm import tqdm
from sefaria.helper.link import rebuild_links_for_title

# with open("linked texts.json", 'r') as f:
#     linked_texts2 = json.load(f)
# with open("unlinked texts.json", 'r') as f:
#     unlinked_texts = json.load(f)
def parse(row):
    global refs_found
    masechet, perek, halacha, mapping, comment, link, base = row
    comment = re.sub("@(.*?)#", r"<b>\1</b>", comment)
    comment = comment.replace("@", "<b>").replace("#", "</b>")
    refs_found[link] += 1
    orig_link = link
    link = Ref(link).all_segment_refs()[0].normal()
    actual_ref = f"Sha'arei Torat Eretz Yisrael on {link}:{refs_found[orig_link]}"
    return actual_ref, comment

linked_texts = []
with open("sha'arei torat eretz yisrael - פירוש ראשי.csv", 'r') as f:
    for row in csv.reader(f):
        linked_texts.append(row)
t = Term()
t.add_primary_titles("Sha'arei Torat Eretz Yisrael", 'שערי תורת ארץ ישראל')
t.name = "Sha'arei Torat Eretz Yisrael"
try:
    t.save()
except:
    pass
c = Category()
c.add_shared_term("Sha'arei Torat Eretz Yisrael")
c.path = ["Talmud", "Yerushalmi", "Commentary", "Sha'arei Torat Eretz Yisrael"]
try:
    c.save()
except:
    pass
refs_found = Counter()
books = set()
for row in linked_texts:
    m = row[0]
    new_c = library.get_index(f"{m}").categories[-1]
    c = Category()
    c.path = ["Talmud", "Yerushalmi", "Commentary", "Sha'arei Torat Eretz Yisrael", new_c]
    if Category().load({"path": c.path}) is None:
        c.add_shared_term(new_c)
        try:
            c.save()
        except:
            pass
    he_base = library.get_index(f"{m}").get_title('he')
    he = f"שערי תורת ארץ ישראל על {he_base}"
    root = JaggedArrayNode()
    root.add_primary_titles(f"Sha'arei Torat Eretz Yisrael on {m}", he)
    root.key = f"Sha'arei Torat Eretz Yisrael on {m}"
    root.add_structure(["Chapter", "Halakhah", "Integer", "Integer"])
    indx = {"schema": root.serialize(), 'dependence': "Commentary", "base_text_titles": [m],
            'base_text_mapping': 'many_to_one',
            'title': root.key, 'categories': c.path, "collective_title": "Sha'arei Torat Eretz Yisrael"}
    books.add(root.key)
    try:
        Index(indx).save()
    except:
        pass

for row in tqdm(linked_texts):
    actual_ref, comment = parse(row)
    if '<sup class' in comment:
        print(actual_ref)
    comment = comment.replace('“footnote”', "'footnote'").replace('“footnote-marker”', "'footnote-marker'")
    tc = TextChunk(Ref(actual_ref), lang='he', vtitle="Jerusalem, 1940")
    tc.text = comment
    #tc.save()

linked_texts = []
with open("sha'arei torat eretz yisrael - השלמות.csv", 'r') as f:
    for row in csv.reader(f):
        linked_texts.append(row)

for row in tqdm(linked_texts):
    actual_ref, comment = parse(row)
    comment = comment.replace('“footnote”', "'footnote'").replace('“footnote-marker”', "'footnote-marker'")
    tc = TextChunk(Ref(actual_ref), lang='he', vtitle="Jerusalem, 1940")
    tc.text = "[<small>" + "השלמות" + ":</small> " + comment + "]"
    #tc.save()

for b in list(books):
    #rebuild_links_for_title(b, user=1)
    b = library.get_index(b)
    b.collective_title = "Sha'arei Torat Eretz Yisrael"
    b.save()
    for v in b.versionSet():
        print(v.versionTitle)
        b.versionSource = 'https://www.nli.org.il/he/books/NNL_ALEPH990020672990205171/NLI'
