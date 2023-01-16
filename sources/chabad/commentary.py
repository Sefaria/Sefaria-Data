import csv
from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import match_text
from tqdm import tqdm
ref_to_soup = defaultdict(str)
from sefaria.system.exceptions import InputError
seg_to_ref_dict = {}
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

def seg_to_ref(name, parasha, seg, prev_ref):
    if len(parasha) > 0:
        parasha = Term().load({"titles.text": parasha}).get_primary_title('en')
        prev_ref = ""
    elif len(prev_ref) > 0:
        parasha = Ref(prev_ref).index_node.get_primary_title('en')

    if seg == "":
        return prev_ref
    else:
        next_parasha = get_next_parasha(name, parasha)
        last_ref = Ref(f"{name}, {parasha}").all_segment_refs()[-1]
        refs = Ref(f"{name}, {parasha}").all_segment_refs() if prev_ref == "" else Ref(prev_ref).to(last_ref).range_list()
        refs += next_parasha
        seg = seg.replace(" ", "").strip()
        result = refs_to_value(refs, seg, Ref(f"{name}, {parasha}"))
        if result == -1:
            assert len(prev_ref) > 0
            print(f"Falling back on {prev_ref}")
            return prev_ref
        else:
            return result

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

def parse_to(f, title, curr_parasha="", curr_segment="", curr_dh="", text={}):
    def add(parasha="", seg="", dh=""):
        last_dh, curr_text = which_dict[seg][-1] if len(which_dict[seg]) > 0 else ["", ""]
        curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
        if len(which_dict[seg]) > 0:
            which_dict[seg][-1] = [last_dh, curr_text]
        else:
            which_dict[seg].append([last_dh, curr_text])

    new_parasha = False
    addenda = {}
    which_dict = text
    prev_ref = ""
    rows = list(enumerate(csv.reader(f)))
    for r, row in rows:
        parasha, seg, dh, comm = row
        parasha = parasha.replace('אחרי', 'אחרי מות').replace('בחקותי', "בחוקתי")
        if "".join(row) == "":
            continue
        if 'הוספות' in parasha:
            # book = Ref(" ".join(prev_ref.replace(title + ", ", "").split()[:-1])).book
            # book_refs = []
            # for node in library.get_index(book).contents()["alts"]["Parasha"]["nodes"]:
            #     book_refs += Ref(f"{title}, {node['title']}").all_segment_refs()
            # seg = refs_to_value(book_refs, seg)
            # prev_ref = seg
            # if book not in addenda:
            #     addenda[book] = {}
            # addenda[book][seg] = {}
            # curr_text = addenda[book][seg].get("dh", "")
            # curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
            # addenda[book][seg][dh] = curr_text
            # which_dict = addenda
            return (text, addenda)

        if len(seg) > 0:
            curr_dh = ""

        temp = seg_to_ref(title, parasha, seg, prev_ref)
        if len(seg) > 0:
            seg_to_ref_dict[temp] = seg
        seg = temp
        prev_ref = seg

        if len(parasha) > 0:
            curr_parasha = parasha
            curr_dh = ""
        else:
            new_parasha = False

        if seg not in which_dict:
            which_dict[seg] = []

        if len(dh) > 0:
            curr_dh = dh
            which_dict[seg].append([curr_dh, ""])

        add(parasha=curr_parasha, seg=seg, dh=curr_dh)

        prev_row = row

    return (text, addenda)


