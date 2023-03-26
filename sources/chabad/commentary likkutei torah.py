import csv
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import match_text
from tqdm import tqdm
ref_to_soup = defaultdict(str)
from sefaria.system.exceptions import InputError
seg_to_ref_dict = defaultdict(list)
def calcDataValue(letters):
    sum = 0
    for count, x in enumerate(letters.split(",")[::-1]):
        sum += getGematria(x)*pow(10, count)
    return sum

def get_next_parasha(title, parasha):
    if title == "Torah Ohr" and parasha == "Vayakhel":
        return Ref(f"{title}, Megillat Esther").all_segment_refs()
    elif title == "Torah Ohr" and parasha == "Megillat Esther":
        return []
    parshiyot = [x for x in TopicSet({"slug": {"$regex": "^parashat-"}}) if IntraTopicLink().load({"toTopic": "torah-portions", "fromTopic": x.slug})]
    parshiyot = sorted(parshiyot, key=lambda x: x.displayOrder)
    for p, curr in enumerate(parshiyot):
        parasha_ref = Ref("Parashat "+parasha) if not parasha.startswith("Megillat") else parasha
        if Ref(str(curr).replace("Beha'alotekha", "Beha'alotcha")) == parasha_ref:
            found = False
            while not found:
                try:
                    ref_to_return = Ref(f"{title}, {str(parshiyot[p+1])}").all_segment_refs()
                    found = True
                except:
                    p += 1
            return ref_to_return
    raise Exception

def seg_to_ref(name, parasha, seg, prev_ref, hosafot):
    if hosafot:
        parasha = parasha.replace(hosafot, "")
        supplements = "Supplements, "
    else:
        supplements = ""

    if len(parasha) > 0:
        try:
            parasha = Term().load({"titles.text": parasha}).get_primary_title('en')
        except Exception as e:
            print(parasha)
            parasha = Topic().load({"titles.text": parasha}).get_primary_title('en')
        prev_ref = ""
    elif len(prev_ref) > 0:
        parasha = Ref(prev_ref).index_node.get_primary_title('en')

    if seg == "":
        return (prev_ref, False)
    else:
        parasha = parasha.replace("Shmini Atzeret", "Shemini Atzeret").replace("Song of Songs", "Shir HaShirim").replace("Megilat Esther", "Megillat Esther")
        last_ref = Ref(f"{name}, {supplements}{parasha}").all_segment_refs()[-1]
        parasha_refs = Ref(f"{name}, {supplements}{parasha}").all_segment_refs() if prev_ref == "" else Ref(prev_ref).to(last_ref).range_list()
        next_refs = []
        if title == "Torah Ohr" and parasha == "Tetzaveh":
            next_refs = Ref("Torah Ohr, Parashat Zakhor").all_segment_refs()
        elif title == "Torah Ohr" and parasha == "Vayakhel":
            next_refs = Ref(f"{title}, Megillat Esther").all_segment_refs()
        seg = seg.replace(" ", "").strip()
        main_ref = Ref(f"{name}, {supplements}{parasha}")
        result = refs_to_value(parasha_refs, seg, main_ref)
        if result == -1:
            # assert len(prev_ref) > 0
            result = refs_to_value(next_refs, seg, main_ref)
            if result == -1:
                # print(f"Falling back on {prev_ref}")
                return (prev_ref, False)
            else:
                return (result, True)
        else:
            return (result, False)

def refs_to_value(refs, seg, main_ref):
    for ref in refs:
        soup = ref_to_soup[ref]
        if soup == "":
            i_tags = BeautifulSoup(ref.text('he').text).find_all("i")
            soup = [calcDataValue(i.attrs['data-value']) for i in i_tags if 'data-value' in i.attrs]
            ref_to_soup[ref] = soup
        segVal = calcDataValue(seg)
        for val in soup:
            if segVal <= val:
                return ref.normal()
    print(f"Can't find {seg} in {main_ref.normal()}")
    return -1



