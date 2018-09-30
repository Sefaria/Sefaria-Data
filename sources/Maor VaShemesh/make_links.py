#encoding=utf-8
import django
django.setup()
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.system.database import db
from sources.functions import post_link
if __name__ == "__main__":
    def get_dh(x):
        x = x[x.find("<b>")+3:x.find("</b>")].replace(u"אלקים", u"אלהים")
        x = x.split(u"וכו'", 1)[0]
        return x
    base_tokenizer = lambda x: [x for x in x.split()]
    index = library.get_index("Maor VaShemesh")
    section_refs = index.all_section_refs()
    current_book = "Genesis"
    ls = []
    for section in section_refs:
        print section
        section_text = section.text('he').text
        # section_dh_text = [get_dh(line) if "<b>" in line and "</b>" in line for text in section_text for line in text]
        ja = section.index_node
        ja_title = ja.get_primary_title()
        parasha = db.parshiot.find({"parasha": ja_title})
        if list(parasha) != []:
            parasha = list(db.parshiot.find({"parasha": ja_title}))[0]
            current_book = parasha["ref"].split()[0]
            tc_current_book = Ref(current_book).text('he')
            matches = match_ref(tc_current_book, section_text, base_tokenizer, dh_extract_method=get_dh)["matches"]
            for i, match in enumerate(matches):
                if match:
                    link = {"refs": [match.normal(), "{} {}".format(section.normal(), i+1)], "auto": True, "type": "Commentary", "generated_by": "maor_vashemesh"}
                    ls.append(link)
    post_link(ls, server="http://proto.sefaria.org")