from sources.functions import *
import os
from data_utilities.dibur_hamatchil_matcher import match_ref
def dher(str):
    dh = re.search("<b>(.*?)</b>", str)
    return dh.group(1) if dh else ""

if __name__ == "__main__":
    links = []
    for ritva_section in library.get_index("Ritva on Pesachim").all_section_refs():
        comments = ritva_section.text('he').text
        ritva_section = ritva_section.normal()
        pesachim_section = ritva_section.replace("Ritva on ", "")
        links += match_ref_interface(pesachim_section, ritva_section, comments, lambda x: x.split(), dher)
    results = post_link(links, VERBOSE=True, server="https://www.sefaria.org")
    print(results)






    # ritva = "Ritva on Pesachim - he - Chiddushei haRitva, Warsaw 1864.csv"
    # pesachim = "Pesachim - he - William Davidson Edition - Aramaic.csv"
    # files = [pesachim, ritva]
    # text_dict = {"Pesachim": [], "Ritva on Pesachim": []}
    # for i, file_name in enumerate(files):
    #     with open(file_name) as f:
    #         file_name = file_name.replace(".csv", "")
    #         title = file_name.split(" - ")[0]
    #         lang = file_name.split(" - ")[1]
    #         vtitle = file_name.split(" - ", 2)[2]
    #         for row in csv.reader(f):
    #             if row[0].startswith(title):
    #                 TextChunk(Ref(row[0]), lang=lang, vtitle=vtitle).save()
    #
    #
