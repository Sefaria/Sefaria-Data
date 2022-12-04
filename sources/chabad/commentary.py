import csv
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import match_text
from tqdm import tqdm
ref_to_soup = defaultdict(str)

def calcDataValue(letters):
    sum = 0
    for count, x in enumerate(letters.split(",")[::-1]):
        sum += getGematria(x)*pow(10, count)
    return sum

def seg_to_ref(name, parasha, seg, prev_ref):
    if len(parasha) > 0:
        parasha = Term().load({"titles.text": parasha}).get_primary_title('en')
    else:
        parasha = Ref(prev_ref).index_node.get_primary_title('en')

    if seg == "":
        return prev_ref
    else:
        last_ref = Ref(f"{name}, {parasha}").all_segment_refs()[-1]
        refs = Ref(f"{name}, {parasha}").all_segment_refs() if prev_ref == "" else Ref(prev_ref).to(last_ref).range_list()
        seg = seg.replace(" ", "").strip()
        for ref in refs:
            soup = ref_to_soup[ref]
            if soup == "":
                soup = [calcDataValue(i.attrs['data-value']) for i in BeautifulSoup(ref.text('he').text).find_all("i")]
                ref_to_soup[ref] = soup
            segVal = calcDataValue(seg)
            for val in soup:
                if segVal <= val:
                    return ref.normal()
        return ""

def parse(f, title, curr_parasha="", curr_segment="", curr_dh="", text={}):
    def add(parasha="", seg="", dh=""):
        curr_text = which_dict[parasha][seg].get(dh, "")
        curr_text = curr_text + "<br>" + comm if len(curr_text) > 0 else comm
        which_dict[parasha][seg][dh] = curr_text

    new_parasha = False
    addenda = {}
    which_dict = text
    prev_ref = ""
    for r, row in enumerate(csv.reader(f)):
        parasha, seg, dh, comm = row
        if "".join(row) == "":
            continue
        seg = seg_to_ref(title, parasha, seg, prev_ref)
        prev_ref = seg
        if 'הוספות' in parasha:
            which_dict = addenda
            title += ", Supplements,"
            if "Likkutei" in f.name:
                for parasha in text:
                    which_dict[parasha] = {}
                    for seg in text[parasha]:
                        which_dict[parasha][seg] = {}
                        for dh in text[parasha][seg]:
                            which_dict[parasha][seg][dh] = ""
                add(parasha=parasha, seg=seg, dh=dh)
            continue

        try:
            if len(parasha) > 0:
                curr_parasha = parasha
                which_dict[curr_parasha] = {}
                new_parasha = True
                curr_dh = ""
            else:
                new_parasha = False

            if len(seg) > 0:
                curr_segment = seg
                which_dict[curr_parasha][curr_segment] = {}
                curr_dh = ""
            elif new_parasha:
                print(f"{row}")
                which_dict[curr_parasha][curr_segment] = {}
                curr_dh = ""

            if len(dh) > 0:
                curr_dh = dh
                which_dict[curr_parasha][curr_segment][curr_dh] = ""

            add(parasha=curr_parasha, seg=curr_segment, dh=curr_dh)

            prev_row = row
        except Exception as e:
            print(e)
            print(f)
            print(r)
            print(row)
            print("***")

    for parasha in addenda:
        for seg in addenda[parasha]:
            bad_keys = []
            for dh in addenda[parasha][seg]:
                if len(addenda[parasha][seg][dh]) == 0:
                    bad_keys.append(dh)
            for k in bad_keys:
                addenda[parasha][seg].pop(k)
    return (text, addenda)


def dher(dh):
    dh = dh.replace("— כו'", "")
    dh = dh.split(" — ")[0].replace(":", "").strip()
    return dh

def tokenizer(x):
    x = bleach.clean(x, strip=True, tags=[])
    return x.split()

if __name__ == "__main__":

    with open("Likkutei Torah Commentary.csv", 'r') as lt:
        lt_text, lt_addenda = parse(lt, "Likkutei Torah")
    torah_ohr = {"Introduction": {"1": {}}}
    with open("Torah Ohr Commentary.csv", 'r') as to:
        to_text, to_addenda = parse(to, "Torah Ohr", curr_parasha="Introduction", curr_segment="1", text=torah_ohr)

    lines = {}
    for text, file in [(lt_text, "Likkutei Torah Main Text.csv"), (lt_addenda, "Likkutei Torah Addenda.csv"),
                  (to_text, "Torah Ohr Main Text.csv"), (to_addenda, "Torah Ohr Addenda.csv")]:
        lines[file] = []
        title = "Likkutei Torah" if "Likkutei" in file else "Torah Ohr"
        supplements = "," if "Main Text" in file else ", Supplements,"
        title += supplements

        for parasha in text:
            print(parasha)
            term = Term().load({"titles.text": parasha})
            parasha_ref = Ref(f"{title} {term.get_primary_title('en')}")
            tc = parasha_ref.text('he')
            last_ref = parasha_ref.all_segment_refs()[-1]
            last_found = ""
            dhs = []
            for seg in tqdm(lt_text[parasha]):
                dhs = list(lt_text[parasha][seg].keys())
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

