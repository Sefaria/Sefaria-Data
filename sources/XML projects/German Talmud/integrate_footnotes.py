from sources.functions import *
import os
import copy
ftnotes = {}
found_ftnotes = {}
version = """Index Title,{}
    Version Title,"Talmud Bavli. German. Lazarus Goldschmidt. 1929 -- footnotes"
    Language,en
    Version Source,https://www.sefaria.org
    Version Notes,"""
if __name__ == "__main__":
    for f in os.listdir("./just ftnotes"):
        if f.endswith("txt"):
            title = f.replace(" just ftnotes.txt", "")
            prev_ftnote_num = 0
            prob = False
            if title in ["Beitzah", "Taanit", "Sukkah", "Yoma"]:
                perek = 1
                reader = csv.reader(open("just ftnotes/"+f, 'r'))
                for row in reader:
                    seg_ref, ftnote_num, ftnote_comment = row
                    ftnote_num = int(ftnote_num)
                    sec_ref = Ref(seg_ref).index.title
                    if sec_ref not in ftnotes:
                        ftnotes[sec_ref] = {}
                        found_ftnotes[sec_ref] = {}
                        ftnotes[sec_ref][perek] = {}
                        found_ftnotes[sec_ref][perek] = {}
                    if ftnote_num - prev_ftnote_num < -50 and 2 < ftnote_num < 10:
                        print(seg_ref)
                        print("SKIP BACK")
                    if (ftnote_num - prev_ftnote_num < -50 and 0 < ftnote_num < 10):
                        perek += 1
                        ftnotes[sec_ref][perek] = {}
                        found_ftnotes[sec_ref][perek] = {}
                    if ftnote_num in ftnotes[sec_ref][perek]:
                        if ftnotes[sec_ref][perek][ftnote_num] != ftnote_comment:
                            if prob == False:
                                prob = True
                                print("{} {} {} -> {} vs {}".format(sec_ref, perek, ftnote_num, ftnotes[sec_ref][perek][ftnote_num], ftnote_comment))
                        else:
                            prob = False
                    else:
                        ftnotes[sec_ref][perek][ftnote_num] = ftnote_comment
                        found_ftnotes[sec_ref][perek][ftnote_num] = ftnote_comment
                        prob = False
                    prev_ftnote_num = ftnote_num

    new_found_ftnotes = {}
    for sec_ref in found_ftnotes:
        new_found_ftnotes[sec_ref] = {}
        for perek in found_ftnotes[sec_ref]:
            new_found_ftnotes[sec_ref][perek] = {}
            for num in found_ftnotes[sec_ref][perek]:
                if re.search("<br>\d+\.", found_ftnotes[sec_ref][perek][num]):
                    for i, x in enumerate(found_ftnotes[sec_ref][perek][num].split("<br>")):
                        if i == 0:
                            new_found_ftnotes[sec_ref][perek][num] = x
                        else:
                            after = re.search("^(\d+)\. (.+)", x)
                            after_num = int(after.group(1))
                            after_comm = after.group(2)
                            new_found_ftnotes[sec_ref][perek][after_num] = after_comm
                else:
                    new_found_ftnotes[sec_ref][perek][num] = found_ftnotes[sec_ref][perek][num]


    found_ftnotes = copy.deepcopy(new_found_ftnotes)
    ftnotes = copy.deepcopy(new_found_ftnotes)
    for f in os.listdir("3 - aligned txt files"):
        title = f.split("_")[0]
        if title in ["Beitzah", "Taanit", "Sukkah", "Yoma"]:
            perek = 1
            prev_ftnote_num = 0
            with open("{}_aligned_with_ftnotes.csv".format(title), 'w') as new_f:
                writer = csv.writer(new_f)
                version_list = version.format(title).splitlines()
                for row in version_list:
                    writer.writerow(row.split(",", 1))
                for line in open("3 - aligned txt files/"+f, 'r'):
                    ref, comm = line.split("\t", 1)
                    ref = ref.replace(chr(65279), "")
                    sec_ref = Ref(ref).index.title
                    fns = re.findall("\$fn\d+", comm)
                    for fn in fns:
                        num = int(fn.replace("$fn", ""))
                        if (num - prev_ftnote_num < -50 and 0 < num < 10):
                            perek += 1
                        if num in ftnotes[sec_ref][perek]:
                            ftnotes[sec_ref][perek].pop(num)
                        assert fn in comm
                        try:
                            comm = comm.replace(fn, found_ftnotes[sec_ref][perek][num], 1)
                        except KeyError as e:
                            print("{} doesnt exist in {} {}".format(num, sec_ref, perek))
                        prev_ftnote_num = num
                    writer.writerow([ref, comm])
