from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import match_text

def dher(x):
    result = re.sub("<b>(.*?)</b>.*", "\g<1>", x).replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
    return bleach.clean(result, tags=[], strip=True)

def dher2(s):
    s = s.replace("… :", "").strip()
    poss = dher(s).split("…")[-1].strip()
    if poss == "":
        return dher(s).split("…")[0].strip()
    return poss


def dher3(s):
    return dher(s).split("…")[-1].strip()


ftnote_corrections = {}
with open("essay contents/ftnotes_compare_resolved.csv", 'r') as f:
    for row in list(csv.reader(f))[1:]:
        curr_ref, new_ref, new_text, curr_text, manual, ftnote = row
        if len(manual) > 0:
            pass
        elif len(new_ref) > 0:
            curr_text = new_text
        else:
            assert len(curr_text) > 0
            ftnote_corrections[curr_ref] = (new_text, curr_text)

ftnotes = defaultdict(list)
prev_ref = None
with open("essay contents/Torah_ftnotes_from_XML_corrected.csv", 'r') as f:
    rows = csv.reader(f)
    for row in rows:
        ref, comm = row[0].split()[:2], row[0].split()[2:]
        ref = " ".join(ref)
        try:
            if prev_ref:
                assert Ref(ref).follows(prev_ref)
        except:
            print(ref)
        comm = " ".join(comm)
        ftnotes[ref.replace(":", " ")] = ["<b>"+c for c in comm.split("<b>")][1:]


bad_results = []
not_found = defaultdict(list)
bad = 0
books_not_found = Counter()
ITAG_HOLDER = "$#%^!" # characters that dont occur in text hold place of itags during iteration
total = 0
with open("essay contents/torah_-_updated.csv", 'r') as f:
    text = {row[0]: row[1] for row in csv.reader(f)}
    orig_text = text
    for ref in text:
        text[ref] = text[ref].replace("<br/>", " <br/> ").replace("<br>", " <br> ")
        if ref in ftnotes:
            orig = text[ref]
            if ref in ftnote_corrections:
                text[ref] = text[ref].replace(ftnote_corrections[ref][1], ftnote_corrections[ref][0])
            base_words = bleach.clean(text[ref], tags=["br"], strip=True).replace("\n", " \n ").replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
            base_words = base_words.split()
            results = match_text(base_words, ftnotes[ref], dh_extract_method=dher2, lang='en')
            # if (-1, -1) in results["matches"]:
            #    results = match_text(base_words, ftnotes[ref][p+1], dh_extract_method=dher2, lang='en', prev_matched_results=results["matches"])
            # if (-1, -1) in results["matches"]:
            #     results = match_text(base_words, ftnotes[ref][p+1], dh_extract_method=dher3, lang='en', prev_matched_results=results["matches"])
            curr = 0
            total += len(results["matches"])
            i_tags = []
            text[ref] = text[ref].replace("\n", " <br/>")
            words = text[ref]
            text[ref] = text[ref].split()
            not_found_bool = []
            for i, x in enumerate(results["matches"]):
                ellipsis = [el.strip() for el in re.search("<b>(.*?)</b>", ftnotes[ref][i]).group(1).split("…")]
                ellipsis_or_not_found = False
                if x == (-1, -1):
                    j = i
                    while j < len(results["matches"]) - 1 and results["matches"][j] == (-1, -1):
                        j += 1
                    end = results["matches"][j][1]
                    if end != -1:
                        end += 1
                    if curr >= 0 and end > curr:
                        phrase = " ".join(base_words[curr:end])
                    elif curr >= 0:
                        phrase = " ".join(base_words[curr:])
                    else:
                        phrase = " ".join(base_words)
                    if len(phrase) > 0 and phrase.find(results["match_text"][i][1]) >= 0:
                        ellipsis_or_not_found = True
                    else:
                        if results["match_text"][i][1] not in not_found[ref]:
                            not_found[ref].append(results["match_text"][i][1])
                        bad_results.append(results["match_text"][i][1])
                        not_found_bool.append(i)

                if ellipsis_or_not_found and len(results["match_text"][i][1]) > 0:
                    word_num = phrase.split(results["match_text"][i][1])[0].count(" ")+curr
                else:
                    word_num = x[1]

                if x != (-1, -1):
                    curr = x[1]
                if word_num >= 0:
                    text[ref][word_num] = text[ref][word_num]+ITAG_HOLDER
                    i_tags.append("<sup>•</sup><i class='footnote'>" + ftnotes[ref][i].strip() + "</i>")
                else:
                    not_found_bool.append(i)
                    if results["match_text"][i][1] not in not_found[ref]:
                        not_found[ref].append(results["match_text"][i][1])

            if len(not_found_bool) > 0:
                for i, x in enumerate(results["matches"]):
                    if i in not_found_bool:
                        if results["match_text"][i][1] in " ".join(text[ref]):
                            words = " ".join(text[ref]).split(results["match_text"][i][1], 1)[0].split()
                            word_num = len(words)+results["match_text"][i][1].count(" ")+1
                            text[ref][word_num] = text[ref][word_num]+ITAG_HOLDER
                            i_tags.append("<sup>•</sup><i class='footnote'>" + ftnotes[ref][i].strip()+"</i>")
                            not_found[ref].remove(results["match_text"][i][1])
            text[ref] = " ".join(text[ref]).replace("\n", "<br/>")
            for i_tag in i_tags:
                text[ref] = text[ref].replace(ITAG_HOLDER, i_tag, 1)
with open("text.json", 'w') as f:
    json.dump(text, f)
with open("ftnotes_compare.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Ref", "Text", "Footnotes"])
    for ref in not_found:
        for f, ftnote in enumerate(list(set(not_found[ref]))):
            if f > 0:
                writer.writerow([ref, ftnote, '""'])
            else:
                writer.writerow([ref, ftnote, orig_text[ref]])