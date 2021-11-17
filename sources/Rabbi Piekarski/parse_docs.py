from sources.functions import *
text = defaultdict(str)
text["Ketubot"] = defaultdict(str)
for path in Path('Kesubos').rglob('*.docx'):
    match = re.search("^(\d+[ab]{1})(\d+)", path.stem.split()[0])
    if match:
        orig_daf = match.group(1)
        daf = AddressTalmud(0).toNumber("en", orig_daf)
        segment_refs = [r.normal() for r in Ref("Tosafot on Ketubot {}".format(orig_daf)).all_segment_refs()]
        try:
            comm_num = segment_refs[int(match.group(2)) - 1]
            text["Ketubot"][comm_num] = ""
            html = docx2python(str(path), html=True)
            for el in html.body[0][0][0]:
                result = bleach.clean(el, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
                text["Ketubot"][comm_num] += result + "<br/>"
        except:
            print("Problem with {}".format(orig_daf))
#
# for book in text:
#     send_text = {
#         "language": "en",
#         "versionTitle": "Rabbi Piekarski",
#         "versionSource": "https://www.sefaria.org",
#         "text": ""
#     }
#     for ref in text[book]:
#         send_text["text"] = text[book][ref]
#         post_text(ref, send_text, server="http://localhost:8000")