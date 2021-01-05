from sources.functions import *


def dh_extract_method(some_string):
    some_string = some_string.replace(u'<b>', u'').replace(u'</b>', u'')
    if u'וכו\'' in u' '.join(some_string.split(u' ')[:10]):
        return some_string[:some_string.index(u'וכו\'') - 1]
    elif u'.' in some_string:
        if len(some_string.split(u'.')[0].split(u' ')) < 12:
            return some_string.split(u'.')[0]
    return ' '.join(some_string.split(u' ')[:5])



talmud_words = [u'בגמרא', u'גמרא', u'בגמ\'', u'גמ\'', u'במשנה', u'משנה', u'מתניתין', u'מתני\'', u'שם', u'בתר"י',
                u'בהרי"ף', u'ברי"ף', u'בר"ן']
rashi_words = [u'רש\"י ד\"ה', u'ברש\"י', u'רש\"י', u'רד\"ה']
tos_words = [u'תוספות ד\"ה', u'תוס\' ד\"ה', u'תוד\"ה', u'תוס\' ד"ה', u'תוס\'', u'תוספות', u'בתד"ה', u'תד"ה',
             u'בתוס\' ד"ה']
csv_files = [f for f in os.listdir(".") if f.endswith("csv")]
starting_daf_dict = {"Rashash on Nedarim": "2a", "Rashash on Bava Batra": "29a", "Rashash on Pesachim": "99b"}
bava_batra = """ברשב"ם ד"ה
רשב"ם ד"ה
בר"ש ד"ה
ר"ש ד"ה""".splitlines()
nedarim = ["""ר"ן ד"ה""", """רא"ש ד"ה"""]
patterns_dict = {"Rashash on Nedarim": nedarim, "Rashash on Bava Batra": bava_batra, "Rashash on Pesachim": bava_batra}

rashbam = {}
ran = {}
rosh = {}
links = []

for f in csv_files:
    starting = False
    with open(f, 'r') as open_f:
        reader = csv.reader(open_f)
        for row in reader:
            ref, comm = row
            if ref.startswith("Rashash on"):
                section_ref = ref.split(":")[0]
                if section_ref not in ran:
                    ran[section_ref] = []
                    rosh[section_ref] = []
                    rashbam[section_ref] = []
                title = " ".join(ref.split()[:-1])
                starting_daf = title + " " + starting_daf_dict[title]
                if section_ref == starting_daf:
                    starting = True
                if starting:
                    patterns = patterns_dict[title]
                    found = False
                    this_dict = {}
                    other_dict_1 = {}
                    other_dict_2 = {}
                    for pattern in patterns:
                        if pattern in " ".join(comm.split()[:5]):
                            if pattern == """ר"ן ד"ה""":
                                this_dict = ran
                                other_dict_1 = rosh
                                other_dict_2 = rashbam
                            elif pattern == """רא"ש ד"ה""":
                                this_dict = rosh
                                other_dict_1 = ran
                                other_dict_2 = rashbam
                            else:
                                this_dict = rashbam
                                other_dict_1 = rosh
                                other_dict_2 = ran

                            dh = dh_extract_method(comm.replace(pattern, "")).strip()
                            this_dict[section_ref].append(dh)
                            other_dict_1[section_ref].append("")
                            other_dict_2[section_ref].append("")
                            found = True
                            break
                    if not found:
                        ran[section_ref].append("")
                        rashbam[section_ref].append("")
                        rosh[section_ref].append("")
for dhs in [("Ran", ran), ("Rashbam", rashbam), ("Commentary of the Rosh", rosh)]:
    for section_ref in dhs[1]:
        if len([x for x in dhs[1][section_ref] if len(x) > 0]) > 0:
            base_ref = dhs[0] + " on " +section_ref.replace("Rashash on ", "")
            new_links = match_ref_interface(base_ref, section_ref, dhs[1][section_ref], lambda x: x.split(), lambda x: x)
            links += new_links
            for new_link in new_links:
                rashash, comm = new_link["refs"]
                base = comm.split(" on ")[-1].split(":")[0]
                ls = LinkSet({"$and": [{"refs": {"$regex": "^{}".format(base)}}, {"refs": {"$regex": comm}}]})
                if ls.count() == 1:
                    for l in ls:
                        base_ref = l.refs[0] if l.refs[0].startswith(base) else l.refs[1]
                        links.append({"refs": [base_ref, rashash], "generated_by": "derivative_links_for_rashash", "type": "Commentary",
                                      "auto": True})



print(len(links))
post_link_in_steps(links, 250, sleep_amt=5)





