#encoding=utf-8
import django
django.setup()
from linking_utilities.dibur_hamatchil_matcher import *
from sefaria.system.database import db
from sources.functions import post_link
if __name__ == "__main__":
    def get_dh(x):
        first_2_words = " ".join(x.split()[0:2])
        if u"</b>" in first_2_words:
            return u" ".join(x.split(u" ")[0:10]).strip()
        elif u"</b>" in x:
            first_b = x.find("<b>")
            second_b = x.find("</b>")
            x = x[first_b+3:second_b]
        x = x.replace(u"<b>", u"").replace(u"</b>", u"").replace(u"אלקים", u"אלהים").replace(u" כו", u"")
        if u"וכו'" in x:
            x = x.split(u"וכו'", 1)[0]
        return u" ".join(x.split(u" ")[0:10]).strip()
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
            current_parasha = parasha["ref"].split()[0]
            tc_current_book = Ref(current_parasha).text('he')
            matches = match_ref(tc_current_book, section_text, base_tokenizer, dh_extract_method=get_dh,
                                word_threshold=0.35, char_threshold=0.26)["matches"]
            for i, match in enumerate(matches):
                if match:
                    link = {"refs": [match.normal(), "{} {}".format(section.normal(), i+1)], "auto": True, "type": "Commentary", "generated_by": "maor_vashemesh"}
                    ls.append(link)
    post_link(ls, server="http://proto.sefaria.org")