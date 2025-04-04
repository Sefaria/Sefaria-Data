from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import match_text
import time
from fuzzywuzzy import fuzz
import requests
import base64
import copy
from sefaria.system.database import db
def get_segments(text):
    if not text:
        yield []
    elif type(text) == dict:
        yield from get_segments(text.values())
    elif first_type(text) == str:
        yield text
    else:
        for a in text:
            yield from get_segments(a)

def first_type(array):
    for x in array:
        if x:
            return type(x)

i = 0
imgs = {}
# col = db.texts
# doc_ids = [d['_id'] for d in col.find({})]
# for idd in doc_ids:
#     doc = col.find_one({'_id': idd})
#     new = copy.deepcopy(doc)
#     for array in get_segments(new['chapter']):
#         for x in array:
#             if "<img>" in x:
#                 print(new['title'])
# refs = library.get_index("The Five Books of Moses, by Everett Fox").all_segment_refs()
# for ref in refs:
#     temp = re.findall("<img.*?>", TextChunk(ref, lang='en').text)
#     if len(temp) > 0:
#         imgs[ref] = temp
#         url = f"https://storage.googleapis.com/sefaria-in-text-images/The%20Five%20Books%20of%20Moses%2C%20by%20Everett%20Fox/Art_P{i + 1}.jpg"
#         print(url)
#         data = requests.get(url)
#         b64 = base64.b64encode(data.content)
#         tc = TextChunk(ref, lang='en', vtitle='The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995')
#         tc.text = tc.text.replace("<img>", f"<img src='data:image/{b64}'/>")
#         print(tc.text)
#         tc.save(force_save=True)
#         i += 1
#         print(temp[0])


def get_phrase(curr_line, k, v):
    phrase_tuple = match_text(curr_line.split(), [k], dh_extract_method=lambda x: x, lang='en')['match_text'][0]
    new, old = phrase_tuple
    phrase = new
    if phrase != "":
        v = v.replace("<b>"+re.sub(r'\\(.)', r'\1', old), f"<b>{phrase}")
        return phrase, v
    else:
        max_i = -1
        max_line = ""
        k_num_words = k.count(" ")+1
        line_num_words = curr_line.count(" ")+1
        words = curr_line.split(" ")
        for word_pos in range(0, line_num_words, k_num_words):
            these_words = " ".join(words[word_pos:word_pos+k_num_words])
            ratio = fuzz.ratio(these_words, k)
            if ratio > max_i:
                max_i = ratio
                max_line = these_words

        if max_i > 85:
            return max_line, v
        else:
            return None, None


def dher(x):
    result = re.sub("<b>(.*?)</b>.*", "\g<1>", x).replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
    return bleach.clean(result, tags=[], strip=True)


def dher3(x):
    result = re.sub("<b>(.*?)</b>.*", "\g<1>", x).replace(":", "")#.replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "").replac
    result = re.escape(result)
    result = result.replace('\\ …\\ ', '.*?').replace('…', '.*?')
    return bleach.clean(result, tags=ALLOWED_TAGS, strip=True)


def dher2(s):
    s = s.replace("… :", "").strip()
    poss = dher(s).split("…")[-1].strip()
    if poss == "":
        return dher(s).split("…")[0].strip()
    return poss

