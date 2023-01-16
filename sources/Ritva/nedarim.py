from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import *
import csv
import time

def base_t(str):
    return str.split()

def get_dh(line):
    if "@33" in line:
        match = re.search("@11(.*?)@33(.*)", line)
        dh = match.group(1)
        line = match.group(2)
    elif "." in line:
        match = re.search("@11(.*?\.) (.*)", line)
        dh = match.group(1)
        line = match.group(2)
    else:
        dh = " ".join(line.split()[0:5])
        line = " ".join(line.split()[5:])
    return (dh, line)


files = ["Ritva on Nedarim.txt"]
perakim = {}
dhs = {}
curr = 0
for f in files:
    print("NEW FILE")
    with open(f) as open_f:
        for line in open_f:
            if line.startswith("@00"):
                assert len(line.split()) == 2
                line = getGematria(line.split()[1])
                if line not in perakim:
                    perakim[line] = []
                    dhs[line] = []
                curr = line
            elif line.startswith("@11"):
                dh, line = get_dh(line)
                dhs[curr].append(dh)
                perakim[curr].append(line)
            elif line.startswith("@22"):
                line = removeAllTags(line)
                if perakim[curr]:
                    perakim[curr][-1] += "\n"+line
                else:
                    perakim[curr] = [line]
    start = time.time()
    with open("{}.csv".format(f), 'w') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(["Perek", "Text", "DH", "Match"])
        for perek, dhs_in_perek in dhs.items():
            now = time.time()
            tc = Ref("Nedarim, Chapter {}".format(perek)).text('he')
            print(len(dhs_in_perek))
            print(now-start)
            start = now
            results = match_ref(tc, dhs_in_perek, base_t)["matches"]
            counter = 0
            for dh, ref in zip(dhs_in_perek, results):
                text = perakim[perek][counter]
                match = ref if dh else ""
                writer.writerow([perek, text, dh, match])
                counter += 1

