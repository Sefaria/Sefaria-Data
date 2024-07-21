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

def convert_links(title, links):
    ls = Ref(title).linkset()
    generated_by = set()
    for l in ls:
        ref_pos = 0 if title in l.refs[0] else 1
        ref = l.refs[ref_pos]
        ref = Ref(ref)
        start, end = ref.starting_ref().normal(), ref.ending_ref().normal()
        if start not in links:
            print(ref)
        if end not in links:
            print(ref)
        start = links.get(start, start)
        end = links.get(end, end)
        new_ref = Ref(start).to(Ref(end)).normal()
        l.refs[ref_pos] = new_ref
        generated_by.add(l.generated_by)
        #l.save()
    print(generated_by)

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
                assert len(poss_img.strip()) > 0
                inc_count += 1
                curr_ref_to_save = inc_ref(curr_ref, inc_count)
                if curr_ref_to_save == 'Mishnat Eretz Yisrael on Mishnah Middot 2:5:21':
                    curr_ref_to_save = "Mishnat Eretz Yisrael on Mishnah Middot 2:6:1"
                    inc_count = 0
                what_to_save = poss_img
                just_found_ref = False
            elif len(poss_img.strip()) == 0:  # found ref
                inc_count = reset_count(poss_ref, inc_count)
                assert len(poss_ref.strip()) > 0
                curr_ref_to_save = inc_ref(poss_ref, inc_count)
                links[poss_ref] = curr_ref_to_save
                curr_ref = poss_ref
                what_to_save = text
                just_found_ref = True
            else:
                print(f"Problem at {poss_ref}")
            #tc = TextChunk(Ref(curr_ref), lang='he', vtitle='Mishnat Eretz Yisrael, Tamid-Middot, Elon Shvut, 2020')
            #tc.text = what_to_save
            new_rows.append([curr_ref_to_save, what_to_save])
        with open(f"{title} new.csv", 'w') as new_f:
            csv_writer = csv.writer(new_f)
            csv_writer.writerows(new_rows)
            #tc.save()


for f in os.listdir("."):
    if f.endswith(".csv") and "new" in f:
        title = f.replace(' new.csv', '').strip()
        convert_links(title, links)
