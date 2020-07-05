import django
django.setup()
from sefaria.model import *
from sources.functions import *
from sefaria.system.exceptions import *
probs = """Judges - 37.3
I Samuel - 76:8
II Samuel - 141:6
Joel - 533:8
Amos - 538:5
Micah - 551:4
Nahum - 560:2
Habakkuk - 561:7
Zephaniah - 566:2
Haggai - 569:1
Nehemiah - 1069:14
II Chronicles - 1083:2""".splitlines()
probs_dict = {prob.split(" - ")[0]: prob.split(" - ")[1] for prob in probs}
alt_structs = library.get_index("Yalkut Shimoni on Nach").alt_structs["Books"]["nodes"]
for i, each_dict in enumerate(alt_structs):
    try:
        titles = each_dict["titles"]
        title = titles[0]["text"] if titles[0]["lang"] == "en" else titles[1]["text"]
        if title in probs_dict.keys():
            new_start = Ref("Yalkut Shimoni on Nach {}".format(probs_dict[title]))
            old_ref = Ref(each_dict["wholeRef"])
            end = old_ref.ending_ref()
            new_ref = new_start.to(end)
            each_dict["wholeRef"] = new_ref.normal()
    except InputError as e:
        print e

old_index = get_index_api("Yalkut Shimoni on Nach", server="http://www.sefaria.org")
old_index["alt_structs"] = alt_structs
#post_index(old_index, server="http://ste.sandbox.sefaria.org")


