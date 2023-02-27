from sources.functions import *
from sefaria.system.database import db
from linking_utilities.dibur_hamatchil_matcher import *
i = library.get_index("Tzafnat Pa'neach on Torah")
links = []

def dher(str):
    return str.split(".")[0].replace("<b>", "").replace("</b>", "").replace("וגו׳", "").strip()

#base_ref, comm_ref, comments, base_tokenizer, dh_extract_method, vtitle=""
links = []
for ref in i.all_section_refs():
      if "Haftarot" in ref.normal():
          parasha = ref.normal().split(",")[-1].strip()
          haftarah = list(db.parshiot.find({"parasha": parasha}))
          if haftarah:
              haftarah = Ref(haftarah[0]["haftara"]["ashkenazi"][0])
              haftarah_index = haftarah.index.title
              haftarah_base = haftarah.text('he')
              comments = ref.text('he').text
              #links += match_ref_interface(haftarah_index, ref.normal(), comments, lambda x: x.split(), dher)
          else:
              print("***")
              print(parasha)
              print("haftarah {}".format(haftarah))
      else:
          for sub in ref.all_segment_refs():
              base = sub.normal().replace("Tzafnat Pa'neach on Torah, ", "").rsplit(":", 1)[0]
              links.append({"refs": [sub.normal(), base], "generated_by": "tzafnat_to_torah", "auto": True,
                            "type": "Commentary"})



post_link(links)
     # else:
     #    Link({"refs": [ref.normal(), ref.normal().rsplit(":")[0].replace("Tzafnat Pa'neach on Torah, ", "")],
     #               "generated_by": "tzafnat_to_torah", "auto": "True", "type": "Commentary"}).save()
