from sources.functions import *
from docx2python import docx2python
from bs4 import BeautifulSoup
#allowed = ('i', 'b', 'br', 'u', 'strong', 'em', 'big', 'small', 'img', 'sup', 'a')

def get_body_html(document, ftnotes):
    new_body = {}
    book = ""
    curr_perek = 0
    last_perek = []
    total = 0
    body = document.body[0][0][0]
    for c, comment in enumerate(body):
        comment = comment.replace("1 Kings", "I Kings").replace("2 Kings", "II Kings")
        if len(comment) > 0 and is_index(BeautifulSoup(comment).text):
            last_perek = new_body[book].get(curr_perek, []) if len(book) > 0 else []
            book = comment
            new_body[book] = {}
            total += curr_perek
            curr_perek = 0
        elif len(book) > 0 and not comment.startswith("BOOK"):
            if comment.strip().isdigit():
                if int(curr_perek) > 0 and len(Ref(f"{book} {curr_perek}").all_segment_refs()) != len(new_body[book][curr_perek]):
                    max = 0
                    max_line = -1
                    for l, line in enumerate(new_body[book][curr_perek]):
                        jps = TextChunk(Ref(f"{book} {curr_perek}:{l+1}"), lang='en', vtitle='Tanakh: The Holy Scriptures, published by JPS').text.replace("<br>", " ").replace("<br/>", " ").replace("  ", " ")
                        line = line.replace("<br>", " ").replace("<br/>", " ").replace("  ", " ")
                        jps = BeautifulSoup(jps)
                        line = BeautifulSoup(line)
                        for x in line.findAll('sup'):
                            x.decompose()
                        for x in jps.findAll('sup'):
                            x.decompose()
                        for x in line.findAll("i", {"class": "footnote"}):
                            x.decompose()
                        for x in jps.findAll("i", {"class": "footnote"}):
                            x.decompose()
                        line = line.text
                        jps = jps.text
                        order = (line, jps) if line.count(" ") > jps.count(" ") else (jps, line)
                        curr = (order[0].count(" ")-order[1].count(" "))/float(order[0].count(" "))
                        if curr > max:
                            max = curr
                            max_line = l
                    print("***")
                    print(f"{book} {curr_perek}")
                    print(new_body[book][curr_perek][max_line])
                    print(TextChunk(Ref(f"{book} {curr_perek}:{max_line+1}"), lang='en', vtitle='Tanakh: The Holy Scriptures, published by JPS').text)

                curr_perek = int(comment.strip())
                new_body[book][curr_perek] = []
            else:
                ftnoteholders = []
                comment = bleach.clean(comment, tags=['sup'], strip=True)
                marker = "$ftnoteholder$"
                for full_ftnote, char in re.findall("(----footnote\d+----(<sup>.*?</sup>|.{1}))", comment):
                    if char.startswith("<sup>"):
                        char = BeautifulSoup(char).text[0]
                    pasuk, ftnote_text = ftnotes[curr_perek][char][0]
                    ftnotes[curr_perek][char] = ftnotes[curr_perek][char][1:]
                    ftnoteholders.append(f"<sup class='footnote-marker'>{char}</sup><i class='footnote'>{ftnote_text}</i>")
                    comment = comment.replace(full_ftnote, marker)
                # for tag in allowed:
                #     m = re.search(f"<{tag}>(\\d+"+chr(160)+f")</{tag}>", comment)
                #     if m:
                #         comment = comment.replace(m.group(0), m.group(1))
                m = re.search(f"<sup>(\\d+" + chr(160) + f")</sup>", comment)
                if m:
                    comment = comment.replace(m.group(0), m.group(1))
                pasukim = re.split(f"\d+" + chr(160), comment)
                count = 0
                for p, pasuk in enumerate(pasukim):
                    pasuk = pasuk.strip()
                    if not pasuk:
                        continue
                    curr_markers = pasuk.count(marker)
                    for i in range(curr_markers):
                        pasuk = pasuk.replace(marker, ftnoteholders[count:][i])
                    count += curr_markers
                    assert marker not in pasuk
                    assert "-footnote" not in pasuk
                    if pasukim[0].strip() != "" and p == 0:
                        if len(new_body[book][curr_perek]) == 0:
                            print(comment)
                        else:
                            new_body[book][curr_perek][-1] += "<br/>" + pasuk
                    else:
                        new_body[book][curr_perek].append(pasuk)



                assert len(ftnoteholders[count:]) == 0
    return new_body



