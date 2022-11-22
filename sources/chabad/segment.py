import csv
from collections import defaultdict
from sources.functions import post_text
def check(lines, henay):
    for line in lines:
        if line.count(" ") > 175 and henay in line:
            pass

probs = []
total = 0
def cut_line(line, num, asdf = ". ו"):
    lines = [line]
    global total
    prob = False
    while len(lines) < len(line):
        x = []
        split = False
        for i in lines:
            if i.count(" ") > 100:
                split_text = i.split(asdf)
                if len(split_text) == 1:
                    if i.count(" ") > 100:
                        prob = True
                    x.append(i)
                else:
                    index = 0
                    running_text = split_text[0]
                    while running_text.count(" ") < 30 and index < len(split_text) - 1:
                        index += 1
                        running_text += asdf+split_text[index]
                    new_i = i.replace(running_text, "", 1)
                    if asdf[0] == ".":
                        new_i = new_i[2:]
                        running_text += "."
                    elif asdf == "</i>":
                        running_text += "</i>"
                        new_i = new_i[4:]
                    if running_text.count(" ") < 30 or new_i.count(" ") < 30:
                        if i.count(" ") > 100:
                            prob = True
                        x.append(i)
                    else:
                        x.append(running_text)
                        x.append(new_i)
                        split = True
            else:
                x.append(i)
        lines = x
        if not split:
            break

    if "</i>" in line and asdf != "</i>":
        actual_lines = []
        for l in lines:
            actual_lines += cut_line(l, 0, asdf="</i>")
        return actual_lines
    else:
        for l in lines:
            if l.count(" ") > 100:
                probs.append(l.count(" "))
        return lines



def segment(file, new_name):
    how_many = 0
    r = list(csv.reader(file))
    header = r[:5]
    r = r[5:]
    all_rows = []
    new_rows_dict = defaultdict(list)
    for row in r:
        ref, text = row
        orig = text
        if ":" in ref:
            sec_ref = ref.split(":")[0]
        else:
            sec_ref = " ".join(ref.split()[:-1])
        henay = ". והנה"
        temp = text.split(". והנה")

        running_text = temp[0]
        index = 0
        while running_text.count(" ") < 30 and index < len(temp) - 1:
            index += 1
            running_text += henay + temp[index]
        # first will be running_text
        split_text = text.split(running_text)



        new_rows = new_rows_dict[sec_ref]
        temp[0] = temp[0] if len(temp) == 1 else temp[0] + "."
        if temp[0].count(" ") > 30 or len(temp) == 1:
            text = temp
        else:
            text = [text]
        new_rows_to_add = []
        new_rows_to_add += cut_line(text[0], 150)
        check(new_rows_to_add, ". והנה")
        others = []
        for line in text[1:]:
            if line != text[-1]:
                line += "."
            line = " והנה" + line
            others += cut_line(line, 150)
        check(others, ". והנה")
        new_rows += new_rows_to_add + others
    with open(new_name, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(header)
        for sec_ref in new_rows_dict:
            #new_rows_dict[sec_ref] = [x.replace("..", ".").replace(":.", ":") for x in new_rows_dict[sec_ref]]
            for x in new_rows_dict[sec_ref]:
                # if x.count(" ") < 30:
                #     how_many += 1
                if x.count(" ") > 175 and ". והנה" in x:
                    how_many += 1
            writer.writerows(new_rows_dict[sec_ref])
    for sec_ref in new_rows_dict:
        send_text = {"text": new_rows_dict[sec_ref], "language": "he", "versionTitle": "segmented", "versionSource": "https://www.sefaria.org"}
        for l, line in enumerate(new_rows_dict[sec_ref]):
            if line.count(" ") < 30:
                print(line)
            if line.count(" ") > 250:
                print(f"{sec_ref}:{l+1} has {line.count(' ')} words.")
        #post_text(sec_ref, send_text, server="http://localhost:8000")

if __name__ == "__main__":
    with open("Likkutei Torah - he - Kehot Publication Society.csv", 'r') as lt:
        segment(lt, "Likkutei Torah (segmented) - he - Kehot Publication Society.csv")
    with open("Torah Ohr - he - Kehot Publication Society.csv", 'r') as to:
        segment(to, "Torah Ohr (segmented) - he - Kehot Publication Society.csv")

    print(sum(probs)/len(probs))
    print(len(probs))
    print(total)