def parse(f, title, curr_parasha="", curr_segment="", curr_dh="", text={}):
    def add(parasha="", seg="", dh="", daf=""):
        last_dh, curr_text = which_dict[parasha][daf][seg][-1] if len(which_dict[parasha][daf][seg]) > 0 else ["", ""]
        curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
        if len(which_dict[parasha][daf][seg]) > 0:
            which_dict[parasha][daf][seg][-1] = [last_dh, curr_text]
        else:
            which_dict[parasha][daf][seg].append([last_dh, curr_text])


    new_parasha = False
    addenda = {}
    which_dict = text
    prev_ref = ""
    curr_daf = ""
    hosafot = ""
    rows = list(enumerate(csv.reader(f)))
    for r, row in rows:
        parasha, daf, dh, comm = row
        parasha = parasha.replace('אחרי', 'אחרי מות').replace('בחקותי', "בחוקתי")\
            .replace('פינחס', "פנחס").replace('תצא', 'כי תצא').replace('תבא', 'כי תבוא')\
            .replace('ר"ה', 'ראש השנה').replace('יוהכ"פ', "יום כיפור").replace('שמ"ע', 'שמיני עצרת').replace('מגלת אסתר', "מגילת אסתר")
        if "".join(row) == "":
            continue
        if 'הוספות' in parasha:
            # book = Ref(" ".join(prev_ref.replace(title + ", ", "").split()[:-1])).book
            # book_refs = []
            # for node in library.get_index(book).contents()["alts"]["Parasha"]["nodes"]:
            #     book_refs += Ref(f"{title}, {node['title']}").all_segment_refs()
            # seg = refs_to_value(book_refs, seg, Ref(f"{title}, {node['title']}"))
            # prev_ref = seg
            # if book not in addenda:
            #     addenda[book] = {}
            # addenda[book][seg] = {}
            # curr_text = addenda[book][seg].get("dh", "")
            # curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
            # addenda[book][seg][dh] = curr_text
            # which_dict = addenda
            hosafot = "Hosafot"
            prev_ref = ""
            curr_daf = ""
            curr_dh = ""

            continue

        if len(daf) > 0:
            curr_dh = ""


        temp, next_parasha_bool = seg_to_ref(title, parasha, daf, prev_ref, hosafot)
        if next_parasha_bool:
            parasha = " ".join(temp.replace(title, "").split(", ")[1].split()[:-1])
            print(f"Switched to {parasha}")
        if len(daf) > 0:
            seg_to_ref_dict[temp].append(daf)  # temp is ref, seg is dappim
        seg = temp
        prev_ref = seg

        if len(parasha) > 0:
            curr_parasha = hosafot+parasha
            which_dict[curr_parasha] = {}
            new_parasha = True
            curr_dh = ""
        else:
            new_parasha = False

        if len(daf) > 0 and daf not in which_dict[curr_parasha]:
            which_dict[curr_parasha][daf] = {}


        curr_daf = daf if len(daf) > 0 else curr_daf

        if len(curr_daf) > 0:
            if seg not in which_dict[curr_parasha][curr_daf]:
                which_dict[curr_parasha][curr_daf][seg] = []

            if len(dh) > 0:
                curr_dh = dh
                if curr_dh not in which_dict[curr_parasha][curr_daf][seg]:
                    which_dict[curr_parasha][curr_daf][seg].append((curr_dh, ""))

            add(parasha=curr_parasha, seg=seg, dh=curr_dh, daf=curr_daf)

        prev_row = row


    return (text, addenda)


def dher(dh):
    dh = dh.replace("— כו'", "")
    dh = dh.split(" — ")[0].replace(":", "").strip()
    return dh

def tokenizer(x):
    x = bleach.clean(x, strip=True, tags=[])
    return x.split()

if __name__ == "__main__":
    next_parasha_dict = {"Torah Ohr": [{"Vayakhel": "Megillat Esther"}, {"Tetzaveh": "Parashat Zachor"}]}
    torah_ohr = {"Introduction": {"1": {}}}
    # #
    title = "Torah Ohr"
    file = f"{title} Main Text2.csv"
    # with open("Torah Ohr Commentary.csv", 'r') as to:
    #     # to_text, to_addenda = parse_to(to, "Likkutei Torah", curr_parasha="Introduction", curr_segment="1", text=torah_ohr)
    #     to_text, to_addenda = parse(to, "Torah Ohr", curr_parasha="Introduction", curr_segment="1", text=torah_ohr)
    #

    #ref_to_soup = defaultdict(str)
    with open(f"{title} Commentary.csv", 'r') as lt:
        if title.startswith("Torah"):
            text, to_addenda = parse(lt, "Torah Ohr", curr_parasha="Introduction", curr_segment="1", text=torah_ohr)
        else:
            text, lt_addenda = parse(lt, title)



    # for text, file in [(to_text, "Torah Ohr Main Text2.csv")]:
                  # (to_text, "Likkutei Torah Main Text.csv"), (to_addenda, "Likkutei Torah Addenda.csv")]:
    lines = []
    for parasha in text:
        if parasha in ["Introduction", ""]:
            continue
        print(parasha)
        if "Hosafot" in parasha:
            parasha = parasha.replace("Hosafot", "")
            supplements = "Supplements, "
            continue
        else:
            supplements = ""
        term = Term().load({"titles.text": parasha})
        if term is None:
            term = Topic().load({"titles.text": parasha})
        try:
            parasha_ref = Ref(f"""{title}, {supplements}{term.get_primary_title('en').replace("Shmini Atzeret", "Shemini Atzeret")
                              .replace("Song of Songs", "Shir HaShirim").replace("Megilat Esther", "Megillat Esther")}""")
        except:
            parasha = parasha.replace("Shmini Atzeret", "Shemini Atzeret")
            parasha_ref = Ref(f"{title}, {supplements}{parasha}")

        last_ref = parasha_ref.all_segment_refs()[-1]
        last_found = ""
        dhs = []
        if len(supplements) > 0:
            parasha = "Hosafot"+parasha

        for d, daf in enumerate(text[parasha]):
            next_ref = None
            for base_ref in text[parasha][daf]:
                if next_ref is None:
                    if d == len(text[parasha]) - 1:
                        next_ref = Ref(
                            list(text[parasha][daf].keys())[0]).top_section_ref().last_segment_ref().normal()
                    else:
                        next_daf = list(text[parasha].keys())[d + 1]
                        next_daf_base_refs = list(text[parasha][next_daf].keys())
                        for next in next_daf_base_refs:
                            if Ref(next).top_section_ref().index_node.get_primary_title('en') in base_ref:
                                next_ref = next
                        assert next_ref is not None

                dhs, comms = list(zip(*text[parasha][daf][base_ref]))
                dhs = list(dhs)
                comms = list(comms)
                try:
                    tc = TextChunk(Ref(base_ref).to(Ref(next_ref)), lang='he')
                    results = match_ref(tc, dhs, dh_extract_method=dher, base_tokenizer=tokenizer)
                    count = -1
                    for dh, ref in list(zip(dhs, results["matches"])):
                        count += 1
                        ref = ref.normal() if ref else ""
                        lines.append([parasha, dh, ref, comms[count], daf])
                        if ref != "":
                            last_found = ref
                except Exception as e:
                    print(e)
                    print(base_ref)

    with open(file, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(lines)
