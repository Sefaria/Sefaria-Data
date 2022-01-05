from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *
def base_tokenizer(x):
    return x.split()

def dh_extract_method(x):
    return x

text = defaultdict(dict)
text["Ketubot"] = defaultdict(dict)
ftnotes = defaultdict(dict)
ftnotes["Ketubot"] = defaultdict(dict)
for path in Path('Kesubos').rglob('*.docx'):
    match = re.search("^(\d+[ab]{1})(\d+)", path.stem.split()[0])
    if match:
        orig_daf = match.group(1)
        daf = orig_daf
        if len(text["Ketubot"][daf].keys()) == 0:
            text["Ketubot"][daf] = defaultdict(str)
        html = docx2python(str(path), html=True)
        if html.footnotes == []:
            print("Issue with {}".format(path))
            continue
        ftnotes = []
        if len(html.body) > 1:
            print("Perhaps table in "+str(path))
            continue
        for i, el in enumerate(html.body[0][0][0]):
            result = bleach.clean(el, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True).replace("'", "׳")
            if i == 0:
                result = result.replace('–', "-")
                dh = result.split("-")[0].strip()
                dh = " ".join(re.sub("----footnote\d+----", "", bleach.clean(dh, strip=True, tags=[])).split()[:10])
                dh = dh.replace('(שייך לע"א)', "").replace("  ", " ").strip()
                result = result.replace("</b>", "").replace("<b>", "")
                result = result.replace('(שייך לע"א)', "").strip()
                result = f"<b>{result}</b>"
            else:
                if result.startswith("<b>") and result.endswith("</b>") and len(result.split("<b>")) == len(result.split("</b>")) == 2:
                    result = result.replace("<b>", "").replace("</b>", "")
                elif "<b>" in result and "</b>" in result and len(result.split("<b>")) == len(result.split("</b>")):
                    new_result = []
                    for line in result.split("</b>"):
                        if line.strip() == "":
                            continue
                        if line.startswith("<b>"):
                            line = line.replace("<b>", "", 1)
                        elif "<b>" in line:
                            line = "<b>"+line.replace("<b>", "</b>")
                        new_result.append(line)
                    orig_result = result
                    result = "".join(new_result)
                    if len(result.split("<b>")) != len(result.split("</b>")):
                        print(path.stem)
                        print(len(result.split("<b>")) - len(result.split("</b>")))
                elif "<b>" in result and "</b>" in result:
                    pass

                assert len(result.split("<b>")) == len(result.split("</b>"))

                for find in re.findall("<u>(.*?)</u>", result):
                    result = result.replace(f"<u>{find}</u>", f"<br/>{find[0].upper()}<small>{find[1:].upper()}</small>")
            text["Ketubot"][daf][dh] += result + "<br/>"

        ftnote_consecutive = 0
        for i, el in enumerate(html.footnotes[0][0][0]):
            if el.strip() != "" and not (el.startswith("footnote") and " " not in el):
                if ftnote_consecutive >= 1:
                    ftnotes[-1] += "<br/>"+el
                else:
                    ftnotes.append(el)
                ftnote_consecutive += 1
            else:
                ftnote_consecutive = 0

        ftnotes_in_text = re.findall("----footnote\d+----", text["Ketubot"][daf][dh])
        if len(ftnotes_in_text) == len(ftnotes):
            for i, ftnote in enumerate(ftnotes):
                if ftnote.startswith("<b>") and ftnote.endswith("</b>"):
                    ftnote = ftnote.replace("<b>", "", 1).replace("</b>", "", 1)
                ftnote = f"<sup>{i+1}</sup><i class='footnote'>{ftnote}</i>"
                text["Ketubot"][daf][dh] = re.sub("----footnote\d+----", ftnote, text["Ketubot"][daf][dh], count=1)
        elif len(ftnotes) > 0 or "----footnote" in text["Ketubot"][daf][dh]:
            print("Footnotes issue in {}".format(path))
            print(f"{len(ftnotes)} vs {len(ftnotes_in_text)}")

        start = -1
        end = 0
        prev_end = 0
        spans = []
        text["Ketubot"][daf][dh] = text["Ketubot"][daf][dh].replace("<br/>", " <br/>")
        for l, letter in enumerate(text["Ketubot"][daf][dh]):
            if re.search("[\u0591-\u05EA׳]+", letter):
                if start == -1:
                    start = l
                end = l + 1
            elif start >= 0:
                if start - prev_end > 1:
                    spans.append((prev_end, start, False))
                    spans.append((start, end, True))
                elif start - prev_end == 1:
                    prev_span_start = spans[-1][0]
                    spans[-1] = ((prev_span_start, end, True))
                else:
                    raise Exception
                prev_end = end
                start = -1
        if end > start >= 0:
            spans.append((start, end, True))
        if end != len(text["Ketubot"][daf][dh]):
            spans.append((end, len(text["Ketubot"][daf][dh]), False))

        chars = list(text["Ketubot"][daf][dh])
        count = 0
        # words_list = []
        # for span in spans:
        #     start, end, heb = span
        #     if heb:
        #         words = "".join(chars[start:end]).split()
        #         for word in words:
        #             words_list.append("<span dir='rtl'> " + word + " </span>")
        #     else:
        #         words_list.append("".join(chars[start:end]))
        # text["Ketubot"][daf][dh] = "".join(words_list)

for book in text:
    not_found = defaultdict(list)
    for daf in text[book]:
        dhs = list(text[book][daf].keys())
        base = TextChunk(Ref("Tosafot on {} {}".format(book, daf)), lang='he')
        matches = match_ref(base, dhs, base_tokenizer=base_tokenizer, dh_extract_method=dh_extract_method)
        for i, tuple in enumerate(matches["match_text"]):
            if tuple[0] == "":
                not_found[daf].append(tuple[1])
            else:
                text[book][daf][matches["matches"][i]] = text[book][daf][tuple[1]]
                text[book][daf].pop(tuple[1])


    for daf in not_found:
        prev_amud = AddressTalmud(0).toNumber('en', daf)-1
        prev_amud = AddressTalmud.toStr('en', prev_amud)
        next_amud = AddressTalmud(0).toNumber('en', daf)+1
        next_amud = AddressTalmud.toStr('en', next_amud)
        base = TextChunk(Ref("Tosafot on {} {}-{}".format(book, prev_amud, next_amud)), lang='he')
        matches = match_ref(base, not_found[daf], base_tokenizer=base_tokenizer, dh_extract_method=dh_extract_method, boundaryFlexibility=10000)
        for i, tuple in enumerate(matches["match_text"]):
            if tuple[0] == "":
                print(daf)
                print("Not finding {}".format(tuple[1]))
            else:
                text[book][daf][matches["matches"][i]] = text[book][daf][tuple[1]]
                text[book][daf].pop(tuple[1])

for book in text:
    send_text = {
        "language": "en",
        "versionTitle": "Piekarski Tosafot4",
        "versionSource": "https://www.sefaria.org",
        "text": ""
    }
    for daf in text[book]:
        for ref in text[book][daf]:
            send_text["text"] = text[book][daf][ref]
            post_text(ref.normal(), send_text, server="http://localhost:8000")