try:
    this_perek['num'] = int(this_perek['num'])
    note['halacha_num'] = int(note['halacha_num'])
except ValueError as e:
    print(e)
    continue
if this_perek['num'] not in note_dict:
    note_dict[this_perek['num']] = defaultdict(list)
note_dict[this_perek['num']][note['halacha_num']].append(f"<b>{note['title'].strip()}</b>. {note['text'].strip()}")
MT_ref = f"Mishneh Torah, {this_section['name_eng']} {note['halacha_num']}"
print(MT_ref)
comments = len(note_dict[this_perek['num']][note['halacha_num']])
stein = f"Steinsaltz on Mishneh Torah, {this_section['name_eng']} {this_perek['num']}:{note['halacha_num']}:{comments}"
links.append([MT_ref, stein])