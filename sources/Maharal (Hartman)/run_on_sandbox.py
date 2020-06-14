from bs4 import BeautifulSoup
from sefaria.model import *
import re
generated_by = "maharal_i_tags_"
LinkSet({"generated_by": generated_by}).delete()

titles = ["Derech Chaim", "Be'er HaGolah"]
for title in titles:
    ftnote_count = 0
    for ref in library.get_index(title).all_segment_refs():
        try:
            if ref.sections[-1] == 1:
                ftnote_count = 0
            for i_tag in re.findall("<i .*?></i>", ref.text('he').text):
                ftnote_count += 1
                data = BeautifulSoup(i_tag).find("i")
                data = data.attrs
                comm = data["data-commentator"].replace("Index: ", "")
                order = data["data-label"]
                ftnote_title_ref = Ref(ref.normal().replace(title, "{} on {}".format(comm, title)))
                ftnote_section_ref = ftnote_title_ref.section_ref().normal()
                ftnote_ref = "{} {}".format(ftnote_section_ref, ftnote_count)
                link = Link({"refs": [ref.normal(), ftnote_ref], "type": "Commentary",
                             "auto": True, "generated_by": generated_by,
                             "inline_reference": {"data-commentator": comm}})
                print(link.contents())
                link.save()
        except Exception as e:
            print(e)