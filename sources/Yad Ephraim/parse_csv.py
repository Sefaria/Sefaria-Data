#encoding=utf-8
import django
django.setup()
from sources.functions import *
from sefaria.model import *
import csv
if __name__ == "__main__":


    books = {u"עטרת זקנים": "Ateret Zekenim on Shulchan Arukh, Orach Chayim:", u"""או"ח""": "Shulchan Arukh, Orach Chayim:",
             u"""ט"ז""": "Turei Zahav on Shulchan Arukh, Orach Chayim:", u"""מג"א""": "Magen Avraham:"}
    actual_ref_data = {}
    linker = lambda x, y: {"refs": [x, y], "generated_by": "yad_ephraim", "auto": True, "type": "Commentary"}
    links = []
    count_siman_only = 0
    with open("Yad Ephraim on OC - newyad2.csv") as f:
        reader = csv.reader(f)
        reader.next()
        lines = list(enumerate(reader))
        for n, row in lines:
            ref, data = row
            data = data.replace("@11", "<b>").replace("@33", "</b>")
            ref = ref.decode('utf-8')
            for k, v in books.items():
                ref = ref.replace(k, v)
            if not ref:
                ref = prev
            prev = ref
            book, segments = ref.split(":")
            segments = segments.strip()
            if len(segments.split()) == 1:
                count_siman_only += 1
                siman = segments
                siman = getGematria(siman)
                if siman not in actual_ref_data.keys():
                    actual_ref_data[siman] = []
                new_ref = "{} {}".format(book, siman)
                print "Only siman no seif for {}".format(row[0])
            elif len(segments.split()) == 2:
                siman, seif = segments.split()
                siman = getGematria(siman)
                seif = getGematria(seif)
                if siman not in actual_ref_data.keys():
                    actual_ref_data[siman] = []
                new_ref = "{} {}:{}".format(book, siman, seif)
            elif len(segments.split()) == 3:
                raise Exception

            if not Ref(new_ref).text('he').text:
                print "Didn't find any text for {}".format(row[0])
            else:
                yad_ephraim_seif = len(actual_ref_data[siman]) + 1
                yad_ephraim_ref = "Yad Ephraim on Shulchan Arukh, Orach Chayim {}:{}".format(siman, yad_ephraim_seif)
                links.append(linker(yad_ephraim_ref, new_ref))
                actual_ref_data[siman].append(data)
                found = True
                if not new_ref.startswith("Shulchan Arukh"):
                    found = False
                    ls = LinkSet(Ref(new_ref))
                    for l in ls:
                        other_ref = l.refs[1] if l.refs[1] != new_ref else l.refs[0]
                        if other_ref.startswith("Shulchan Arukh"):
                            found = True
                            links.append(linker(yad_ephraim_ref, other_ref))
                # if not found:
                #     print "Didn't find any links for {}".format(new_ref)

    actual_ref_data = convertDictToArray(actual_ref_data)
    text = {
        "text": actual_ref_data,
        "language": "he",
        "versionTitle": "Maginei Eretz: Shulchan Aruch Orach Chaim, Lemberg, 1893",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080"
    }
    root = JaggedArrayNode()
    root.add_primary_titles("Yad Ephraim on Shulchan Arukh, Orach Chayim", u"יד אפרים על שלחן ערוך אורח חיים")
    root.key = "Yad Ephraim on Shulchan Arukh, Orach Chayim"
    root.add_structure(["Siman", "Seif"])
    index = {
        "schema": root.serialize(),
        "title": root.key,
        "dependence": "Commentary",
        "categories": ["Halakhah", "Shulchan Arukh", "Commentary"],
        "collective_title": "Yad Ephraim"
    }
    post_index(index)


    post_text("Yad Ephraim on Shulchan Arukh, Orach Chayim", text, server="http://shmuel.sandbox.sefaria.org")
    post_link(links)