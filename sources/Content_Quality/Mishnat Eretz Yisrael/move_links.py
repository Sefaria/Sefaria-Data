import os
import csv
from sources.functions import *
def inc_ref(ref, inc_count):
    core = Ref(ref)._core_dict()
    while inc_count > 0:
        core['sections'][-1] += 1
        core['toSections'][-1] += 1
        inc_count -= 1
    return Ref(_obj=core).normal()
def reset_count(ref, inc_count):
    if Ref(ref).sections[-1] == 1:
        return 0
    return inc_count

links = {}  # one to one mapping of old and new refs
for f in os.listdir("."):
    if f.endswith(".csv") and "new" not in f:
        inc_count = 0
        title = f.replace('- w images.csv', '').strip()
        library.get_index(title)
        rows = list(csv.reader(open(f)))
        new_rows = rows[:5]
        curr_ref = None
        refs = []
        just_found_ref = False
        for r, row in enumerate(rows[5:]):
            poss_ref, text, poss_img = row
            if len(poss_ref.strip()) == 0:  # found img
                # if just_found_ref:
                #     inc_count = 0
                assert len(poss_img.strip()) > 0
                inc_count += 1
                curr_ref_to_save = inc_ref(curr_ref, inc_count)
                what_to_save = poss_img
                just_found_ref = False
            elif len(poss_img.strip()) == 0:  # found ref
                inc_count = reset_count(poss_ref, inc_count)
                assert len(poss_ref.strip()) > 0
                curr_ref_to_save = inc_ref(poss_ref, inc_count)
                curr_ref = poss_ref
                what_to_save = text
                just_found_ref = True
            #tc = TextChunk(Ref(curr_ref), lang='he', vtitle='Mishnat Eretz Yisrael, Tamid-Middot, Elon Shvut, 2020')
            #tc.text = what_to_save
            new_rows.append([curr_ref_to_save, what_to_save])
        with open(f"{title} new.csv", 'w') as new_f:
            csv_writer = csv.writer(new_f)
            csv_writer.writerows(new_rows)
            #tc.save()

