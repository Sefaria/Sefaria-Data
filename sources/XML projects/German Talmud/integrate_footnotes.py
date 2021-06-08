from sources.functions import *
import os
import copy
html_tags = ['</small <small>', '<img/>', '</i <i>', '<n den\xa0Frieden\xa0in\xa0der\xa0Welt,\xa0denn\xa0es\xa0heißt\xa0:<sup>']



indxs = library.get_indexes_in_category("Bavli")
for i in indxs:
    i = library.get_index(i)
    for v in i.versionSet():
        if v.language == "en" and v.versionTitle == 'Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]':
            print(i)
            v.versionTitle = 'Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]'
            v.save()
    print("***")
ftnotes = {}
found_ftnotes = {}
version = """Index Title,{}
Version Title,Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]
Language,en
Version Source,https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI
Version Notes,"""
if __name__ == "__main__":
    probs = []
    german_blank = []
    fn_probs = []
    transitions = {}
    for f in os.listdir("./just ftnotes"):
        if f.endswith("txt"):
            title = f.replace(" just ftnotes.txt", "")
            transitions[title] = {}
            prev_ftnote_num = 0
            prob = False
            perek = 1
            reader = csv.reader(open("just ftnotes/"+f, 'r'))
            found_skip = -1
            for row in reader:
                seg_ref, ftnote_num, ftnote_comment = row
                ftnote_num = ftnote_num.replace("<sup>", "").replace("</sup>", "")
                ftnote_comment = re.sub("fn\d+\,", "", ftnote_comment)
                ftnote_num = int(ftnote_num)
                sec_ref = Ref(seg_ref).index.title
                if sec_ref not in ftnotes:
                    ftnotes[sec_ref] = {}
                    found_ftnotes[sec_ref] = {}
                    ftnotes[sec_ref][perek] = []
                    found_ftnotes[sec_ref][perek] = []
                if ftnote_num - prev_ftnote_num < -50 and 2 <= ftnote_num < 4:
                    found_skip = prev_ftnote_num
                elif found_skip >= 0:
                    if ftnote_num - found_skip == 1:
                        put_in_next_perek = int(found_ftnotes[sec_ref][perek][0].split(",")[0])
                        if found_skip not in transitions[title]:
                            transitions[title][found_skip] = []
                        transitions[title][found_skip] += [put_in_next_perek]
                        found_ftnotes[sec_ref][perek-1].append(found_ftnotes[sec_ref][perek][0])
                        found_ftnotes[sec_ref][perek] = []
                        perek -= 1
                    found_skip = -1
                else:
                    found_skip = -1
                if (ftnote_num - prev_ftnote_num < -50 and 0 < ftnote_num < 4):
                    perek += 1
                    found_ftnotes[sec_ref][perek] = []
                found_ftnotes[sec_ref][perek].append("{},{}".format(ftnote_num, ftnote_comment))
                prev_ftnote_num = ftnote_num

    new_found_ftnotes = {}
    for sec_ref in found_ftnotes:
        new_found_ftnotes[sec_ref] = {}
        for perek in found_ftnotes[sec_ref]:
            new_found_ftnotes[sec_ref][perek] = []
            for ftnote in found_ftnotes[sec_ref][perek]:
                if re.search("<br>\d+\.", ftnote):
                    for i, x in enumerate(ftnote.split("<br>")):
                        if re.search("(\d+)\. (.*?)", x):
                            m = re.search("(\d+)\. (.*)", x)
                            x = "{},{}".format(m.group(1), m.group(2))
                        if i == 0:
                            new_found_ftnotes[sec_ref][perek].append(x)
                        else:
                            new_found_ftnotes[sec_ref][perek].append(x)
                else:
                    new_found_ftnotes[sec_ref][perek].append(ftnote)


    ftnotes = copy.deepcopy(new_found_ftnotes)
    for f in os.listdir("3 - aligned txt files 3"):
        if f.endswith("txt"):
            title = f.split("_")[1]
            print(title)
            text = {}
            perek = 1
            curr_segment = 0
            prev_ftnote_num = 0
            with open("{}_aligned_with_ftnotes.csv".format(title), 'w') as new_f:
                writer = csv.writer(new_f)
                version_list = version.format(title).splitlines()
                for row in version_list:
                    writer.writerow(row.split(",", 1))
                rows = []
                for line in open("3 - aligned txt files 3/"+f, 'r'):
                    ref, comm = line.split("\t", 1)
                    ref = ref.replace(chr(65279), "")
                    if ref.endswith(","):
                        ref = ref[:-1]
                    no_hadran = ("הַדְרָן" not in Ref(ref).text('he').text and "הָדְרָן" not in Ref(ref).text('he').text and "הדרן" not in Ref(ref).text('he').text and "הֲדַרַן" not in Ref(ref).text('he').text)
                    if comm.strip() == "" and no_hadran:
                        german_blank.append("Blank German Segment Ref {}\n{}".format(ref, Ref(ref).text('he').text))
                    if Ref(ref).section_ref().normal() not in text:
                        text[Ref(ref).section_ref().normal()] = []
                    sec_ref = Ref(ref).index.title
                    fns = re.findall("\$fn\d+", comm)
                    rows.append([ref, comm])

                found_skip = 0
                for i, row in enumerate(rows):
                    ref, comm = row
                    if comm.strip() == "":
                        next_ref = Ref(ref).next_segment_ref()
                        if next_ref is None or next_ref.section_ref() != Ref(ref).section_ref():
                            continue
                    fns = re.findall("\$fn\d+", comm)
                    for fn in fns:
                        num = int(fn.replace("$fn", ""))
                        if (num - prev_ftnote_num < -50 and 0 < num < 4):
                            if (prev_ftnote_num not in transitions[title] or num not in transitions[title][prev_ftnote_num]):
                                perek += 1
                                curr_segment = 0

                        before_loop = curr_segment
                        while curr_segment < len(ftnotes[sec_ref][perek]) and not ftnotes[sec_ref][perek][curr_segment].startswith("{},".format(num)):
                            curr_segment += 1
                        if curr_segment >= len(ftnotes[sec_ref][perek]):
                            curr_segment = before_loop
                        else:
                            ftnotes[sec_ref][perek][curr_segment] = ftnotes[sec_ref][perek][curr_segment].replace("{},".format(num), "")
                            italics_open = len([x for x in ftnotes[sec_ref][perek][curr_segment].split("<i>") if len(x) > 0])
                            italics_close = len([x for x in ftnotes[sec_ref][perek][curr_segment].split("</i>") if len(x) > 0])
                            if italics_open == italics_close + 1:
                                ftnotes[sec_ref][perek][curr_segment] += "</i>"
                                italics_close += 1
                            if italics_open != italics_close:
                                print("{} vs {}".format(italics_open, italics_close))
                            comm = comm.replace(fn, "<sup>{}</sup>{}".format(num, ftnotes[sec_ref][perek][curr_segment]))
                            ftnotes[sec_ref][perek][curr_segment] = ""
                            prev_ftnote_num = num
                        #curr_segment += 1
                    text[Ref(ref).section_ref().normal()].append(comm)
                    if "$fn" in comm:
                        fn_probs.append("$fn in {}".format(ref))
                    for tag in re.findall("<.*?>", comm):
                        if tag in html_tags:
                            print("tags")
                            print(ref)
                            print(tag)
                            print()
                    writer.writerow([ref, comm])

            if len(text) != len(library.get_index(title).all_section_refs()):
                probs.append("Incorrect # of dappim in {}.  Should be {} but is {}".format(title, len(library.get_index(title).all_section_refs()),
                                                                                      len(text)))
            for sec in text:
                if len(Ref(sec).text('en').text) != len(text[sec]):
                    probs.append("Incorrect # of refs in {}.  Should be {} but is {}".format(sec, len(Ref(sec).text('en').text),
                                                                                          len(text[sec])))

    #
    # for p in probs:
    #     print(p)
    #
    # for p in fn_probs:
    #     print(p)
    #
    # for p in german_blank:
    #     print(p)