book = -1
books = ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings"]
with open("The Early Prophets Just Translation.csv", 'r') as f:

    # if new chapter, dont add anything until we get to "\d .*?".  then we check to see if it has <bold> tags to decide if it's a footnote
    # all the while, we
    reader = csv.reader(f)
    text = defaultdict(dict)
    ftnotes = defaultdict(dict)
    for r, row in enumerate(reader):#'Have I not commanded you:<br>be strong and courageous!?<br>Do not be terrified, do not be dismayed<sup>•</sup><i class="footnote"><b>be dismayed:</b> Or “be shattered.”</i>,<br>for with you is Y<small>HWH</small> your God, wherever you go!'
        ref, comm = row
        if re.search("^Chapter \d+. ", comm):
            text_parsing = False
            ftnotes_parsing = False
        elif re.search("^\d+:?\d* <b>.*?</b>", comm):
            ftnotes_parsing = True
            text_parsing = False
        elif comm.find("__") == 0:
            ftnotes_parsing = True
            text_parsing = False
            continue
        elif re.search("^\d+:?\d* ", comm):
            text_parsing = True
            ftnotes_parsing = False

        if re.search("^1:1 ", comm) and text_parsing:
            book += 1
            ch = 0
            text_parsing = True
            ftnotes_parsing = False
            ftnotes_ch = 0
            text[books[book]] = {}
            ftnotes[books[book]] = {}

        if text_parsing:
            ch_w_verse = re.search("^(\d+):(\d+) (.*)", comm)
            v_only = re.search("^(\d+) (.*)", comm)
            if ch_w_verse:
                ch = int(ch_w_verse.group(1))
                if ch not in text[books[book]]:
                    text[books[book]][ch] = {}
                v = ch_w_verse.group(2)
                comm = ch_w_verse.group(3)
            elif v_only:
                v = v_only.group(1)
                comm = v_only.group(2)
            v = int(v)
            if v in text[books[book]][ch]:
                comm = text[books[book]][ch][v]+"<br/>"+comm
            text[books[book]][ch][v] = comm
        elif ftnotes_parsing and re.search("^\d+:?\d* <b>.*?</b>", comm):
            ch_w_verse = re.search("^(\d+):(\d+) (.*)", comm)
            v_only = re.search("^(\d+) (.*)", comm)
            if ch_w_verse:
                ftnotes_ch = int(ch_w_verse.group(1))
                ftnotes[books[book]][ftnotes_ch] = {}
                ftnotes_v = int(ch_w_verse.group(2))
                curr_comm = ch_w_verse.group(3)
            elif v_only:
                ftnotes_v = int(v_only.group(1))
                curr_comm = v_only.group(2)
            ftnotes_v = int(ftnotes_v)
            if ftnotes_v not in ftnotes[books[book]][ftnotes_ch]:
                ftnotes[books[book]][ftnotes_ch][ftnotes_v] = []
            dhs = re.findall("<b>.*?</b> .*?", curr_comm)
            comms = re.split("<b>.*?</b> ", curr_comm)[1:]
            assert len(dhs) == len(comms)
            for x, y in zip(dhs, comms):
                ftnotes[books[book]][ftnotes_ch][ftnotes_v].append(x+y)



