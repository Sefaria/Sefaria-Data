import django
django.setup()
from sefaria.model import *
import re
from collections import Counter
with open("output_sec2sec.txt", 'r') as f:
    content = f.readlines()
    list_of_refs = re.findall("\[.*?\]", content[0])
    counter = Counter()
    for str_tuple in list_of_refs:
        tuple = eval(str_tuple)
        book1 = Ref(tuple[0]).index.title
        book2 = Ref(tuple[1]).index.title
        if book1 == book2:
            print(tuple)

        counter[(book1, book2)] += 1

for c in counter.most_common(100):
    print("{} links from {} to {}".format(c[1], c[0][0], c[0][1]))

    # for l in LinkSet():


    #     count += 1
    #     print(count)
    #     try:
    #         ref_1 = Ref(l.refs[0])
    #         ref_2 = Ref(l.refs[1])
    #         ref_1_not_segment = not ref_1.is_segment_level()
    #         ref_2_not_segment = not ref_2.is_segment_level()
    #         if ref_1_not_segment and ref_2_not_segment:
    #             print(l.refs)
    #             f.write(str(l.refs))
    #     except:
    #         pass
