from sources.functions import *
import string
from sefaria.helper.link import rebuild_links_for_title

with open('steinsaltz_rambam - section.csv') as f:
    section = list(csv.DictReader(f))
sections = [x for x in section if x['intro'] != "NULL"]
root = SchemaNode()
root.add_primary_titles("Steinsaltz Introductions to Mishneh Torah", 'ביאור שטיינזלץ, הקדמות ל'+'משנה תורה')
root.key = "Steinsaltz Introductions to Mishneh Torah"
text = {}
for sec in sections:
    for x, y in [("Yesodei HaTorah", "Foundations of the Torah"),
                 ('Second Tithes and Fourth Years Fruit', "Second Tithes and Fourth Year's Fruit")]:
        sec['name_eng'] = sec['name_eng'].replace(x, y)
    try:
        assert Ref(f"Mishneh Torah, {sec['name_eng']}")
    except Exception as e:
        print(e)
        continue
    node = JaggedArrayNode()
    node.add_primary_titles(sec['name_eng'], sec['name'])
    node.key = sec['name_eng']
    node.add_structure(["Paragraph"])
    root.append(node)
    text[node.key] = sec['intro']
root.validate()

indx = {"schema": root.serialize(),
           "title": root.key,
           "categories": ["Halakhah", "Mishneh Torah", "Commentary", "Steinsaltz"]}
try:
    Index(indx).save()
except:
    pass

for ref in text:
    tc = TextChunk(Ref(f"Steinsaltz Introductions to Mishneh Torah, {ref}"), vtitle='Steinsaltz Mishneh Torah', lang='he')
    text[ref] = [x.strip() for x in text[ref].split("<br>") if x.strip() != ""]
    tc.text = text[ref]
    #tc.save()

for v in VersionStateSet({'versionTitle': "Steinsaltz Mishneh Torah"}):
    v.refresh()
library.get_index("Steinsaltz Introductions to Mishneh Torah").versionState().refresh()
for ref in text:
    try:
        obj = {"refs": [Ref(f"Mishneh Torah, {ref}").as_ranged_segment_ref().normal(),
                        Ref(f"Steinsaltz Introductions to Mishneh Torah, {ref}").as_ranged_segment_ref().normal()],
               "auto": True, "type": "essay", "generated_by": "steinsaltz_essay_links_MT",
               "versions": [{"title": "ALL",
                             "language": "en"},
                            {"title": "ALL",
                             "language": "en"}],
               "displayedText": [{"en": Ref(f"Mishneh Torah, {ref}").as_ranged_segment_ref().normal(),
                                  "he": Ref(f"Mishneh Torah, {ref}").as_ranged_segment_ref().he_normal()},
                                 {"en": f"Steinsaltz Introductions to Mishneh Torah, {ref}",
                                  "he": Ref(f"Steinsaltz Introductions to Mishneh Torah, {ref}").he_normal()}]}
        l = Link(obj).save()
        obj = {"refs": [Ref(f"Steinsaltz on Mishneh Torah, {ref}").as_ranged_segment_ref().normal(),
                        Ref(f"Steinsaltz Introductions to Mishneh Torah, {ref}").as_ranged_segment_ref().normal()],
               "auto": True, "type": "essay", "generated_by": "steinsaltz_essay_links_MT",
               "versions": [{"title": "ALL",
                             "language": "en"},
                            {"title": "ALL",
                             "language": "en"}],
               "displayedText": [{"en": Ref(f"Steinsaltz on Mishneh Torah, {ref}").as_ranged_segment_ref().normal(),
                                  "he": Ref(f"Steinsaltz on Mishneh Torah, {ref}").as_ranged_segment_ref().he_normal()},
                                 {"en": f"Steinsaltz Introductions to Mishneh Torah, {ref}",
                                  "he": Ref(f"Steinsaltz Introductions to Mishneh Torah, {ref}").he_normal()}]}
        l = Link(obj).save()
    except Exception as e:
        print(e)
