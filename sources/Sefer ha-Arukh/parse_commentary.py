from sources.functions import *
import bleach
haflaahs = ["Hafla'ah ShebaArakhin on Sefer HeArukh - he - Sefer HeArukh, Lublin 1883.csv", "hafla'ah last half.csv"]
for haflaah in haflaahs:
    dhs = {}
    prev_word = ""
    with open(haflaah, 'r') as f:
        for row in csv.reader(f):
            if row[0].startswith("Hafla'ah ShebaArakhin on Sefer HeArukh, Letter"):
                ref, comm = row
                sec_ref = ref.split(", ")[-1]
                sec_ref = " ".join(sec_ref.split()[:-1])
                if sec_ref not in dhs:
                    dhs[sec_ref] = []
                word = re.search("<b>(.*?)</b>\s(.*?)\s", comm)
                if word:
                    #word = word.group(1) + " " + word.group(2)
                    #dhs[sec_ref].append(bleach.clean(word, strip=True))
                    second_word = bleach.clean(word.group(2), strip=True)
                    word = bleach.clean(word.group(1), strip=True)
                    if second_word.endswith("'") and len(second_word) <= 3:
                        dhs[sec_ref].append(word + " " + second_word)
                    else:
                        if prev_word == word:
                            last_num = getGematria(dhs[sec_ref][-1].split()[-1]) + 1
                            dhs[sec_ref].append(word + " " + numToHeb(last_num) + "'")
                        else:
                            dhs[sec_ref].append(word + " א'")
                    prev_word = word

    prev_sec_ref = ""
    last_found = 0
    prev_last_found = 0
    links = []
    not_found = []
    prev_dh = "x x"
    prev_word = ""
    base_words = {}
    words_in_a_row = 0
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
                    if sec_ref not in base_words:
                        base_words[sec_ref] = []

                    if prev_word == word:
                        last_num = getGematria(base_words[sec_ref][-1].split()[-1]) + 1
                        base_words[sec_ref].append(word + " " + numToHeb(last_num) + "'")
                    else:
                        base_words[sec_ref].append(word + " א'")
                    prev_word = word
                    # for i, dh in enumerate(dhs[sec_ref][last_found:]):
                    #     if dh.split()[0] == word:
                    #         if dh.split()[0] == prev_dh.split()[0] and len(dh.split()[1]) in [1,2,3] and len(prev_dh.split()[1]) in [1,2,3]:
                    #             prev_num = getGematria(prev_dh.split()[1])
                    #             num = getGematria(dh.split()[1])
                    #             while num > prev_num + 1:
                    #                 num -= 1
                    #                 last_found += 1
                    #         last_found = i+1+last_found
                    #         if last_found > prev_last_found + 1:
                    #             not_found += dhs[sec_ref][prev_last_found+1:last_found-1]
                    #         haflaah_ref = "Hafla'ah ShebaArakhin on Sefer HeArukh, {} {}".format(sec_ref, last_found)
                    #         links.append({"refs": [ref, haflaah_ref], "generated_by": "haflaah_to_sefer_hearukh", "type": "Commentary", "auto": True})
                    #         prev_last_found = last_found
                    #         prev_dh = dh
                    #         break

                # prev_sec_ref = sec_ref
    for sec_ref in dhs:
        last_found = 0
        curr_dhs = dhs[sec_ref]
        for j, dh in enumerate(curr_dhs):
            # match = re.search(".*? (.){1}'", dh)
            # if match:
            #     num = getGematria(match.group(1))
            for i, base_word in enumerate(base_words[sec_ref]):
                if base_word == dh:
                    links.append({"refs": ["Sefer HeArukh, {} {}".format(sec_ref, i+2),
                                           "Hafla'ah ShebaArakhin on Sefer HeArukh, {} {}".format(sec_ref, j+1)],
                                  "type": "Commentary", "auto": True, "generated_by": "haflaah_to_sefer_hearukh"})
                    break



    for word in set(not_found):
        print(word)
    print(len(links))
    post_link_in_steps(links)