def parse(f, title, curr_parasha="", curr_segment="", curr_dh="", text={}):
    def add(parasha="", seg="", dh=""):
        curr_text = which_dict[parasha][seg].get(dh, "")
        curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
        which_dict[parasha][seg][dh] = curr_text

    new_parasha = False
    addenda = {}
    which_dict = text
    prev_ref = ""
    rows = list(enumerate(csv.reader(f)))
    for r, row in rows:
        parasha, seg, dh, comm = row
        parasha = parasha.replace('אחרי', 'אחרי מות').replace('בחקותי', "בחוקתי")
        if "".join(row) == "":
            continue
        if 'הוספות' in parasha:
            book = Ref(" ".join(prev_ref.replace(title + ", ", "").split()[:-1])).book
            book_refs = []
            for node in library.get_index(book).contents()["alts"]["Parasha"]["nodes"]:
                book_refs += Ref(f"{title}, {node['title']}").all_segment_refs()
            seg = refs_to_value(book_refs, seg, Ref(f"{title}, {node['title']}"))
            prev_ref = seg
            if book not in addenda:
                addenda[book] = {}
            addenda[book][seg] = {}
            curr_text = addenda[book][seg].get("dh", "")
            curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
            addenda[book][seg][dh] = curr_text
            which_dict = addenda
            return (text, addenda)

        if len(seg) > 0:
            curr_dh = ""

        seg = seg_to_ref(title, parasha, seg, prev_ref)
        prev_ref = seg

        if len(parasha) > 0:
            curr_parasha = parasha
            which_dict[curr_parasha] = {}
            new_parasha = True
            curr_dh = ""
        else:
            new_parasha = False

        if seg not in which_dict[curr_parasha]:
            which_dict[curr_parasha][seg] = {}

        if len(dh) > 0:
            curr_dh = dh
            which_dict[curr_parasha][seg][curr_dh] = ""

        add(parasha=curr_parasha, seg=seg, dh=curr_dh)

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
    torah_ohr = {} # {"Introduction": {"1": {}}}
    #
    with open("Torah Ohr Commentary.csv", 'r') as to:
        to_text, to_addenda = parse_to(to, "Torah Ohr", curr_parasha="Introduction", curr_segment="1", text=torah_ohr)

    #ref_to_soup = defaultdict(str)
    # with open("Likkutei Torah Commentary.csv", 'r') as lt:
    #     lt_text, lt_addenda = parse(lt, "Likkutei Torah")


    lines = {}
    for text, file in [(lt_text, "Likkutei Torah Main Text.csv")]:
                  # (to_text, "Torah Ohr Main Text.csv"), (to_addenda, "Torah Ohr Addenda.csv")]:
        lines[file] = []
        title = "Likkutei Torah" if "Likkutei" in file else "Torah Ohr"
        supplements = "," if "Main Text" in file else ", Supplements,"
        title += supplements
        if title.startswith("Torah Ohr"):
            last_found = ""
            start = True
            for s, seg in enumerate(text.keys()):
                print(seg)
                if seg == "":
                    continue
                if "Torah Ohr, Vayetzei 1:9" in seg:
                    start = True
                if not start:
                    continue
                dhs = [x[0] for x in text[seg]]
                start_ref = Ref(seg)
                relevant_seg = seg_to_ref_dict[start_ref.normal()]
                last_segment_in_section = Ref(seg).section_ref().last_segment_ref()
                end_ref = Ref(list(text.keys())[s+1]) if s < len(text.keys()) - 1 else last_segment_in_section
                if end_ref.book != start_ref.book:
                    end_ref = last_segment_in_section
                try:
                    range_ref = start_ref.to(end_ref)
                except InputError as e:
                    range_ref = start_ref
                range_ref._ranged_refs = None
                tc = range_ref.text('he')
                commentary_comms = [x[1] for x in text[seg]]
                results = match_ref(tc, dhs, dh_extract_method=dher, base_tokenizer=tokenizer)
                for dh, comm, ref in list(zip(dhs, commentary_comms, results["matches"])):
                    ref = ref.normal() if ref else ""
                    lines[file].append([dh, ref, comm, relevant_seg])
                    if ref != "":
                        last_found = ref


        elif title.startswith("Likkutei"):
            for parasha in text:
                if parasha == "":
                    continue
                print(parasha)
                term = Term().load({"titles.text": parasha})
                parasha_ref = Ref(f"{title}, {term.get_primary_title('en')}")
                tc = parasha_ref.text('he')
                last_ref = parasha_ref.all_segment_refs()[-1]
                last_found = ""
                dhs = []
                for seg in tqdm(text[parasha]):
                    dhs = list(text[parasha][seg].keys())
                    results = match_ref(tc, dhs, dh_extract_method=dher, base_tokenizer=tokenizer)

                    for dh, ref in list(zip(dhs, results["matches"])):
                        ref = ref.normal() if ref else ""
                        lines[file].append([parasha, ref, seg, dh])
                        if ref != "":
                            last_found = ref
                    try:
                        from_ref = Ref(last_found).next_segment_ref()
                        to_ref = last_ref
                        print(from_ref)
                        print(to_ref)
                        tc = from_ref.to(to_ref).text('he')
                    except Exception as e:
                        print(e)


        with open(file, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(lines[file])

