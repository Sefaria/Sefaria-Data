import django
django.setup()
from sefaria.model import *

# response = _get_text_version_file("csv", "Zohar", 'he', "Torat Emet Zohar")
# with open("zohar_full.csv", 'w') as f:
#     f.write(response)
new_zohar_dict = {}
with open("zohar.csv") as new_zohar:
    for row in csv.reader(new_zohar):
        print row[0]
        new_zohar_dict[row[0]] = row[1]
        tc = TextChunk(Ref(row[0]), lang='he', vtitle="Torat Emet Zohar")
        tc.text = row[1]
        tc.save(force_save=True)

found_daf = False
print "Now empty out others"
skip = 100
with open("zohar_full.csv") as old_zohar:
    for i, row in enumerate(csv.reader(old_zohar)):
        if i < skip:
            continue
        ref, text = row
        vol = ref.split()[-1].split(":")[0]
        daf = ref.split()[-1].split(":")[1]
        if not found_daf and vol == "3" and daf == "64a":
            found_daf = True
        if found_daf:
            tc = TextChunk(Ref(ref), lang='he', vtitle="Torat Emet Zohar")
            if ref not in new_zohar_dict.keys():
                print ref
                tc.text = ""
                tc.save(force_save=True)

#64a on needs to be whatever is in zohar.csv


#
# text_to_keep = Ref("Zohar 3:1a-3:63b").text('he').text
# vol_3 = TextChunk(Ref("Zohar 3"), lang='he', vtitle="Torat Emet Zohar")
# vol_3.text = []
# vol_3.save(force_save=True)
#
#
# refs = Ref("Zohar 3:64a-3:299b").range_list()
# already_reset = []
# for ref in refs:
#     ref = ref.context_ref()
#     if ref not in already_reset:
#         already_reset.append(ref)
#         print ref
#         whole_tc = TextChunk(ref, lang='he', vtitle="Torat Emet Zohar")
#         whole_tc.text = []
#         whole_tc.save(force_save=True)
#
# text = {3: {}}
# with open("zohar.csv") as file:
#     lines = list(file)
#     for n, line in enumerate(lines):
#         ref, comm = line.split(',', 1)
#         comm = comm.replace("\r\n", "")
#         if comm[0] == '"':
#             comm = comm[1:]
#         if comm[-1] == '"':
#             comm = comm[:-1]
#         print ref
#         try:
#             tc = TextChunk(Ref(ref), vtitle="Torat Emet Zohar", lang='he')
#             if tc.text != comm:
#                 tc.text = comm
#                 tc.save(force_save=True)
#         except:
#             print "********* {}".format(ref)
