import django
django.setup()
from sefaria.model import *


refs = Ref("Zohar 3:64a-3:299b").range_list()
for ref in refs:
    whole_tc = TextChunk(ref, lang='he', vtitle="Torat Emet Zohar")
    whole_tc.text = ""
    whole_tc.save(force_save=True)

text = {3: {}}
with open("zohar.csv") as file:
    lines = list(file)
    for n, line in enumerate(lines):
        ref, comm = line.split(',', 1)
        comm = comm.replace("\r\n", "")
        if comm[0] == '"':
            comm = comm[1:]
        if comm[-1] == '"':
            comm = comm[:-1]
        print ref
        try:
            tc = TextChunk(Ref(ref), vtitle="Torat Emet Zohar", lang='he')
            if tc.text != comm:
                tc.text = comm
                tc.save(force_save=True)
        except:
            print "********* {}".format(ref)