bad_results = []
not_found = []
bad = 0
ITAG_HOLDER = "$#%^!" # characters that dont occur in text hold place of itags during iteration
total = 0
probs = []
consecutives = []
for book in books:
    our_book = book.replace("Ii", "II")
    diff = len(library.get_index(our_book).all_section_refs()) - len(text[book].keys())
    if diff != 0:
        print(book)
        print(f"{diff} chapters differ")
    with open(f"{book}.csv", 'w') as f:
        writer = csv.writer(f)
        for ch in text[book]:
            diff = len(Ref(f"{our_book} {ch}").all_segment_refs()) - len(text[book][ch])
            if diff != 0:
                print(f"{diff} more verses: {our_book} {ch}")
                max_i = 0
                max_line = -1
                for l, line in enumerate(convertDictToArray(text[book][ch])):
                    jps = TextChunk(Ref(f"{book} {ch}:{l + 1}"), lang='en').text.replace("<br>", " ").replace("<br/>", " ").replace("  ", " ")
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
                    curr = (order[0].count(" ") - order[1].count(" ")) / float(order[0].count(" "))
                    if curr > max_i:
                        max_i = curr
                        max_line = l
                print("***")
                print(f"{book} {ch}")
                print(text[book][ch][max_line])
                print(TextChunk(Ref(f"{book} {ch}:{max_line + 1}"), lang='en').text)
            text[book][ch] = convertDictToArray(text[book][ch])
            for p, pasuk in enumerate(text[book][ch]):
                if ch in ftnotes[book] and p+1 in ftnotes[book][ch]:
                    ftnote_dict = {dher3(x): x for x in ftnotes[book][ch][p+1]}
                    pos = 0
                    br_char = ""
                    curr_line = text[book][ch][p].replace("<br>", "<br/>").replace("<br/>", " <br/> ")
                    ftnote_positions = defaultdict(str)
                    i_tags = []
                    for k, v in ftnote_dict.items():
                        orig_v = v
                        phrase = re.search(k, curr_line)
                        if phrase is None:
                            phrase, v = get_phrase(curr_line, k, v)
                            if phrase == None == v:
                                probs.append([f"{book} {ch}:{p+1}", orig_v, text[book][ch][p]])
                        else:
                            phrase = phrase.group(0)
                        #         text[book][ch][p][word_num] = text[book][ch][p][word_num]+ITAG_HOLDER
                        #
                        if phrase is None:
                            continue
                        start = curr_line.find(phrase)
                        end = len(phrase)+start
                        if curr_line[end:].startswith(ITAG_HOLDER):
                            i_tags[-1] = i_tags[-1][:-4]
                            i_tags[-1] += v+"</i>"
                        else:
                            curr_line = curr_line[:end] + ITAG_HOLDER + curr_line[end:]
                            i_tags.append("<sup class='footnote-marker'>*</sup><i class='footnote'>" + v + "</i>")
                    curr_line = curr_line.replace(" <br/> ", "<br/>")
                    for i_tag in i_tags:
                        curr_line = curr_line.replace(ITAG_HOLDER, i_tag, 1)
                    text[book][ch][p] = curr_line
                    # orig = text[book][ch][p]
                    # base_words = bleach.clean(text[book][ch][p], tags=[], strip=True).replace("\n", "\n ").replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
                    # base_words = base_words.split()
                    # results = match_text(base_words, ftnotes[book][ch][p+1], dh_extract_method=dher2, lang='en')
                    # # if (-1, -1) in results["matches"]:
                    # #    results = match_text(base_words, ftnotes[book][ch][p+1], dh_extract_method=dher2, lang='en', prev_matched_results=results["matches"])
                    # # if (-1, -1) in results["matches"]:
                    # #     results = match_text(base_words, ftnotes[book][ch][p+1], dh_extract_method=dher3, lang='en', prev_matched_results=results["matches"])
                    # curr = 0
                    # total += len(results["matches"])
                    # i_tags = []
                    # text[book][ch][p] = text[book][ch][p].replace("\n", " <br/>")
                    # words = text[book][ch][p]
                    # text[book][ch][p] = text[book][ch][p].split()
                    # curr = 0
                    # for i, x in enumerate(results["matches"]):
                    #     ellipsis = [el.strip() for el in re.search("<b>(.*?)</b>", ftnotes[book][ch][p + 1][i]).group(1).split("…")]
                    #     ellipsis_or_not_found = False
                    #     if x == (-1, -1):
                    #         j = i
                    #         while j < len(results["matches"]) - 1 and results["matches"][j] == (-1, -1):
                    #             j += 1
                    #         end = results["matches"][j][1]
                    #         if end != -1:
                    #             end += 1
                    #         if curr >= 0 and end > curr:
                    #             phrase = " ".join(base_words[curr:end])
                    #         elif curr >= 0:
                    #             phrase = " ".join(base_words[curr:])
                    #         else:
                    #             phrase = " ".join(base_words)
                    #         if len(phrase) > 0 and phrase.find(results["match_text"][i][1]) >= 0:
                    #             ellipsis_or_not_found = True
                    #         else:
                    #             if f"{book} {ch}:{p+1} -- footnote {ftnotes[book][ch][p+1][i]} not found." not in not_found:
                    #                 not_found.append(f"{book} {ch}:{p+1} -- footnote {ftnotes[book][ch][p+1][i]} not found.")
                    #             bad_results.append(results["match_text"][i][1])
                    #
                    #     if ellipsis_or_not_found and len(results["match_text"][i][1]) > 0:
                    #         word_num = phrase.split(results["match_text"][i][1])[0].count(" ")+curr
                    #     else:
                    #         word_num = x[1]
                    #
                    #     if x != (-1, -1):
                    #         curr = x[1]
                    #     if word_num >= 0:
                    #         text[book][ch][p][word_num] = text[book][ch][p][word_num]+ITAG_HOLDER
                    #         i_tags.append("<sup>•</sup><i class='footnote'>" + ftnotes[book][ch][p + 1][i].strip() + "</i>")
                    #     else:
                    #         if f"{book} {ch}:{p + 1} -- footnote {ftnotes[book][ch][p + 1][i]} not found." not in not_found:
                    #             not_found.append(f"{book} {ch}:{p + 1} -- footnote {ftnotes[book][ch][p + 1][i]} not found.")
                    # text[book][ch][p] = " ".join(text[book][ch][p]).replace("\n", "<br/>")
                    # for i_tag in i_tags:
                    #     text[book][ch][p] = text[book][ch][p].replace(ITAG_HOLDER, i_tag, 1)

with open(f"ftnotes.csv", 'w') as f:
    writer = csv.writer(f)
    for p in probs:
        writer.writerow(p)
        # for ch in ftnotes[book]:
        #     pasukim = ftnotes[book][ch]
        #     for p, pasuk in enumerate(pasukim):
        #         writer.writerow([f"{book} {ch}:{p+1}", pasuk])

