import sefaria.system.exceptions
from sources.functions import *
def get_daf_amud(daf, amud):
    amud = amud.replace('ע"', '')
    amud = ord(amud)
    if amud == ord('ב'):
        amud = 'b'
    elif amud - ord('ב') == -1:
        amud = "a"
    else:
        raise Exception
    daf = getGematria(daf)
    return (daf, amud)

class ShaareiRef:
    def __init__(self, masechet, type, reference, prev_one, r):
        self.masechet = masechet
        self.type = type  # Rashi, Tosafot, Talmud, Mishnah
        self.reference = reference
        self.prev_one = prev_one
        self.row = r

def get_type(masechet, ref, prev_one, r):
    orig_ref = ref
    ref = ref.replace("""סופ""", 'פ"').replace('ספ"', 'פ"').replace('רפ"', 'פ"').replace('ספי"א', 'פי"א').replace('רפכ"ה', 'פכ"ה')
    ref = ref.replace("""משנה רפ"ד""", '').replace('משנה שהמלך', '').replace('משנה', '').replace('פי ברמב"ם', '').replace("""פי' ברמב"ם""", '')
    ref = ref.replace('סוף', '').replace('ישנים', '').replace('ר"ש', '').replace('פירוש', '')
    ref = ref.replace('פרק ', 'פ"').replace('“', '"').replace('יו"ד', 'י')
    ref = ref.replace("  ", " ").strip()
    ref = ref.replace('\'', '').strip()
    if (ref.startswith('פ') and ref.find('דף') == -1 and ref.split()[0].find('"') > 0): #or (ref.startswith('פ') and ref.count(" ") <= 1 and len(ref.split()[0]) > 1):
        type = "Mishnah"
        if ref.find(' מ') > 0:
            mishnah_pos = ref.find(' מ')
            ref = f"{ref[:mishnah_pos]} {ref[mishnah_pos:].strip().split()[0]}"
        elif ref.count(" ") > 1:
            ref
    elif ref.startswith('מ"'):
        type = "Mishnah"
        ref = prev_one.reference + " " + ref
    elif 'רש"י' in ref or 'המיוחס לרש"י' in ref or 'בפירש"י' in ref:
        type = "Rashi"
        ref = re.sub('.{0,1}פי.{0,1}', '', ref)
        ref = ref.replace('המיוחס לרש"י', '').replace('בפירש"י', '').replace('רש"י', '').strip()
    elif 'רשב"ם' in ref:
        type = "Rashbam"
        ref = ref.replace('רשב"ם', '').strip()
    elif 'תוס' in ref:
        type = "Tosafot"
        ref = ref.replace('תוספות', '').replace("תוס", '').strip()
    elif 'רי"ף' in ref:
        type = "Rif"
        ref = ref.replace('רי"ף', '').replace('ברי"ף', '')
    elif 'ר"נ' in ref:
        type = "Ran"
        ref = ref.replace('ר"נ', '')
    else:
        type = "Talmud"




    if re.search('דף' + ' \S{1,} \S{1,}', orig_ref):
        ref = re.search('דף' + ' \S{1,} \S{1,}', orig_ref).group(0).replace('דף', '').strip()
    if prev_one and ('שם' in ref or ref.strip() == ""):
        ref = prev_one.reference
        type = prev_one.type
    ref = ref.strip()
    ref = ref.replace('סע"', 'ע"').replace('רע"', 'ע"')
    if ref.count(' ') > 1:
        ref = prev_one.reference
        type = prev_one.type
    return (type, ref)
all_refs = []
refs_by_masechet = defaultdict(list)
bad_rows = []
with open("Sha'are Torath Babel _ Mishnah and Talmud - Mishnah and Talmud.csv", 'r') as f:
    rows = list(csv.reader(f))
    prev_one = None
    first_one = None
    curr_masechet = ""
    for r, row in enumerate(rows[1:]):
        masechet, ref, text = row
        masechet = masechet.replace('בכורים', 'ביכורים')
        if masechet != '':
            curr_masechet = masechet
            try:
                curr_masechet_ref = Ref(masechet).index
                curr_masechet_ref = curr_masechet_ref.title
            except:
                print(masechet)
                curr_masechet_ref = None
        if curr_masechet_ref:
            if prev_one and curr_masechet_ref != prev_one.masechet:
                prev_one = None
            type, reference = get_type(curr_masechet_ref, ref, prev_one, r)
            this_one = ShaareiRef(curr_masechet_ref, type, reference, prev_one, row)
            if prev_one:
                prev_one.next_one = this_one
            prev_one = this_one
            if first_one is None:
                first_one = this_one
            all_refs.append(this_one)
            refs_by_masechet[curr_masechet_ref].append(this_one)

    for r, each_ref in enumerate(all_refs):
        ref = each_ref.reference
        type = each_ref.type
        try:
            if type == "Mishnah":
                if ref.count(' ') == 0:
                    ref = ref.replace('פ', '')
                    perek = getGematria(ref)
                    each_ref.reference = Ref(f"{each_ref.masechet} {perek}")
                else:
                    perek, mishnah = ref.split()[0], ref.split()[1]
                    perek = perek.replace('פ', '')
                    mishnah = mishnah.replace('מ', '')
                    mishnah = getGematria(mishnah)
                    perek = getGematria(perek)
                    each_ref.reference = Ref(f"{each_ref.masechet} {perek}:{mishnah}")
            else:
                ref = ref.replace('דע"', '').replace('ע"', '')
                daf, amud = ref.split()[0], ref.split()[1]
                daf, amud = get_daf_amud(daf, amud)
                if type == "Talmud":
                    each_ref.reference = Ref(f"{each_ref.masechet} {daf}{amud}")
                else:
                    try:
                        each_ref.reference = Ref(f"{type} on {each_ref.masechet} {daf}{amud}")
                    except:
                        each_ref.reference = Ref(f"{type} {each_ref.masechet} {daf}{amud}")
        except (sefaria.system.exceptions.InputError, IndexError) as e:
            print(e)
            print(type, each_ref.masechet, each_ref.row)

    for masechet in refs_by_masechet:
        for each_ref in refs_by_masechet[masechet][:-1]:
            try:
                assert each_ref.reference.sections
            except:
                print(f"Not a ref: {each_ref.row[1]}")
                continue
            try:
                assert each_ref.next_one.reference.sections
            except:
                print(f"Not a ref: {each_ref.next_one.row[1]}")
                continue
            if len(each_ref.reference.sections) == 1:
                curr_sections = each_ref.reference.sections[0]
                next_sections = each_ref.next_one.reference.sections[0]
            else:
                curr_sections = each_ref.reference.sections[0]*10
                next_sections = each_ref.next_one.reference.sections[0]*10
                curr_sections += each_ref.reference.sections[1] if len(each_ref.reference.sections) > 1 else 1
                next_sections += each_ref.next_one.reference.sections[1] if len(each_ref.next_one.reference.sections) > 1 else 1
            try:
                assert next_sections >= curr_sections
            except AssertionError:
                bad_rows.append([masechet, each_ref.row[1], each_ref.next_one.row[1]])

with open("validation problems.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerows(bad_rows)



