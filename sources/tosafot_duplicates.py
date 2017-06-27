__author__ = 'stevenkaplan'
from sefaria.model import *

def print_out_refs(daf, line, segment, prev_daf, prev_line, prev_segment):
    first = "{} {}:{}:{}".format(title, AddressTalmud.toStr("en", daf+1), line+1, segment+1)
    second = "{} {}:{}:{}".format(title, AddressTalmud.toStr("en", prev_daf+1), prev_line+1, prev_segment+1)
    print "First: {}".format(first)
    print "Second: {}\n".format(second)

def delete_same_line_cases(same_line_cases):
    for each_case in same_line_cases:
        print "Deleting {}...".format(each_case)
        ref = Ref(each_case)
        tc = TextChunk(ref, lang='he', vtitle="Vilna Edition")
        tc.text = ""
        tc.save(force_save=True)

if __name__ == "__main___":
    print 'this'
    titles = library.get_indexes_in_category("Tosafot", include_dependant=True)
    diff_line_cases = []
    same_line_cases = []
    for title in titles:
        print title
        text = TextChunk(Ref(title), lang='he').text
        prev = ""
        for daf in range(len(text)):
            for line in range(len(text[daf])):
                for segment in range(len(text[daf][line])):
                    curr = text[daf][line][segment]

                    if prev == curr and (prev_daf != daf or prev_line != line):
                        print_out_refs(daf, line, segment, prev_daf, prev_line, prev_segment)
                    elif prev == curr:
                        same_line_cases.append("{} {}:{}:{}".format(title, AddressTalmud.toStr("en", daf+1), line+1, segment+1))

                    prev = curr

                    prev_segment = segment
                prev_line = line
            prev_daf = daf

    delete_same_line_cases(same_line_cases)



