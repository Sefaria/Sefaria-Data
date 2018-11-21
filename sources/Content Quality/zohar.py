import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
first_tc = TextChunk(Ref("Zohar 3:64a"), lang='he', vtitle='Torat Emet Zohar')
second_tc = TextChunk(Ref("Zohar 3:64b"), lang='he', vtitle='Torat Emet Zohar')
first_tc.text += second_tc.text
first_tc.save(force_save=True)
#starting 65a, move every page down one
for v in library.get_index("Zohar").versionSet():
    vtitle = v.versionTitle
    tc = TextChunk(Ref("Zohar 3"), lang='he', vtitle=vtitle)
    full_text = tc.text[AddressTalmud(0).toNumber('en', '65a'):AddressTalmud(0).toNumber('en', '300b')] #grab text
    tc.text[AddressTalmud(0).toNumber('en', '64b'):AddressTalmud(0).toNumber('en', '300a')] = full_text
    tc.save(force_save=True)
    end_tc = TextChunk(Ref("Zohar 3:300a"), lang='he', vtitle='Torat Emet Zohar')
    end_tc.text = []
    end_tc.save(force_save=True)

i = library.get_index("Zohar")
alt_struct = i.alt_structs["Parasha"]["nodes"]
start_at = "Achrei Mot"
dont_start = True
for each_dict in alt_struct:
    if each_dict["sharedTitle"] == start_at:
        dont_start = False
        orig = Ref(each_dict["wholeRef"])
        new_start = orig.starting_ref()
        new_end = orig.ending_ref()
        new_end.toSections[1] -= 1
        new_end = Ref(_obj=new_end._core_dict())
        new = new_start.to(new_end)
    elif not dont_start:
        orig = Ref(each_dict["wholeRef"])
        new_start = orig.starting_ref()
        new_start.toSections[1] -= 1
        new_start = Ref(_obj=new_start._core_dict())
        new_end = orig.ending_ref()
        new_end.toSections[1] -= 1
        new_end = Ref(_obj=new_end._core_dict())
        new = new_start.to(new_end)



