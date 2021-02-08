from sources.functions import *
arr = ['Footnotes and Annotations on Ohr Chadash 10:2',
'Footnotes and Annotations on Ohr Chadash 2:17',
'Footnotes and Annotations on Ohr Chadash 2:22',
'Footnotes and Annotations on Ohr Chadash 3:10',
'Footnotes and Annotations on Ohr Chadash 3:2',
'Footnotes and Annotations on Ohr Chadash 3:4',
'Footnotes and Annotations on Ohr Chadash 3:6',
'Footnotes and Annotations on Ohr Chadash 3:7',
'Footnotes and Annotations on Ohr Chadash 3:8',
'Footnotes and Annotations on Ohr Chadash 4:14',
'Footnotes and Annotations on Ohr Chadash 4:7',
'Footnotes and Annotations on Ohr Chadash 5:11',
'Footnotes and Annotations on Ohr Chadash 5:12',
'Footnotes and Annotations on Ohr Chadash 5:13',
'Footnotes and Annotations on Ohr Chadash 5:14',
'Footnotes and Annotations on Ohr Chadash 5:5',
'Footnotes and Annotations on Ohr Chadash 5:6',
'Footnotes and Annotations on Ohr Chadash 5:9',
'Footnotes and Annotations on Ohr Chadash 6:10',
'Footnotes and Annotations on Ohr Chadash 6:11',
'Footnotes and Annotations on Ohr Chadash 6:12',
'Footnotes and Annotations on Ohr Chadash 6:13',
'Footnotes and Annotations on Ohr Chadash 6:2',
'Footnotes and Annotations on Ohr Chadash 6:8',
'Footnotes and Annotations on Ohr Chadash 7:3',
'Footnotes and Annotations on Ohr Chadash 7:4',
'Footnotes and Annotations on Ohr Chadash 7:5',
'Footnotes and Annotations on Ohr Chadash 7:7',
'Footnotes and Annotations on Ohr Chadash 7:9',
'Footnotes and Annotations on Ohr Chadash 8:10',
'Footnotes and Annotations on Ohr Chadash 8:12',
'Footnotes and Annotations on Ohr Chadash 8:13',
'Footnotes and Annotations on Ohr Chadash 8:14',
'Footnotes and Annotations on Ohr Chadash 8:17',
'Footnotes and Annotations on Ohr Chadash 8:2',
'Footnotes and Annotations on Ohr Chadash 8:5',
'Footnotes and Annotations on Ohr Chadash 9:12',
'Footnotes and Annotations on Ohr Chadash 9:22',
'Footnotes and Annotations on Ohr Chadash 9:26',
'Footnotes and Annotations on Ohr Chadash 9:27',
'Footnotes and Annotations on Ohr Chadash 9:28',
'Footnotes and Annotations on Ohr Chadash 9:31']
new_text = {}
for ref in arr:
    base_ref = ref.replace("Footnotes and Annotations on ", "")
    base_ref = Ref(base_ref)
    ftnotes_ref = Ref(ref).prev_section_ref()
    new_text[ref] = []
    new_text[ftnotes_ref.normal()] = []
    for segment in base_ref.text('he').text:
        i_tags = re.findall('<i data-commentator=\"Footnotes and Annotations\" data-label=\"(\d+)\"></i>', segment)
        i_tags = ["("+x+")" for x in i_tags]
        for ftnotes_segment in ftnotes_ref.text('he').text:
            ftnotes_i_tag = ftnotes_segment.split()[0]
            if ftnotes_i_tag not in i_tags and ftnotes_segment not in new_text[ftnotes_ref.normal()]:
                new_text[ftnotes_ref.normal()].append(ftnotes_segment)
            elif ftnotes_segment not in new_text[ref]:
                new_text[ref].append(ftnotes_segment)
#7000 in 3:1
for ref in new_text:
    send_text = {
        "language": "he",
        "versionTitle": "Ohr Chadash, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2014",
        "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH004713598/NLI",
        "text": new_text[ref]
    }
    post_text(ref, send_text)