def get_footnotes(document):
    ftnotes = list(document.footnotes[0][0])
    new_ftnotes = {}
    last_ftnote = ""
    curr = 0
    prev = ""
    perek = 0
    for i, ftnote in enumerate(ftnotes):
        ftnote = ftnote[0]
        if not ftnote:
            continue
        try:
            soup = BeautifulSoup(ftnote)
            ftnote = bleach.clean(soup.find("span").parent, strip=True, tags=["span"]) # ----footnote1----<sup>a</sup>
            ftnote = ftnote.replace(re.search("^footnote\d+\)", ftnote).group(0), "").strip()
            spans = ftnote.count("<span>") - 1
            for span in range(spans):
                ftnote = ftnote.replace("<span>", "", 1)
                ftnote = ftnote.replace("</span>", "", 1)
            assert "<span>" in ftnote and "</span>" in ftnote
            ftnote = ftnote.replace('–', "-").strip()
            basic_pattern = re.search("^(.{1})\s?([\d.-]{1,})\.([\d.-]{1,})\s(.{1,})", ftnote)
            dash_pattern = re.search("([a-z]{1})-[a-z]{1} (.+)", ftnote)
            pattern = basic_pattern if basic_pattern else dash_pattern
            if pattern:
                char = pattern.group(1)
                perek = int(pattern.group(2).split(".")[0])
                pasuk = pattern.group(3)
                comment = "<b>" + pattern.group(4).replace("<span>", "</b>").replace("</span>", "")
                if perek not in new_ftnotes:
                    new_ftnotes[perek] = defaultdict(list)
                new_ftnotes[perek][char[0:1]].append((pasuk, comment))
                last_ftnote = char
            else:
                pass
                # ftnote = chr(ord(last_ftnote)+1)
                # last_ftnote = ftnote
        except:
            pass

        prev = ftnote
    return new_ftnotes

x = {}
for f in os.listdir("RJPS"):
    if not f.endswith("docx"):
        continue
    start_at = 0
    document = docx2python("RJPS/"+f, html=True)
    ftnotes = get_footnotes(document)
    data = get_body_html(document, ftnotes)
    x.update(data)
    for book in data:
        for perek in data[book]:
            send_text = {"language": "en", "versionTitle": "RJPS", "versionSource": "https://www.jps.org", "text": data[book][perek]}
            post_text(f"{book} {perek}", send_text, server="http://localhost:8000")

for b in tqdm(x):
    diff = len(x[b]) - len(library.get_index(b).all_section_refs())
    if diff != 0:
        print(b)
    for perek in x[b]:
        diff = len(x[b][perek]) - len(Ref(f"{b} {perek}").all_segment_refs())
        if diff != 0:
            print(f"{b} {perek} -> {diff}")
        for p, pasuk in enumerate(x[b][perek]):
            tc = TextChunk(Ref(f"{b} {perek}:{p+1}"), lang='en', vtitle='RJPS_1st_pass')
            tc.text = pasuk
            tc.save()

for v in VersionSet({"versionTitle": 'RJPS_1st_pass'}):
    v.versionSource = "https://www.sefaria.org"
    v.save()


ftnotes = {}
increment_perek = 0
heb_uncertain = 0
with open("ftnotes.csv", 'r') as f:
    for row in csv.reader(f):
        heb_uncertain = 0
        if row[0] == "increment":
            increment_perek += 1
        elif row[0] == "decrement":
            increment_perek -= 1
        else:
            perek, ftnote, comm = row
            perek = int(perek) + increment_perek
            if perek not in ftnotes:
                ftnotes[perek] = {}
            ftnotes[perek][ftnote] = comm