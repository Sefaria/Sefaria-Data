import re
from sefaria.model import *


def get_ftnotes(sec_ref, title):
    # get footnotes on text found in sec_ref
    node_name = sec_ref.index_node.get_titles("en")[0]
    relevant_footnote_ref = "{}, Footnotes, {}".format(title, node_name)
    ftnotes = Ref(relevant_footnote_ref).text('en').text
    assert type(ftnotes[0]) is unicode
    ftnotes = dict(enumerate(ftnotes))
    return ftnotes

if __name__ == "__main__":
    title = "Or Neerav"
    index = library.get_index(title)
    sec_refs_in_main_text = index.all_section_refs()
    for sec_ref in sec_refs_in_main_text:
        if "Subject" in sec_ref.normal():
            continue
        ftnotes = get_ftnotes(sec_ref, title)
        text = sec_ref.text('en').text
        assert 0 < len(ftnotes) - len(text) < 10, "ftnotes {} vs text {}".format(len(ftnotes), len(text))
        for comment in text:
            matches = re.findall("<sup>(\d+)</sup>", comment)
            assert len(set(matches)) == len(matches)  # assert no duplicates
            for match in matches:
                old_ftnote = "<sup>{}</sup>".format(match)
                ftnote_num = int(match)
                ftnote_text = ftnotes[ftnote_num - 1]
                new_ftnote = u"{}<i class='footnote'>{}</i>".format(old_ftnote, ftnote_text)
                comment = comment.replace(old_ftnote, new_ftnote)
        pass







