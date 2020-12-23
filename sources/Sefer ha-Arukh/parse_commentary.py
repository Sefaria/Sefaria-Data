from sources.functions import *
import bleach
dhs = {}
with open("Hafla'ah ShebaArakhin on Sefer HeArukh - he - Sefer HeArukh, Lublin 1883.csv", 'r') as f:
    for row in csv.reader(f):
        if row[0].startswith("Hafla'ah ShebaArakhin on Sefer HeArukh, Letter"):
            ref, comm = row
            sec_ref = ref.split(", ")[-1]
            sec_ref = " ".join(sec_ref.split()[:-1])
            if sec_ref not in dhs:
                dhs[sec_ref] = []
            word = re.search("<b>(.*?)</b>\s", comm)
            if word:
                word = word.group(1)
                dhs[sec_ref].append(bleach.clean(word, strip=True))

prev_sec_ref = ""
last_found = 0
prev_last_found = 0
links = []
not_found = []
with open("Sefer HeArukh - he - Sefer HeArukh, Lublin 1883.csv", 'r') as f:
    for row in csv.reader(f):
        if row[0].startswith("Sefer HeArukh, Letter"):
            ref, comm = row
            sec_ref = ref.split(", ")[-1]
            sec_ref = " ".join(sec_ref.split()[:-1])
            if sec_ref != prev_sec_ref:
                last_found = 0
            word = re.search("<b>(.*?)</b>\s", comm)
            if word:
                word = bleach.clean(word.group(1), strip=True)
                for i, dh in enumerate(dhs[sec_ref][last_found:]):
                    if dh == word:
                        last_found = i+1+last_found
                        if last_found > prev_last_found + 1:
                            not_found += dhs[sec_ref][prev_last_found+1:last_found-1]
                        haflaah_ref = "Hafla'ah ShebaArakhin on Sefer HeArukh, {} {}".format(sec_ref, last_found)
                        links.append({"refs": [ref, haflaah_ref], "generated_by": "haflaah_to_sefer_hearukh", "type": "Commentary", "auto": True})
                        prev_last_found = last_found

            prev_sec_ref = sec_ref
for word in set(not_found):
    print(word)
print(len(links))
#post_link(links)



