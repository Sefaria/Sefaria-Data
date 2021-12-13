from sources.functions import *
mishnayot = library.get_indices_by_collective_title("English Explanation of Mishnah")
for mishnah in mishnayot:
    index = library.get_index(mishnah)
    for sec_ref in index.all_section_refs():
        questions_start = -1
        new_sec_ref_text = []
        for seg_ref in sec_ref.all_segment_refs():
            if "Questions for Further Thought" in seg_ref.text('en').text:
                questions_start += 1
                new_sec_ref_text.append(seg_ref.text('en').text+"<br/>")
            elif questions_start > -1:
                if new_sec_ref_text[-1]+seg_ref.text('en').text != new_sec_ref_text[-2]:
                    passage = seg_ref.text('en').text.replace("", "•")
                    new_sec_ref_text[-1] += passage
                else:
                    new_sec_ref_text.pop(-1)
            else:
                new_sec_ref_text.append(seg_ref.text('en').text)
        for i, passage in enumerate(new_sec_ref_text):
            if i > 0 and passage == new_sec_ref_text[i-1]:
                new_sec_ref_text.pop(i)
        for i, passage in enumerate(new_sec_ref_text):
            if "•" in passage:
                passages = passage.split("•")
                if len(passages[0]) == 0:
                    passages = passages[1:]
                new_sec_ref_text[i] = ""
                for j, p in enumerate(passages):
                    if "Questions for Further Thought" in p:
                        new_sec_ref_text[i] += p.replace("\n", "").replace("<br/>", "") + "<br/>"
                    elif j == len(passages)-1:
                        new_sec_ref_text[i] += "•"+p
                    else:
                        new_sec_ref_text[i] += "•"+p+"<br/>"

        tc = TextChunk(sec_ref, vtitle='Mishnah Yomit by Dr. Joshua Kulp', lang='en')
        if new_sec_ref_text != tc.text:
            print(tc)
            tc.text = new_sec_ref_text
            tc.save(force_save=True)
# start = "Bava Metzia"
# starting = False
# with open("report_of_corrected_phrases.csv", 'w') as f:
#     writer = csv.writer(f)
#     for i in library.get_indexes_in_category("Mishnah"):
#         tc = TextChunk(Ref(i), lang='en', vtitle=vtitle)
#         if tc.text:
#             for a, sec in enumerate(tc.text):
#                 for b, seg in enumerate(sec):
#                     #tc[a][b][c]
#                     find = re.search("([:?.]{1})([a-zA-Z]{2,})", seg)
#                     if find:
#                         words = seg.split()
#                         pos = -1
#                         for j, w in enumerate(words):
#                             if find.group(0) in w:
#                                 pos = j
#                                 break
#                         assert pos != -1
#                         words = " ".join(words[pos-2:pos+2]) if pos >= 2 else " ".join(words[0:pos+2])
#                         assert len(words) > 0
#                         writer.writerow([words, "{} {}:{}".format(i, a+1, b+1)])
#                         tc.text[a][b] = seg.replace(find.group(0), find.group(1)+" "+find.group(2))
#                         send_text = {
#                             "text": tc.text[a][b],
#                             "versionTitle": "Mishnah Yomit by Dr. Joshua Kulp",
#                             "versionSource": "http://learn.conservativeyeshiva.org/mishnah/",
#                             "language": "en"
#                         }
                        #post_text("{} {}:{}".format(i, a+1, b+1), send_text)

#
# from sefaria.helper.schema import *
# indices = """Shevuot
# Sanhedrin
# Eduyot
# Makkot
# Sheviit
# Kilayim
# Makhshirin
# Avodah Zarah""".splitlines()
# for l in indices:
#     l = library.get_index("English Explanation of Mishnah {}".format(l))
#     print(l)
#     intro = JaggedArrayNode()
#     intro.add_structure(["Paragraph"])
#     intro.add_shared_term("Introduction")
#     intro.key = "Introduction"
#     insert_first_child(intro, l.nodes)
#     refresh_version_state(l.title)
# library.rebuild(include_toc=True)