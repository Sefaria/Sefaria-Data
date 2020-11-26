import django
django.setup()
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import *
def add_citations(row):
    match = re.search(".*?\d+\.\d+\.\d+", row[0])
    if not match:
        return row
    if "Part" not in row[0]:
        row[0] = row[0].replace(".", ", ", 1)
        row[0] = re.sub("(\d+), ", "Part \g<1>, ", row[0])
    section_ref = Ref(row[0]).section_ref().normal()
    if section_ref not in found_by_sec:
        found_by_sec[section_ref] = []
        found_by_seg[section_ref] = {}
    found_by_sec[section_ref].append(new_citation)
    found_by_seg[section_ref][Ref(row[0]).normal()] = new_citation
    return row

def test(poss_links, ref, corresponding):
    found = False
    real_links = [get_ref(l) for l in LinkSet(Ref(ref))]
    for l in poss_links:
        if l in real_links:
            found = True
            corresponding[ref] = ref
            break
    return found

def get_corr_siman_try_2(our_guide_links, our_guide_links_by_seg, links, links_by_seg):
    corresponding = {}
    found = False
    guide = "Guide for the Perplexed, Part 1"
    curr_siman = 1

    for r, ref in enumerate(links):
        poss_links = links[ref]
        overlap = set(poss_links).issubset(set(our_guide_links[ref])) #set(poss_links).intersection(our_guide_links[ref]) > 0
        if overlap:

            corresponding[ref] = ref


        else:
            prev_5 = None
            next_5 = None
            others_to_check = []
            corresponding[ref] = []
            for i in range(1, 6):
                if r+i < len(links):
                    others_to_check.append(list(links.keys())[r+i])
                if r-i >= 0:
                    others_to_check.append(list(links.keys())[r-i])
            for l in others_to_check:
                overlap = set(poss_links).intersection(l)
                if len(overlap) > 0:
                    print("Found match")
                    corresponding[ref] += l
    return corresponding

    # try instead of resetting each time we find, because this relies on assumptions,
    # just start at each position and go up and down 5 - 10 spots looking for all matches and record all

def get_ref(l):
    guide_pos = 0 if l.refs[0].startswith("Guide for the Perplexed,") else 1
    guide_ref = l.refs[guide_pos]
    other_ref = l.refs[1-guide_pos]
    other_index = Ref(other_ref).index
    not_comm = "Commentary" not in other_index.categories
    tanakh = "Tanakh" in other_index.categories
    if tanakh and not_comm:
        return other_ref
    else:
        return ""

def get_corresponding_simanim(links):
# if you can find tne of the links move on to next siman, if you find none in corresponding siman, check before and after
# save the spot where you found it last
    corresponding = {}
    found = False
    guide = "Guide for the Perplexed, Part 1"
    curr_siman = 1
    for ref in links:
        if ref.startswith(guide):
            poss_links = links[ref]
            found = test(poss_links, ref, corresponding)
            print(found)
            if found:
                curr_siman += 1
            elif not found:
                #if you move Guide back, you're saying that French version is split into two,
                if curr_siman > 1:
                    curr_siman -= 1
                    ref = "{} {}".format(guide, curr_siman)
                    found = test(poss_links, ref, corresponding)
                    if not found:
                        #if you move Guide forward, you're saying Guide is split
                        curr_siman += 2
                        ref = "{} {}".format(guide, curr_siman)
                        found = test(poss_links, ref, corresponding)
                        if not found:
                            corresponding[ref] = "Not found"
                            curr_siman -= 1
    return corresponding

fr_books = """Genèse
Exode
Lévitique
Nombres
Deutéronome
Josué
Juges
I Samuel
II Samuel
I Rois
II Rois
Isaïe
Jérémie
Ézéchiel
Osée
Joël
Amos
Abdias
Jonas
Michée
Nahum
Habacuc
Zéphanie
Aggée
Zacharie
Malachie
Psaumes
Proverbes
Job
Cantique des Cantiques
Ruth
Lamentations
Ecclésiaste
Esther
Daniel
Esdras
Néhémie
1 Chroniques
2 Chroniques""".splitlines()

en_tanakh = library.get_indexes_in_category("Tanakh")
books = "|".join(fr_books)
found_by_seg = {}
found_by_sec = {}
from sources.functions import *
with open("new_full_text.csv", 'w') as new_f:
    writer = csv.writer(new_f)
    with open("Moreh Nevukhim.csv", 'r') as f:
        rows = list(csv.reader(f))
        for r, row in enumerate(rows):
            finds = re.findall("("+books+"), ([ILVXC]+), (\d+)", row[1])
            if finds:
                for find in finds:
                    find = list(find)
                    old_citation = "{}, {}".format(*find[1:])
                    if len(find) != 3:
                        print("ERROR")
                    else:
                        find[1] = roman_to_int(find[1])
                        loc = fr_books.index(find[0])
                        actual_book = en_tanakh[loc]
                        find[0] = actual_book
                        new_citation = "{}:{}".format(*find[1:])
                        assert old_citation in row[1]
                        row[1] = row[1].replace(old_citation, new_citation, 1)
                        new_citation = "{} {}".format(actual_book, new_citation)
                        row = add_citations(row)
            else:
                pass


            writer.writerow(row)
our_guide_links = {}
our_guide_seg_links = {}
segs = Ref("Guide for the Perplexed, Part 1").all_segment_refs() + Ref(
    "Guide for the Perplexed, Part 2").all_segment_refs() + Ref("Guide for the Perplexed, Part 3").all_segment_refs()
secs = Ref("Guide for the Perplexed, Part 1").all_subrefs() + Ref(
    "Guide for the Perplexed, Part 2").all_subrefs() + Ref("Guide for the Perplexed, Part 3").all_subrefs()

for ref in segs:
    our_guide_seg_links[ref.normal()] = [get_ref(l) for l in LinkSet(ref)]

for ref in secs:
    our_guide_links[ref.normal()] = [get_ref(l) for l in LinkSet(ref)]

results = get_corr_siman_try_2(our_guide_links, our_guide_seg_links, found_by_sec, found_by_seg)
pass
# now that we know that most of the time the entire siman matches the original (as in the citations are contained)
# when citations are contained entirely, we can look at each individual citation and make a map of segments
# from French to Original.  once map is generated, I can look at it and come up with segmentation plan.


# do I need to make a map of French segments to citations and English/Hebrew segments to citations?