for book in text:
    send_text = {
        "language": "en",
        "versionSource": "https://www.penguinrandomhouse.com/books/55159/the-early-prophets-joshua-judges-samuel-and-kings-by-everett-fox/",
        "versionTitle": "The Early Prophets, by Everett Fox. New York, Schocken Books, 1995",
        "text": text[book]
    }
    for perek in text[book]:
        tc = TextChunk(Ref(f"{book} {perek}"), vtitle="The Early Prophets, by Everett Fox. New York, Schocken Books, 1995", lang='en')
        curr_tc = TextChunk(Ref(f"{book} {perek}"), vtitle="Tanakh: The Holy Scriptures, published by JPS", lang='en').text
        if len(tc.text) != len(curr_tc):
            print(f"{book} {perek}")
        tc.text = text[book][perek]
        tc.save(force_save=True)

for v in VersionSet({"versionTitle": "The Early Prophets, by Everett Fox. New York, Schocken Books, 1995"}):
    v.formatAsPoetry = True
    v.save()

for x in not_found:
    print(x)









    #
    #
    #
    #
    # book = 0
    # ch = 0
    # ftnote_ch = 0
    # ftnotes = defaultdict(dict)
    # ftnotes_bool = False
    # lines = list(reader)
    # prev_ftnote_verse = 0
    # prev_verse = 0
    # for r, row in enumerate(lines):
    #     ref, comm = row
    #     while book < len(books) and books[book] not in ref:
    #         book += 1
    #         ch = 0
    #         parsing = False
    #         ftnote_ch = 0
    #         text[book] = {}
    #     if comm.replace("_", "").strip() == "":
    #         continue
    #
    #     prev_ftnotes_bool = ftnotes_bool
    #     if re.search("^\d+-\d+", comm) is not None:
    #         print(comm)
    #     ftnotes_bool = bool(re.search("^\d+[:.]{1}\S+ .*?<b>", comm)) or bool(re.search("^\d+ .*?<b>", comm))
    #
    #     if ref.split()[-1].split(".")[-1] == '1':
    #         parsing = False
    #
    #     if re.search("^\d+[:.]{1}\S+ ", comm):
    #         parsing = True
    #         m = re.search("^(\d+)[:.]{1}(\S+) ", comm)
    #         verse = m.group(2)
    #         while not verse.isdigit():
    #             verse = verse[:-1]
    #         verse = int(verse)
    #         comm = comm.replace(m.group(0), "", 1).strip()
    #         if ftnotes_bool:
    #             ftnote_ch = int(m.group(1))
    #         else:
    #             ch = int(m.group(1))
    #
    #         which_ch = ftnote_ch if ftnotes_bool else ch
    #
    #
    #         if not ftnotes_bool:
    #             if ch not in text[books[book]]:
    #                 text[books[book]][which_ch] = []
    #             assert len(text[books[book]][which_ch]) == int(verse)-1
    #             verse -= len(text[books[book]][which_ch])
    #             while verse > 1:
    #                 text[books[book]][which_ch].append("")
    #                 verse -= 1
    #             text[books[book]][which_ch].append(comm)
    #         else:
    #             if ch not in ftnotes[books[book]]:
    #                 ftnotes[books[book]][which_ch] = {}
    #             comms = ["<b>"+c for c in comm.split("<b>")[1:]]
    #             ftnotes[books[book]][which_ch][int(verse)] = comms
    #             prev_ftnote_verse = int(verse)
    #     elif re.search("^\d+ ", comm) and ch >= 1:
    #         parsing = True
    #         verse = re.search("^(\d+) ", comm).group(1)
    #         if prev_ftnote_verse > int(verse) and ftnotes_bool:
    #             raise Exception
    #         comm = comm.replace(verse, "").strip()
    #         if not ftnotes_bool:
    #             text[books[book]][ch].append(comm)
    #             assert len(text[books[book]][ch]) == int(verse)
    #         else:
    #             comms = ["<b>" + c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
    #             ftnotes[books[book]][ftnote_ch][int(verse)] = comms
    #             prev_ftnote_verse = int(verse)
    #     elif ch >= 1 and parsing:
    #         if prev_ftnotes_bool:
    #             comms = ["<b>" + c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
    #             for comm in comms:
    #                 # ftnotes[books[book]][ftnote_ch][prev_ftnote_verse][-1] += "\n" + comm
    #                 ftnotes[books[book]][ftnote_ch][prev_ftnote_verse].append(comm)
    #         else:
    #             text[books[book]][ch][-1] += "\n" + comm
    #
    #


