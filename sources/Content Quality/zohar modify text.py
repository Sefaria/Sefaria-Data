import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
#starting 65a, move every page down one

data = """3.64b.1 3.64a.5 -1
3.82b.18 3.82b.1 1
3.116a.1 3.117a.1 2
3.152b.1 3.152b.9 -1
3.212a.11 3.213a.1 1
3.225b.1 3.226a.2 -1
3.248a.11 3.249a.1 1
3.250a.1 3.250b.7 -1
3.250b.1 3.250b.10 -1
3.260a.1 3.259b.9 -1""".splitlines()
data = [el.split(" ") for el in data]




#for v in library.get_index("Zohar").versionSet():
absolute_tcs = []
vtitle = "Torat Emet Zohar"
lang = "he"
skip = []
until = 3
save = True
for row in data:
    ref = Ref("Zohar "+row[0])
    end_daf = ref.section_ref().as_ranged_segment_ref().ending_ref()
    absolute_tcs.append(TextChunk(ref.to(end_daf), lang=lang, vtitle=vtitle).text)
for i, row in enumerate(data):
    print row
    if i in skip:
        continue
    if i == until:
        break
    orig, new, move = row
    move = int(move)
    #move text of tc to new
    if move == -1:
        curr = Ref("Zohar " + new).section_ref()
        curr_tc = TextChunk(curr, lang=lang, vtitle=vtitle)
        curr_tc.text += absolute_tcs[i]
        if save:
            curr_tc.save(force_save=True)
        tc = TextChunk(Ref("Zohar 3"), lang='he', vtitle=vtitle)
        daf = curr.sections[1] - 1
        full_text = tc.text[daf+2:]  # grab text
        tc.text[daf+1:] = full_text
        if save:
            tc.save(force_save=True)
    elif move > 0:
        tc = TextChunk(Ref("Zohar 3"), lang='he', vtitle=vtitle)
        curr = Ref("Zohar " + new)
        curr.sections[1] -= move
        curr.sections[2] = Ref("Zohar "+orig).sections[2]

        #get all text that we shift and remove either the previous amud/daf or just part of it
        #TextChunk(Ref(_obj=curr._core_dict()).to(Ref("Zohar 3").all_subrefs()[-1]), lang=lang, vtitle=vtitle).text
        amud = curr.sections[1] - 1
        full_text = tc.text[amud:]
        starting_segment = curr.sections[2]
        len_section = len(tc.text[amud])
        for i in range(len_section):
            if i >= starting_segment:
                tc.text[amud][i] = ""
        if save:
            tc.save(force_save=True)

        amud += move
        tc.text[amud:] = full_text
        if save:
            tc.save(force_save=True)

        # curr.sections[1] += move
        # curr.sections[2] = Ref("Zohar "+new).sections[2]
        # new_tc = TextChunk(Ref(_obj=curr._core_dict()).to(Ref("Zohar 3").all_subrefs()[-1]), lang=lang, vtitle=vtitle)
        # new_tc.text = full_text
        # new_tc.save(force_save=True)




