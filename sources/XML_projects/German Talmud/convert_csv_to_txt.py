from sources.functions import *
from sefaria.export import text_is_copyright, make_json, make_text, prepare_merged_text_for_export, \
    prepare_text_for_export, export_merged_csv, export_version_csv, import_versions_from_stream
import os
from sefaria.views import _get_text_version_file
masechtot = [f for f in os.listdir("CSVs/") if ".csv" in f]
mishnayot = [f for f in os.listdir("mishnah/") if "structured" in f]
for arr, dir in [(masechtot, "CSVs/"), (mishnayot, "mishnah/")]:
    for title in arr:
        if "Chullin" not in title:
            continue
        with open(dir+title, 'r') as f:
            reader = csv.reader(f)
            reader = list(reader)
            vtitle = reader[1][1]
            if "ftnote_markers_only" in title:
                vtitle = vtitle.replace("footnotes", "no footnotes")
            lang = 'en'
            vsource = reader[3][1]
            for row in reader[5:]:
                ref, comm = row
                if dir == "mishnah/":
                    ref = "Mishnah "+ref
                    ref = ref.replace("Orla ", "Orlah ")
                tc = TextChunk(Ref(ref), lang=lang, vtitle=vtitle)
                tc.text = comm
                tc.save(force_save=True)
                index = Ref(ref).index.title
        results = _get_text_version_file("txt", index, lang, vtitle)
        if "mishnah" in dir:
            with open("{}.txt".format(index), 'w') as new_f:
                new_f.write(results)
        else:
            with open("{}.txt".format(title.replace(".csv", "")), 'w') as new_f:
                new_f.write(results)
