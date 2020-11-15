from bs4 import BeautifulSoup
from sefaria.model import *
import re
generated_by = "maharal_i_tags_"
LinkSet({"generated_by": generated_by}).delete()
titles = ["Netivot Olam"]#, "Netivot Olam"] #["Gevurot Hashem", "Ner Mitzvah"]
for title in titles:
    ftnote_count = 0
    i = library.get_index(title)
    vs = [v for v in i.versionSet() if "with footnotes and annotations by Rabbi Yehoshua" in v.versionTitle]
    assert len(vs) in [1, 0]
    vtitle = vs[0].versionTitle
    for ref in i.all_segment_refs():
        print(ref)

        try:
            if ref.sections[-1] == 1:
                ftnote_count = 0
            tc = TextChunk(ref, lang='he', vtitle=vtitle)
            i_tags = re.findall("<i .*?></i>", tc.text)
            for i_tag in i_tags:
                ftnote_count += 1
                print(i_tag)
                print(ftnote_count)
                print("****")
                data = BeautifulSoup(i_tag).find("i")
                data = data.attrs
                comm = data["data-commentator"].replace("Index: ", "")
                order = data["data-label"]
                ftnote_title_ref = Ref(ref.normal().replace(title, "{} on {}".format(comm, title), 1))
                ftnote_section_ref = ftnote_title_ref.section_ref().normal()
                ftnote_ref = "{} {}".format(ftnote_section_ref, ftnote_count)
                link = Link({"refs": [ref.normal(), ftnote_ref], "type": "Commentary",
                             "auto": True, "generated_by": generated_by,
                             "inline_reference": {"data-commentator": comm}})
                print(link.contents())
                link.save()
        except Exception as e:
            print(e)

library.rebuild(include_toc=True)